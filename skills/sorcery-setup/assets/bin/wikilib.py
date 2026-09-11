#!/usr/bin/env python3
"""Shared link patterns and wiki-root discovery for the deterministic wiki gates.

`lint-mechanical.py` (link graph + structure) and `check-links.py` (link targets + line
ranges) have to agree on what a slug reference *is*; when each carried its own regex they
drifted, and one gate's notion of a slug ref stopped matching the forms WIKI-SCHEMA.md
emits. This module is the single definition. Stdlib only, and import-side-effect free —
neither root resolution nor process exits happen here.

Link forms per WIKI-SCHEMA.md `## Emit`, where the display text is the slug verbatim:

    [[slug](slug.md)]                from a page inside wiki/pages/ (same directory)
    [[slug](pages/slug.md)]          from wiki/overview.md or wiki/pages/index.md
    [[slug](/wiki/pages/slug.md)]    absolute
    [[slug](slug.md#L4-8)]           with a line range

The optional path prefix deliberately stops short of `../`, so source path links
(`[[CONTEXT.md](../../CONTEXT.md)]`) and URLs can never match: a source path is not a slug
reference, per SCHEMA. Bare `[[slug]]` / legacy `[[slug|display]]` are not slug references
either — `check-links.py` reports those as malformed.
"""
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

# Group "slug" (also group 1) is the referenced page. Use .finditer + group("slug"); a
# findall returns the (slug, target) tuple.
LINK_RE = re.compile(
    r"\[\[(?P<slug>[a-z0-9-]+)\]\("
    r"(?P<target>(?:/wiki/pages/|pages/)?(?P=slug)\.md(?:#L[\d,-]+)?)\)\]")

# Every `[[display](target)]` shape, canonical or not — what check-links walks to validate
# targets and line ranges. Deliberately broader than LINK_RE.
ANY_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\(([^)\s]+)\)\]")

# Slug references in forms a renderer shows as literal text: no target at all, or the
# pre-standard pipe form.
BARE_RE = re.compile(r"\[\[([a-z0-9-]+)\](?!\()")
PIPE_RE = re.compile(r"\[\[([a-z0-9-]+)\|[^\]]+\]\]")


def decode_target(target):
    """Percent-decode the path part of a link target before resolving it on disk.

    A link's inner target may not contain a space or a `)`, so a source path carrying either
    is written percent-encoded in the link only (`%20`, `%28`, `%29`) — WIKI-SCHEMA.md § Percent-
    encoding. An encoded link must be verified exactly like a plain one, existence and line range.
    """
    return unquote(target)


def git_toplevel(start):
    """The top level of the git repository enclosing `start`, or None (no repo, no git).

    Scoped to `start` rather than the process working directory, so the root is always the
    repository the scripts themselves live in, whatever directory a hook or caller invokes them from.
    """
    try:
        result = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    top = result.stdout.strip()
    return Path(top).resolve() if top else None


def find_repo_root(start=None):
    """The wiki root = the git toplevel, else the nearest ancestor, containing wiki/pages.

    git first so the gates track the repository even when the scripts are symlinked or run
    from an unexpected working directory; the ancestor walk covers wikis that are not git
    repos, and the `<repo>/bin/` layout where the scripts sit above `wiki/`. Returns the
    top of the filesystem when nothing matches — callers gate on `require_wiki`, which turns
    "no wiki here" into an error instead of a silently clean report.
    """
    d = Path(start).resolve() if start else Path(__file__).resolve()
    d = d.parent if d.is_file() else d
    top = git_toplevel(d)
    if top is not None and (top / "wiki" / "pages").is_dir():
        return top
    while d != d.parent and not (d / "wiki" / "pages").is_dir():
        d = d.parent
    return d


def require_wiki(root, caller):
    """Return `root` if it holds a wiki, else exit non-zero with an actionable message.

    A gate that finds no pages reports "everything clean", which is the failure mode this
    exists to prevent: an unresolvable root must never look like a pass.
    """
    if not (root / "wiki" / "pages").is_dir():
        raise SystemExit(
            f"{caller}: no wiki/pages directory under {root}\n"
            "  Not a wiki root — check that this repo was set up by the sorcery-setup skill,\n"
            "  and that the scripts live at wiki/bin/ (or <repo>/bin/) inside it.")
    return root
