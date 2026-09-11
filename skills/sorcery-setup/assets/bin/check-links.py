#!/usr/bin/env python3
"""Deterministic link validator for the wiki — checks what the other gates cannot.

`lint-mechanical.py` checks the link *graph* (does the target page exist?) and `okf lint` checks
OKF shape. Neither validates a source-path link's *target* or its `#L` line range, and neither
notices a slug reference written in a form the link regex cannot see (`[[slug]]` with no target,
or the legacy `[[slug|display]]`). This tool closes those gaps:

  * every slug reference `[[slug](path.md)]` resolves to an existing page, and its display text
    is the slug verbatim;
  * every source-path link `[[x](../../target.ext#L…)` resolves to an existing file;
  * every `#L…` line range lies **inside** the target file (no range may run past EOF);
  * no malformed slug reference remains: bare `[[slug]]` or legacy `[[slug|display]]`;
  * no malformed *link* — `[[display](target)` with the closing `]` missing. Both slug regexes
    above require the trailing `]`, so this class is invisible to every other gate and renders a
    stray `[`;
  * footnote definitions that cite a **wiki page** instead of source material (`§ Citations`:
    a citation must be a source path link). Reported as one line per page — it is a corpus-wide
    migration, so it fails the run only under `--strict-citations`.

The line-range rule is the important one: `wiki-audit` relies on `L<start>-<end>` tokens to
verify quotes, so a range that runs past the end of the file silently defeats it. 139 such
defects were found by this check on 2026-09-09 after both other gates passed.

Usage:
  check-links.py                     # whole wiki: every page, overview, and reports
  check-links.py helaman alma        # named slugs
  check-links.py wiki/pages/foo.md   # named paths
  check-links.py --staged            # staged wiki/pages/*.md only (pre-commit gate)
  check-links.py --strict-citations  # also fail on footnotes that cite a wiki page

Exit 0 = clean, 1 = problems (printed). Stdlib only.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Link patterns come from wikilib so this gate and lint-mechanical.py cannot drift: LINK_RE
# (ANY_LINK_RE) walks every `[[display](target)]` to validate targets and line ranges; BARE_RE
# and PIPE_RE catch the malformed slug forms. wikilib.LINK_RE is the canonical slug-reference
# pattern the graph checks use.
from wikilib import ANY_LINK_RE as LINK_RE, BARE_RE, PIPE_RE, decode_target, find_repo_root, require_wiki

WIKI_ROOT = find_repo_root()
PAGES_DIR = WIKI_ROOT / "wiki" / "pages"
# Wiki documents outside the pages bundle that also carry links (overview + the reports).
EXTRA_DOCS = [WIKI_ROOT / "wiki" / "overview.md"]

CODE_SPAN_RE = re.compile(r"`[^`]*`")

# An attempted link whose target is not followed by the closing `]`: `[[display](target)`.
# `[^\]\n]*` between `[[` and `](` keeps this to real link attempts, so transcript-diff text such
# as `-[[2 Hebrew words]]-` is not mistaken for one.
ATTEMPTED_LINK_RE = re.compile(r"\[\[[^\]\n]*\]\(([^)\s]+)\)(?!\])")

# A footnote definition, and a footnote whose *first* link is a wiki page rather than a source.
# The `../pages/` alternative exists so the check cannot silently miss a wiki-page target written in
# the non-canonical spelling; `slug.md` is the form actually in use.
FOOTNOTE_RE = re.compile(r"^\[\^(\d+)\]:\s*")
FOOTNOTE_SLUG_TARGET_RE = re.compile(
    r"\[\[[^\]]+\]\((?:\.\./pages/|pages/)?([a-z0-9-]+)\.md(?:#L[\d,-]+)?\)\]")


def strip_code(text):
    """Blank out inline code spans and fenced blocks so documentation examples are not linted."""
    text = CODE_SPAN_RE.sub(lambda m: " " * len(m.group()), text)
    out, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append("" if fence else line)
    return "\n".join(out)


def line_count(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return len(fh.read().splitlines())


def check_text(text, display_path, base_dir):
    """Return a list of problem strings for one document's text."""
    problems = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in ATTEMPTED_LINK_RE.finditer(line):
            problems.append(f"{display_path}:{i} malformed link [[…]({m.group(1)}) — the closing "
                            f"']' is missing (WIKI-SCHEMA.md § Emit: \"[[display](target)]\")")
        for m in BARE_RE.finditer(line):
            problems.append(f"{display_path}:{i} malformed slug reference [[{m.group(1)}]] "
                            f"(no (target.md) — it renders as literal text)")
        for m in PIPE_RE.finditer(line):
            problems.append(f"{display_path}:{i} legacy pipe form [[{m.group(1)}|…]] "
                            f"(use [[{m.group(1)}]({m.group(1)}.md)])")
        for m in LINK_RE.finditer(line):
            display, target = m.group(1), m.group(2)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):   # http:, https:, mailto:
                continue
            path_part, _, frag = target.partition("#")
            path_part = decode_target(path_part)      # %20 / %28 / %29 → space / ( / )
            resolved = os.path.normpath(os.path.join(str(base_dir), path_part))
            if not os.path.exists(resolved):
                problems.append(f"{display_path}:{i} target does not exist: {target}")
                continue
            if frag.startswith("L"):
                n = line_count(resolved)
                for part in frag[1:].split(","):
                    nums = [int(x) for x in re.findall(r"\d+", part)]
                    if nums and max(nums) > n:
                        problems.append(
                            f"{display_path}:{i} line range {frag} runs past EOF: "
                            f"{path_part} has {n} lines")
            if path_part.endswith(".md") and "/" not in path_part and ".." not in path_part:
                if os.path.basename(path_part)[:-3] != display:
                    problems.append(f"{display_path}:{i} slug-reference display text "
                                    f"{display!r} is not the slug verbatim")
    return problems


def default_targets():
    targets = sorted(PAGES_DIR.glob("*.md"))
    targets += [p for p in EXTRA_DOCS if p.exists()]
    targets += sorted((WIKI_ROOT / "wiki" / "reports").glob("*.md"))
    return targets


def resolve_arg(arg):
    """An argument is a slug, a repo-relative path, or an absolute path."""
    p = Path(arg)
    if p.is_file():
        return p
    for cand in (PAGES_DIR / f"{arg}.md", WIKI_ROOT / arg, WIKI_ROOT / arg / "index"):
        if cand.is_file():
            return cand
    return PAGES_DIR / f"{arg}.md"      # report it as missing below


def check_citations(text, display_path):
    """Footnote definitions must cite source material, never a wiki page (`§ Citations`).

    `[[slug](slug.md)]` in a footnote satisfies every link check — the page exists, the display
    text matches the slug — so this class was invisible to all three gates until an LLM sweep read
    the bodies, and the corpus reached ~1,800 such footnotes (many of them a page citing *itself*).
    One summary line per page, so the count is a migration-progress number.
    """
    offenders = []
    for line in text.splitlines():
        m = FOOTNOTE_RE.match(line)
        if not m:
            continue
        link = FOOTNOTE_SLUG_TARGET_RE.match(line[m.end():])
        if link:
            offenders.append((m.group(1), link.group(1)))
    if not offenders:
        return []
    first_n, first_slug = offenders[0]
    return [f"{display_path}: {len(offenders)} footnote definition(s) cite a wiki page instead of "
            f"source material (first: [^{first_n}] → {first_slug}.md) — WIKI-SCHEMA.md § Citations "
            f"requires a source path link"]


def run_staged():
    """Pre-commit gate: validate the staged text of staged wiki/pages/*.md.

    Deliberately excludes `check_citations`: this gate must not stall an ingest that touches pages
    whose citations are still part of the corpus-wide migration. Promote it (one call, below) once
    the migration is done.
    """
    try:
        out = subprocess.run(["git", "-C", str(WIKI_ROOT), "diff", "--cached", "--name-only",
                              "--diff-filter=ACM"], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0                        # not a git repo / no git — nothing to gate
    problems = []
    checked = 0
    for rel in out.splitlines():
        rel = rel.strip()
        if not (rel.startswith("wiki/pages/") and rel.endswith(".md")):
            continue
        if Path(rel).name == "index.md" or Path(rel).name.startswith("audit-"):
            continue                          # generated / local-only artifacts
        blob = subprocess.run(["git", "-C", str(WIKI_ROOT), "show", f":{rel}"],
                              capture_output=True, text=True).stdout
        checked += 1
        problems += check_text(strip_code(blob), rel, WIKI_ROOT / Path(rel).parent)
    if problems:
        print("commit blocked — link problems in staged page(s):\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\nFix the page(s) and re-stage. To commit anyway: git commit --no-verify",
              file=sys.stderr)
        return 1
    return 0


def main(argv):
    require_wiki(WIKI_ROOT, "check-links.py")
    if "--staged" in argv:
        return run_staged()
    strict_citations = "--strict-citations" in argv
    args = [a for a in argv if not a.startswith("-")]
    targets = [resolve_arg(a) for a in args] if args else default_targets()
    problems = []
    citation_notes = []
    for path in targets:
        if not path.exists():
            problems.append(f"{path} does not exist")
            continue
        rel = os.path.relpath(path, WIKI_ROOT)
        text = strip_code(path.read_text(encoding="utf-8"))
        problems += check_text(text, rel, path.parent)
        citation_notes += check_citations(text, rel)
    if strict_citations:
        problems += citation_notes
    elif citation_notes:
        print(f"{len(citation_notes)} document(s) cite a wiki page from a footnote instead of source "
              f"material — not fatal; migrate in batches (--strict-citations to fail on these):")
        print("\n".join("  " + n for n in citation_notes))
        print()
    if problems:
        print("\n".join(problems))
        print(f"\n{len(problems)} problem(s) in {len(targets)} document(s)")
        return 1
    print(f"clean: {len(targets)} document(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
