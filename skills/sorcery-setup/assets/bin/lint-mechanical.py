#!/usr/bin/env python3
"""Deterministic wiki health checks — the zero-LLM phase of wiki-lint.

Two modes:
  python bin/lint-mechanical.py            full mode  -> JSON, all checks, whole wiki
  python bin/lint-mechanical.py --staged   staged mode -> human text + exit code,
                                           staged files only (pre-commit gate)

Full mode emits a JSON object {"findings": {...}, "clusters": [...]} for wiki-lint to fold
into its report. Staged mode runs the per-file/resolvable checks against the staged blobs and
exits non-zero if any fire. Stdlib only.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikilib import LINK_RE, find_repo_root, require_wiki

WIKI_ROOT = find_repo_root()
PAGES_DIR = WIKI_ROOT / "wiki" / "pages"
CONFIG_DIR = WIKI_ROOT / "wiki" / "config"
FAMILIES_FILE = CONFIG_DIR / "slug-families.txt"

# Required per-page fields per wiki/WIKI-SCHEMA.md page templates (both resource and
# concept pages carry these; `resource`/`sources` are type-specific and checked by
# the schema, not here).
REQUIRED_FIELDS = ("type", "title", "description", "tags", "generated", "updated")
# Slug references: LINK_RE, shared with check-links.py via wikilib, matches exactly the forms
# WIKI-SCHEMA.md emits — [[slug](slug.md)], the pages/ and /wiki/pages/ prefixes, and any of
# those with a trailing #L line range. The path prefix stops short of `../`, so source path
# links and URLs never register as slug references.
STALE_MARKERS = ("current", "latest", "recent", "state-of-the-art")
# Word-boundary match so "recently" / "currently" do not read as stale markers.
STALE_MARKER_RES = tuple(re.compile(r"\b" + re.escape(m) + r"\b") for m in STALE_MARKERS)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
STALE_AGE_DAYS = 90
DEFAULT_CLUSTER_CAP = 25


def split_doc(text):
    """Return (frontmatter_dict_or_None, body_text) — body excludes the frontmatter block."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, text
    return parse_frontmatter(text), "\n".join(lines[end + 1:])


def parse_frontmatter(text):
    """Return the page's frontmatter as a dict, or None if absent/unterminated.

    Scalar `key: value` lines become strings; `key: [a, b]` inline lists and the block form
    (`key:` followed by indented `- item` lines) become lists. A list value is always a list,
    never a string — a scalar `tags: concept` stays a string and `as_list` normalizes it.
    Only top-level keys are read, so nested blocks (a concept page's `sources:` entries, a
    `review:` block) contribute nothing beyond their parent key. No third-party YAML dependency.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    fm = {}
    i = 1
    while i < end:
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line[0] in " \t":
            continue  # nested/indented line — belongs to the key above, not a key itself
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            fm[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        elif not value:
            # Block list: `key:` with nothing after it, then indented `- item` lines.
            items = []
            while i < end:
                nxt = lines[i]
                item = nxt.strip()
                if not (nxt[:1] in " \t" and item.startswith("-")):
                    break
                items.append(item[1:].strip().strip("\"'"))
                i += 1
            fm[key] = items
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fm[key] = value
    return fm


def as_list(value):
    """A frontmatter value as a list of strings: a list verbatim, a scalar as one item.

    Guards consumers against a value written as a bare scalar (`tags: concept`), which would
    otherwise iterate character by character.
    """
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def links_in(text):
    """Return the cross-referenced slugs in a page body.

    Takes the slug from every `LINK_RE` form (see wikilib): same-directory, `pages/` and
    `/wiki/pages/` prefixed, with or without a `#L…` line range. Source path links are
    excluded by construction, so a citation never registers as a link to a page.
    """
    return [m.group("slug") for m in LINK_RE.finditer(text)]


def is_page(path):
    # index.md is a generated artifact (okf index) — no frontmatter, not part of
    # the link graph. audit-* reports are gitignored local-only artifacts.
    return path.suffix == ".md" and path.stem != "index" and not path.name.startswith("audit-")


def load_pages():
    """Return {slug: {"fm": dict|None, "body": str, "links": [slug, ...]}} for real pages.

    `body` and `links` exclude the frontmatter block, so frontmatter dates never count as
    stale-content years and frontmatter never contributes phantom links.
    """
    pages = {}
    if not PAGES_DIR.exists():
        return pages
    for path in sorted(PAGES_DIR.glob("*.md")):
        if not is_page(path):
            continue
        fm, body = split_doc(path.read_text(encoding="utf-8"))
        pages[path.stem] = {"fm": fm, "body": body, "links": links_in(body)}
    return pages


def missing_fields(fm):
    """Required frontmatter fields that are absent or empty."""
    fm = fm or {}
    return [f for f in REQUIRED_FIELDS if not fm.get(f)]


def check_missing_frontmatter(pages):
    out = []
    for slug, page in pages.items():
        missing = missing_fields(page["fm"])
        if missing:
            out.append({"page": slug, "missing": missing})
    return out


def check_broken_links(pages):
    known = set(pages)
    out = []
    for slug, page in pages.items():
        for target in page["links"]:
            if target not in known:
                out.append({"page": slug, "link": target})
    return out


def check_orphans(pages):
    inbound = {slug: 0 for slug in pages}
    for slug, page in pages.items():
        for target in page["links"]:
            if target in inbound and target != slug:
                inbound[target] += 1
    return [{"page": slug} for slug, n in inbound.items() if n == 0]


def slug_families():
    """Declared intentional slug families: a list of sets of slugs.

    Reads wiki/config/slug-families.txt — one family per line, space-separated
    slugs, '#' starts a comment. A family declares that its slugs are related
    pages (a glossary term beside the class/concept derived from it, a source
    page beside its test or sibling), NOT homonym collisions of different
    senses. A missing or empty file means no declared families.
    """
    families = []
    if not FAMILIES_FILE.exists():
        return families
    for line in FAMILIES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        members = set(line.split())
        if members:
            families.append(members)
    return families


def is_declared_family(group, families):
    """True if the whole collision group sits inside a single declared family."""
    return any(fam.issuperset(group) for fam in families)


def check_slug_collisions(pages, families=None):
    """Flag a bare single-token slug colliding with qualified slugs sharing its lead token.

    Groups that form a declared slug family (see slug_families) are intended
    relatives, not collisions, and are skipped.
    """
    families = families or []
    out = []
    for slug in pages:
        if "-" in slug:
            continue  # only bare slugs are ambiguous
        qualified = sorted(s for s in pages if s != slug and s.split("-")[0] == slug)
        if not qualified:
            continue
        group = {slug, *qualified}
        if is_declared_family(group, families):
            continue
        out.append({"token": slug, "pages": [slug] + qualified})
    return out


def updated_date(value):
    """The page's `updated` date as a date, or None if absent/unparseable.

    WIKI-SCHEMA.md writes provenance as an inline map — `updated: { by: pi/model, at: <datetime> }`
    — so the date lives under the `at:` key, not in the value as a whole. A bare `updated: <date>`
    is also accepted. Reading the raw map string with `date.fromisoformat` always failed, which
    silently disabled this check for every schema-conformant page.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.startswith("{"):
        m = re.search(r"\bat\s*:\s*([^,}]+)", text)
        if not m:
            return None
        text = m.group(1).strip().strip("\"'")
    text = text.split("T")[0].split(" ")[0]  # a datetime's date part
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def check_stale_date(pages, today):
    out = []
    for slug, page in pages.items():
        fm = page["fm"] or {}
        updated = updated_date(fm.get("updated"))
        if updated is None:
            continue
        age = (today - updated).days
        if age <= STALE_AGE_DAYS:
            continue
        body = page["body"].lower()
        has_marker = any(m.search(body) for m in STALE_MARKER_RES)
        has_old_year = any(int(m.group()) <= today.year - 2 for m in YEAR_RE.finditer(body))
        if has_marker or has_old_year:
            out.append({"page": slug})
    return out


def check_missing_concept(pages):
    """A [[slug]] referenced 3+ times across the wiki that resolves to no page."""
    known = set(pages)
    counts = {}
    for page in pages.values():
        for target in page["links"]:
            if target not in known:
                counts[target] = counts.get(target, 0) + 1
    return [{"slug": s, "count": n} for s, n in sorted(counts.items()) if n >= 3]


def build_clusters(pages, cap):
    """Group pages by shared tag into contradiction-sweep clusters.

    A tag with >=2 pages is a candidate cluster; singleton tags are skipped. A cluster that
    is a strict subset of another is dropped (the superset's subagent covers it). A cluster
    larger than `cap` is deterministically split into alphabetical chunks, each flagged
    `split` so the report can note the recall caveat.
    """
    by_tag = {}
    for slug, page in pages.items():
        for tag in as_list((page["fm"] or {}).get("tags")):
            by_tag.setdefault(tag, set()).add(slug)

    candidates = {frozenset(s) for s in by_tag.values() if len(s) >= 2}
    kept = [c for c in candidates if not any(c < other for other in candidates)]

    out = []
    for members in sorted((sorted(c) for c in kept)):
        if len(members) > cap:
            for i in range(0, len(members), cap):
                out.append({"pages": members[i:i + cap], "split": True})
        else:
            out.append({"pages": members, "split": False})
    return out


def run_full(today=None, cluster_cap=None):
    today = today or date.today()
    cluster_cap = cluster_cap if cluster_cap and cluster_cap > 0 else DEFAULT_CLUSTER_CAP
    pages = load_pages()
    findings = {
        "missing_frontmatter": check_missing_frontmatter(pages),
        "broken_links": check_broken_links(pages),
        "orphans": check_orphans(pages),
        "slug_collisions": check_slug_collisions(pages, slug_families()),
        "stale_date": check_stale_date(pages, today),
        "missing_concept": check_missing_concept(pages),
    }
    return {"findings": findings, "clusters": build_clusters(pages, cluster_cap)}


def git(*args):
    result = subprocess.run(["git", "-C", str(WIKI_ROOT), *args],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def staged_page_paths():
    """Yield staged (added/copied/modified) wiki/pages/*.md paths.

    Excludes the generated index and audit reports — the same exemptions `is_page`
    applies in full mode. index.md is rebuilt by `okf index` and carries no
    frontmatter, so gating it would block every commit that regenerates it.
    """
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    for path in out.splitlines():
        path = path.strip()
        if (path.startswith("wiki/pages/") and path.endswith(".md")
                and Path(path).name != "index.md"
                and not Path(path).name.startswith("audit-")):
            yield path


def known_slugs():
    """The slug set used to resolve links/collisions in staged mode — the git index.

    Read from the index rather than the working tree so resolution matches the content being
    gated: the staged blobs. A page present on disk but never staged is not a valid target, and
    a page staged then deleted from the working tree still counts. Outside a git repo, fall
    back to the pages on disk.
    """
    try:
        out = git("ls-files", "--cached", "--", "wiki/pages")
    except RuntimeError:
        out = None
    if out is None:
        if not PAGES_DIR.exists():
            return set()
        return {p.stem for p in PAGES_DIR.glob("*.md") if is_page(p)}
    return {Path(p).stem for p in out.splitlines() if p.strip() and is_page(Path(p.strip()))}


def collision_for(slug, known, families=None):
    """Return the colliding slug group if `slug` collides with a known slug, else None.

    Declared slug families (see slug_families) are intended relatives, not
    collisions, so a group inside one is not a collision.
    """
    families = families or []
    others = known - {slug}
    if "-" not in slug:  # bare slug vs qualified slugs sharing it
        partners = sorted(s for s in others if s.split("-")[0] == slug)
        if not partners:
            return None
        group = {slug, *partners}
        return None if is_declared_family(group, families) else [slug] + partners
    base = slug.split("-")[0]  # qualified slug vs an existing bare base
    if base not in others:
        return None
    group = {base, slug}
    return None if is_declared_family(group, families) else sorted([base, slug])


def run_staged():
    try:
        git("rev-parse", "--is-inside-work-tree")
    except RuntimeError:
        return 0  # not a git repo — nothing to gate
    known = known_slugs()
    families = slug_families()
    problems = []
    for path in staged_page_paths():
        slug = Path(path).stem
        try:
            fm, body = split_doc(git("show", f":{path}"))  # the staged blob
        except RuntimeError:
            continue
        missing = missing_fields(fm)
        if missing:
            problems.append((slug, f"missing frontmatter: {', '.join(missing)}"))
        for target in links_in(body):
            if target not in known:
                problems.append((slug, f"broken link: [[{target}]]"))
        collision = collision_for(slug, known, families)
        if collision:
            problems.append((slug, f"slug collision: {', '.join(collision)}"))

    if not problems:
        return 0
    print("commit blocked — structural problems in staged page(s):\n", file=sys.stderr)
    for slug, msg in problems:
        print(f"  wiki/pages/{slug}.md\n    {msg}", file=sys.stderr)
    print("\nFix the page(s) and re-stage. To commit anyway: git commit --no-verify",
          file=sys.stderr)
    return 1


def parse_opt(argv, name, convert):
    prefix = f"--{name}="
    for arg in argv:
        if arg.startswith(prefix):
            try:
                return convert(arg[len(prefix):])
            except ValueError:
                raise SystemExit(f"bad --{name} value: {arg[len(prefix):]!r}")
    return None


def main(argv):
    require_wiki(WIKI_ROOT, "lint-mechanical.py")
    if "--staged" in argv:
        sys.exit(run_staged())
    today = parse_opt(argv, "today", date.fromisoformat)
    cap = parse_opt(argv, "cluster-cap", int)
    json.dump(run_full(today, cap), sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
