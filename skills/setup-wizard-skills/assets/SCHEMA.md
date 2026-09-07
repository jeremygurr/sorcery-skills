# Wiki Schema

## Wiki Page Templates

All wiki pages strictly follow Google's Open Knowledge Format. It must follow valid YAML 
formatting. There are two types of wiki pages: resource pages, and concept pages. 

### Wiki Resource Page

A resource page directly describes a file from the source material of this repo. 
You must strictly use the following template. Don't add anything to the frontmatter: 

```markdown
---
type: Sources
resource: <absolute path to source material file, relative to the root of this repo>
title: <Source Title>
description: <one-line description of the source file>
tags: [<relevant tags>]
generated: { by: <current agent or harness name>/<current model>, at: <current time in ISO 8601 datetime format> }
updated: { by: <current agent or harness name>/<current model>, at: <current time in ISO 8601 datetime format> }
---

# <Source Title>

**Source:** <original source URL or file path>
**Date updated:** <today>

## Summary

<2-3 paragraph synthesis — your own words, not abstract copy-paste>

## Key Takeaways

- <bullet>

## Entities & Concepts

<list of entities/concepts as cross-reference links>

## Relation to Other Wiki Pages

<how this connects to or updates existing knowledge>
```

### Wiki Concept Page

A concept page describe a concept that is part of 1 or more source material files. 
You must strictly use the following template. Don't add anything to the frontmatter: 

```markdown
---
type: <Category based on the concept>
title: <Entity or Concept Name>
description: <one-line description for the index>
tags: [entity | concept]
generated: { by: <current agent or harness name>/<current model>, at: <current time in ISO 8601 datetime format> }
updated: { by: <current agent or harness name>/<current model>, at: <current time in ISO 8601 datetime format> }
sources:
  <add a yaml list item with a `resource:` key for each source used in this doc, the value is the absolute path to the source file relative to the root of this repo>
---

# <Name>

## Description

<synthesis across all sources that discuss this>

## Appearances in Sources

- <slug-reference to source-slug, in the wiki's link_style> — <one-line note>

## Related Concepts

- <slug-reference to related-slug, in the wiki's link_style> — <relationship>
```

## Wiki Link Style

This section defines how cross-references and citation targets are written and parsed for wikis.

### Emit

Use `[[slug](<path>)]` for every cross-reference and every citation target — a standard markdown 
link wrapped in outer brackets. The display text is the slug verbatim. The outer brackets preserve 
the visual `[slug]` cue from Obsidian; the inner link is what GitHub and other plain-markdown 
renderers will make clickable.

The same form is used in body prose, in index/list entries, and inside citation footnotes.

### Path rule: relative to the page emitting the link

The inner `<path>` must be a path **relative to the directory of the page containing the link**, 
not to the wiki root. Since all slug pages live flat in `wiki/pages/`:

- **From a page inside `wiki/pages/`** (e.g. `wiki/pages/alma.md` linking to `wiki/pages/helaman.md`): the target is in the *same* directory, so the path is just `<slug>.md`.
  - `see [[helaman](helaman.md)] for the account of the wars`
  - Using `pages/helaman.md` here would be **wrong**: GitHub resolves it against the page's own directory, giving `wiki/pages/pages/helaman.md`, which does not exist.
- **From a page outside `wiki/pages/`** (e.g. `wiki/pages/index.md`, `wiki/overview.md`): the target is one directory down, so the path is `pages/<slug>.md`.
  - `- [[helaman](pages/helaman.md)] — the record of the priests`
  - Citation footnote: `[^1]: [[helaman](pages/helaman.md)] §3.2 — "..."`

Do not prefix with `wiki/` or `./pages/` from inside `pages/`, and do not use absolute-looking paths such as `/wiki/pages/<slug>.md` — GitHub resolves those against the repository root, which breaks when the repo is viewed in a subdirectory or rendered by non-GitHub tools.

Quick check before writing a link: *"From the file I'm editing, does this path reach the target file?"* Open the target from the link and verify it exists.

Drive-by citations (paths outside of `wiki/`, and bare URLs) are unchanged by link style — they are not slug references.

### Parse

To find slug references in any wiki page, match either pattern (a wiki may legitimately contain both forms if a user has hand-edited content or imported pages):

```
\[\[([a-z0-9-]+)\]\((?:/wiki/pages/)?\1\.md\)\]             (markdown form, pages/ prefix optional)
```

The `/wiki/pages/` prefix is optional in the parse because it is correct for pages outside `wiki/pages/` but must be absent for pages inside `wiki/pages/`. The captured group is the slug; resolve to `wiki/pages/<slug>.md`.

Reading is permissive; writing is strict.

## Concept Identity

The slug **is** the concept's identity — there is no separate id. A concept is the
page at `wiki/pages/<slug>.md`; everything that links to it uses `[[slug]]`. This only
works if the link graph is trustworthy, so two rules hold everywhere links are written:

1. **Links are verified, never invented.** Before writing any `[[slug]]`, the slug must
   resolve to an existing `wiki/pages/<slug>.md` **or** to a page being created in the
   same operation. List the existing page set first (`ls wiki/pages/`); never emit a
   link to a slug you have not confirmed. A `[[slug]]` that resolves to nothing is a
   hallucinated link — the failure this discipline exists to prevent.

2. **Homonyms get qualified slugs.** When a new concept collides with an existing slug
   for a *different* sense, qualify both with a discriminator rather than overloading
   one page:
   - `mercury-planet` / `mercury-element` / `mercury-mythology`
   - `transformer-ml` / `transformer-electrical`

   Pick the narrowest discriminator that disambiguates. `wiki-lint` warns when slugs
   sharing a base token look like an unintended collision.

Consolidating two pages that turn out to be the same concept (merge), or separating one
overloaded page into qualified pages (split), is the job of the `wiki-merge` skill.

## Citations

Cite every non-common-knowledge factual claim. "Common knowledge" = uncontroversial,
undergraduate-level facts in this wiki's domain. Granularity is paragraph or claim,
never per-sentence. If you cannot produce a citation in one of the forms below,
find one, weaken the claim, or drop it.

Format: Markdown footnotes. Two citation kinds, three valid targets.
The slug-target form below follows the `link_style` declared above; the examples
shown here use that style.

**Quote citation** (preferred):
```
The model uses 8 attention heads.[^1]

[^1]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2.2 L142-143 — "We employ h = 8 parallel attention layers"
```

**Synthesis citation** (when no single quote captures the claim):
```
The architecture is fundamentally an encoder-decoder with attention.[^2]

[^2]: [[attention-is-all-you-need](pages/attention-is-all-you-need.md)] §3.2-3.4 [synthesis] L138-202 — encoder, decoder, and
      attention sections together describe the full multi-head architecture
```

`L142-143` / `L138-202` are line ranges in the raw source file. For a quote they mark
the lines the quote is taken from; for a synthesis they mark the block being summarized.

Three rules for every footnote:

1. **The cited target is one of three forms:**
   - A slug reference to a source-type wiki page, written in the wiki's
     `link_style` (preferred for sources you've updated via `wiki-update`)
   - `raw/<file>` or `assets/<file>` — a path to a local file (for drive-by
     citations where a synthesis page isn't worth creating)
   - `<URL>` — a live URL, tweet, or ephemeral source (no local copy required)

   Never cite entity, concept, or analysis pages — those are syntheses, not sources.

2. **A locator is present.** Always a semantic locator: `§<section>`, `p.<n>`,
   `[HH:MM:SS]` for transcripts, URL anchor for web, or `(YYYY-MM-DD)` for dated posts.

   **Plus a line-range when the source is text-addressable.** If the resolved raw
   file is markdown, plaintext, code, or cached HTML, append a line-range token after
   the semantic locator:

   - `L<start>-<end>` — a range, e.g. `L142-145`
   - `L<n>` — a single line, e.g. `L142`
   - `L142-145,L201-203` — disjoint ranges

   The line range refers to lines in the **raw source file** resolved from the target
   (`[[slug]]` → its `**Source:**` raw path; or a direct `raw/<file>`/`assets/<file>`).
   `raw/` is immutable, so these line numbers are stable references.

   A line-range is **required** for text-addressable sources and applies to BOTH
   citation kinds — a `[synthesis]` footnote marks the block it summarizes with `L…`
   just as a quote marks the lines it quotes. **Exempt** (semantic locator only, no
   `L…`): PDFs, transcripts, and live URLs with no local cached copy.

3. **Either a verbatim quote, or the `[synthesis]` tag plus a description** of
   what the cited range supports. No third option.

**Drive-by citation examples:**
```
[^3]: raw/scaling-laws.pdf p.7 — "loss scales as a power law in compute"
[^4]: https://twitter.com/user/status/123 (2026-04-15) — "<tweet text>"
```

## Cross-Model Review

`wiki-audit strong` runs a second-opinion pass with a different-provider model and
stamps the audited page with an optional `review:` frontmatter block:
```
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: YYYY-MM-DD
  status: clean         # or: disputed
  findings: 2           # present only when status: disputed
```
- `status: clean` — the reviewer surfaced no disagreement with the normal audit.
- `status: disputed` — the reviewer flagged overreach or a contradiction the normal
  audit missed; `findings:` carries the count. The detail lives in the (local-only)
  audit report.
- `provider: anthropic` (the `claude-sonnet` fallback) means no different-provider CLI
  was available, so the check is same-provider and weaker.

This block is optional and is added only by `wiki-audit strong`. Pages never need it to
be valid.

## Contradiction Check

`wiki-update` runs a cheap contradiction check on the pages each update touches, before it
commits. It is a **gate, not an annotation**: every page that lands in git is clean.

- **Scope — touched neighbors only.** The check compares the pages an update wrote or
  edited against (a) themselves and (b) the pages that update already read (the entity /
  concept pages it updated and the neighbor pages from its backlink audit). It does NOT
  re-read the whole wiki — a conflict with a distant, untouched page is left to the
  periodic `wiki-lint` sweep.
- **Blocking vs. soft.** A **blocking** contradiction is a real factual conflict on the same
  entity under the same scope — incompatible dates, counts, names, or mutually-exclusive
  claims. A **soft** tension (differing emphasis, values within plausible version /
  measurement variance, claims that hold under different scope) is not a conflict.
- **The transient blocker flag.** When a blocking contradiction is found, a single line is
  written to the affected page's frontmatter and the update stops before committing:
  ```yaml
  contradiction-check: failed — <one-line reason naming the counterpart [[slug]] or "internal">
  ```
  The machine-readable token is the literal `contradiction-check: failed`. It exists ONLY
  while the conflict is unresolved; resolving the conflict **removes the line**. A committed
  page never carries it — there is no `passed` stamp, no severity history, nothing. Absence
  of the flag is the only "clean" state.
- **Soft tensions are surfaced, not recorded** — mentioned in the update summary so you can
  act if you wish, but never persisted and never blocking.

This flag is also what the **Pre-commit Gate** below scans staged files for.

## Pre-commit Gate

On a git wiki, `bin/hooks/pre-commit` (installed by `wiki-init` via
`git config core.hooksPath bin/hooks`) runs **two** deterministic gates before every commit —
no LLM:

1. **`bin/check-contradictions.py`** — scans the **staged** content of `wiki/pages/*.md`,
   frontmatter only, and **blocks the commit** if any page still carries a
   `contradiction-check: failed` flag. Backstop to the skill-level hold in `wiki-update`
   step 7b; on a healthy wiki it never fires. Resolve the contradiction and remove the
   `contradiction-check:` line, then re-stage.
2. **`bin/lint-mechanical.py --staged`** — scans the staged pages for **structural**
   problems and **blocks the commit** on any: missing required frontmatter, a broken
   `[[link]]`, or a slug collision (a bare slug clashing with a qualified one). Fix the page
   and re-stage.

- **Fresh clone:** `core.hooksPath` is repo-local config and is not cloned — re-run
  `git config core.hooksPath bin/hooks` once after cloning.
- **Override** an intentional commit with `git commit --no-verify`.

## Operation Log & Commit Convention
Operations: init, update, query, update, lint, audit, merge, split

**The git history is the operation log.** After an operation, the skill
suggests a commit message and commits on your confirmation (skills never auto-commit).
Render the human log on demand with `python wiki/bin/render-log.py`.

The suggested subject line follows the repo's commit convention:
1. **Detect an existing convention first** — scan recent `git log` and any `.gitmessage`,
   commitlint config, or `CONTRIBUTING.md`. If the repo already has a subject style,
   follow it.
2. **Default to Conventional Commits** when none is found, choosing the type by operation:

   | Operation        | Type                                  |
   |------------------|---------------------------------------|
   | init             | `chore`                               |
   | update           | `docs`                                |
   | update           | `docs`                                |
   | query (saved)    | `docs`                                |
   | lint             | `fix` if fixes applied, else `chore`  |
   | audit            | `fix` if fixes applied, else `chore`  |
   | merge / split    | `refactor`                            |

**Always append a `Wiki-Op:` trailer**, whatever the subject style — it is what
`render-log.py` keys on, decoupling the log from the subject convention. Which pages
changed is read from the commit diff, so no `Pages:` trailer is needed.
```
docs: summarize Attention Is All You Need

Wiki-Op: update
```

## Index Generation
`wiki/pages/index.md` is a generated artifact — never hand-edit it. It is rebuilt
from page frontmatter by `wiki/bin/okf`:
- Run `python wiki/bin/okf` (or `python3`) **after** any operation that adds, removes, renames, or re-categorizes a page.
- The generator groups pages by their Cateogry (stored in `type` in frontmatter), in the order categories are
  listed under **Index Categories** below; within a type it lists pages newest-first
  by `created`. Each entry is `- [[slug]] — summary _(created)_`.
  If a Category has no pages, then that Category won't be shown in the index.
- Pages whose filename matches `audit-*.md` are excluded (gitignored local-only
  artifacts). A page with an unrecognized or missing `type` lands in an
  `Uncategorized` section.

## Index Categories
Categories: Sources | Entities | Concepts | Analyses | Modules | APIs | Decisions | Flows

Not all categories need to be used. A codebase will use categories like Sources, Modules, APIs, Decisions, 
and Flows. A general purpose document or research repo may use Sources, Entities, Concepts, 
Analyses. Use what is appropriate for the subject/concept/object being described. When in doubt, ask the user.

Note that the Category is written into the `type` field of frontmatter.

## Conventions
- These wiki skills should never modify anything outside of the wiki folder.
- wikis are expected to be git repositories
- operation log: git wikis record each op as a commit (see Operation Log & Commit Convention) and render it with bin/render-log.py
- index.md is GENERATED by wiki/bin/okf and is saved in the repo to make it easier to browse — 
  never hand-edit it; set page frontmatter (type, summary) and regenerate instead
- All pages live flat in wiki/pages/ — no subdirectories
- overview.md reflects the current synthesis across all sources
- Cross-reference and citation slug-targets follow conventions specified in wiki/SCHEMA.md .
  every skill reads it before writing or scanning links
- contradiction check: update gates on blocking contradictions in touched pages via a transient 
  `contradiction-check: failed` flag, removed before commit — committed pages are always clean (see 
  Contradiction Check)
- pre-commit gate: git wikis run bin/hooks/pre-commit (via core.hooksPath) → 
  bin/check-contradictions.py, which blocks any commit staging a page that still carries the flag 
  (see Pre-commit Gate); re-run `git config core.hooksPath bin/hooks` after a fresh clone

# Wiki Tools

## okf

A binary excutable for working with Open Knowledge Format wikis. It returns responses in json to be 
more agent friendly. If you run into trouble using this tool, you can read more about it: 
https://github.com/okfcli/okf .

the `okf schema` command will return a json object containing all of the available commands, what they do, and how to use them.

