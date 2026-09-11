#!/usr/bin/env python3
"""One-shot migration of wiki/pages/* frontmatter to the OKF templates in wiki/WIKI-SCHEMA.md.

The pre-schema wiki wrote its metadata in a shape OKF rejects: `category:` instead of
`type:`, `summary:` instead of `description:`, bare `created:`/`updated:` dates instead of
the `generated:`/`updated:` provenance maps, and a `sources:` list of *wiki page* slugs
where the schema wants a list of repo-relative `resource:` paths. `okf` refuses to load
the bundle until this is fixed, so `okf index` / `okf lint` and the pre-commit gate are all
dead until it is.

The slug -> resource path map is derived, not hardcoded: the raw-path -> volume number comes
from the filenames in raw/ancient-christian-writers-collection/, and each resource page's own
volume number from its `**Source:**` line. A non-resource page's `sources:` entries are
resource-page slugs, resolved through that map one hop.

Bodies are left untouched here (link style inside bodies is a separate migration).

Usage:
    python3 wiki/bin/migrate-frontmatter.py [--dry-run] [--by NAME/MODEL]

generated.at / updated.at keep each page's original `created` / `updated` dates, so the
migration only changes metadata shape, never the recorded history.
"""
import argparse
import json
import pathlib
import re
import sys

RAW = pathlib.Path("raw/ancient-christian-writers-collection")
PAGES = pathlib.Path("wiki/pages")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DEFAULT_BY = "pi/unknown"


def field(fm, key):
    m = re.search(rf"^{key}: *(.*)$", fm, re.M)
    return m.group(1).strip() if m else None


def q(value):
    """A YAML scalar that survives a `: ` or `#` inside the value. Old `summary:` lines were
    quoted by hand when they needed it and not when they didn't; re-quoting uniformly via
    json.dumps is the one form that is always valid."""
    v = value.strip()
    if len(v) > 1 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1].replace('\\"', '"')
    return json.dumps(v, ensure_ascii=False)


def volume_map():
    """ACW number -> raw file path, from the collection's filenames."""
    vol = {}
    for f in sorted(RAW.glob("*.txt")):
        m = re.search(r"ACW (\d+)", f.name)
        if not m:
            raise SystemExit(f"{f}: no volume number in filename")
        vol[m.group(1).zfill(3)] = str(f)
    return vol


def build_map(vol):
    """resource-page slug -> raw file path, one hop, derived from each page's Source line."""
    slug2path = {}
    for p in sorted(PAGES.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if not re.search(r"^category: Sources$", text, re.M):
            continue
        line = re.search(r"^\*\*Source:\*\*.*$", text, re.M)
        if not line:
            raise SystemExit(f"{p}: no **Source:** line")
        m = re.search(r"(?:ACW|Ancient Christian Writers)\s*0*(\d+)", line.group(0))
        if not m:
            raise SystemExit(f"{p}: no volume number in its **Source:** line")
        path = vol[m.group(1).zfill(3)]
        if not pathlib.Path(path).exists():
            raise SystemExit(f"{p}: derived resource path does not exist: {path}")
        slug2path[p.stem] = path
    return slug2path


def migrate(path, slug2path, by, dry):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise SystemExit(f"{path}: no frontmatter")
    fm = m.group(1)
    missing = [k for k in ("title", "category", "summary", "tags", "sources", "created", "updated")
               if field(fm, k) is None]
    if missing:
        raise SystemExit(f"{path}: missing {missing}")
    rtype = field(fm, "category")
    slugs = [s.strip() for s in field(fm, "sources").strip("[]").split(",") if s.strip()]
    if rtype == "Sources":
        # A resource page describes one file: its own volume. Extra slugs in the old list are
        # "related sources", which the template has no slot for; they belong in the body's
        # Relation to Other Wiki Pages section.
        extras = [s for s in slugs if s != path.stem]
        src_block = f"resource: {q(slug2path[path.stem])}\n"
        if extras:
            print(f"  note {path.name}: dropped related sources {extras} (schema has no slot)")
    else:
        unknown = [s for s in slugs if s not in slug2path]
        if unknown:
            print(f"  note {path.name}: dropped non-resource slugs {unknown} from sources:")
        paths = sorted({slug2path[s] for s in slugs if s in slug2path})
        src_block = "sources:\n" + "".join(f"  - resource: {q(p)}\n" for p in paths)
    fm_new = (
        f"type: {rtype}\n"
        f"title: {q(field(fm, 'title'))}\n"
        f"description: {q(field(fm, 'summary'))}\n"
        f"tags: {field(fm, 'tags')}\n"
        f"generated: {{ by: {by}, at: {field(fm, 'created')}T00:00:00Z }}\n"
        f"updated: {{ by: {by}, at: {field(fm, 'updated')}T00:00:00Z }}\n"
        f"{src_block}"
    )
    new = "---\n" + fm_new + "---\n" + text[m.end():]
    if dry:
        return new
    path.write_text(new, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the new frontmatter, write nothing")
    ap.add_argument("--by", default=DEFAULT_BY, help="provenance value for generated.by / updated.by")
    args = ap.parse_args()

    slug2path = build_map(volume_map())
    pages = sorted(PAGES.glob("*.md"))
    for p in pages:
        out = migrate(p, slug2path, args.by, args.dry_run)
        if args.dry_run:
            print(f"=== {p.name}\n{out.split('---')[1].strip()}")
    print(f"{'would migrate' if args.dry_run else 'migrated'} {len(pages)} pages")


if __name__ == "__main__":
    sys.exit(main())
