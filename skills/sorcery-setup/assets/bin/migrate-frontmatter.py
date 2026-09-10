#!/usr/bin/env python3
"""One-shot migration of wiki/pages/* frontmatter to the OKF templates in wiki/WIKI-SCHEMA.md.

category -> type, summary -> description, created/updated -> generated/updated provenance
maps, and the `sources:` slug list -> a `resource:` / `sources: - resource:` list of
repo-relative source paths. Deterministic; run once. Bodies are left untouched here.

generated.at keeps each page's original `created` date; updated.at keeps its original
`updated` date, because this migration changes only metadata, not the prose.
"""
import re, pathlib

BOOKS = ["1-Nephi", "2-Nephi", "Jacob", "Enos", "Omni", "Words-of-Mormon", "Mosiah",
         "Alma", "Helaman", "3-Nephi", "4-Nephi", "Mormon", "Moroni", "Ether", "Jarom"]
SRC = {b.lower(): f"raw/bom/{b}-*.txt" for b in BOOKS}
SRC["intro"] = "raw/bom/Intro.txt"
TYPES = {"Sources", "People", "Places", "Concepts", "Analyses"}
CAT2TYPE = {"Figures": "People", "Events": "Analyses", "Sources": "Sources",
            "Places": "Places", "Concepts": "Concepts"}
BY = '"pi/qwen3.8-flash-next"'
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEYS = ("title", "category", "summary", "tags", "sources", "created", "updated")

def field(lines, key):
    for ln in lines:
        if ln.startswith(key + ":"):
            return ln[len(key) + 1:].strip()
    return None

def migrate(path):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        raise SystemExit(f"{path}: no frontmatter")
    lines = m.group(1).splitlines()
    fm = {k: field(lines, k) for k in KEYS}
    if bad := [k for k, v in fm.items() if not v]:
        raise SystemExit(f"{path}: missing {bad}")
    if fm["category"] not in CAT2TYPE:
        raise SystemExit(f"{path}: unmapped category {fm['category']!r}")
    rtype = CAT2TYPE[fm["category"]]
    slugs = [s.strip() for s in fm["sources"].strip("[]").split(",") if s.strip()]
    if unknown := [s for s in slugs if s not in SRC]:
        raise SystemExit(f"{path}: unknown source slug(s) {unknown}")
    if rtype == "Sources":
        if len(slugs) != 1:
            raise SystemExit(f"{path}: source page with sources {slugs}")
        src_block = f"resource: {SRC[slugs[0]]}\n"
    else:
        src_block = "sources:\n" + "".join(f"  - resource: {SRC[s]}\n" for s in slugs)
    fm_new = (
        f"type: {rtype}\n"
        f"title: {fm['title']}\n"
        f"description: {fm['summary']}\n"
        f"tags: {fm['tags']}\n"
        f"generated: {{ by: {BY}, at: {fm['created']}T00:00:00Z }}\n"
        f"updated: {{ by: {BY}, at: {fm['updated']}T00:00:00Z }}\n"
        f"{src_block}"
    )
    path.write_text("---\n" + fm_new + "---\n" + text[m.end():], encoding="utf-8")

pages = sorted(pathlib.Path("wiki/pages").glob("*.md"))
for p in pages:
    migrate(p)
print(f"migrated {len(pages)} pages")
