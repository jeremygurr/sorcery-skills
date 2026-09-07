---
name: wiki-update
description: Use after source material in this repo has changed. This will update the wiki pages. 
disable-model-invocation: true
---

# Wizard Wiki Update

Ingests any new source material into the wiki. Read it, then write a summary 
page, update entity/concept pages, and maintain the index and overview.

## Process

### 0. Load the SCHEMA

read the wiki/SCHEMA.md file if it hasn't been already. 

### 1. Get list of files that have changed

If: the wiki/last_update.yml file exists

Then: 
  - read the file, grab the value of commit_hash from it
  - figure out the hash of the commit that FOLLOWED this commit_hash
  - do a show-files-only diff between the HEAD of the current branch and that commit hash to get a list 
    of files changed since the wiki update was last run.

Else: 
  the list of files changed is all source files in the repo (includes all files outside of the 
  /wiki folder). 

Exclude from this list .gitignore, AGENTS.md, and everything that matches the .gitignore file.

Each of these files in the list is called a source material file.

If: There are more than 3 files in the list
Then: Process each file in a subagent, using a maximum of 3 at a time. 
Else: Process each file sequentially.

For each of those files, apply all of these steps:

### 2. Read the source in full

Read all content. For long sources, read in sections. Do not skip.

### 3. Generate the slug from what you know about this file's identity

Lowercase, hyphens, no special characters.
Example: "Attention Is All You Need" → `attention-is-all-you-need`

### 4. Write/Update the source summary page

Write `wiki/pages/<slug>.md`, using the Wiki Resource Page template, replacing it if necessary.

### 5. Cite as you write — do not skip

While drafting the Summary, Key Takeaways, and any other prose section, every non-common-knowledge 
factual claim must carry a footnote. 

Two citation kinds, three valid targets:

```
Quote:     [^N]: <target> <locator> — "<verbatim quote>"
Synthesis: [^N]: <target> <locator> [synthesis] — <what supports the claim>

<target> is one of:
  <slug-reference>     — a source wiki page, written in the wiki's link_style
                         (preferred for the source you're ingesting)
  <folder>/<file>      — a path, for drive-by citations to other local files
  <URL>                — a live URL or post
```

For the source being ingested, the slug-reference target is `<this-source-slug>` written in the 
form prescribed by the wiki link style. `wiki-update` is creating that page now, so the target 
exists by the time the page is read.

**Line-range provenance — required for text-addressable sources.** If the raw file you are citing 
is markdown, plaintext, code, or cached HTML, every footnote to it must carry a line-range token 
after the semantic locator: `L<start>-<end>` (or `L<n>` for a single line). As you read the raw 
file, note the line numbers of the passage you are citing — for a quote, the lines the quote is 
taken from; for a `[synthesis]` claim, the block of lines being summarized. Example:

```
[^1]: [[<this-source-slug>]] §3.2 L142-143 — "We employ h = 8 parallel attention layers"
[^2]: [[<this-source-slug>]] §3.2-5.3 [synthesis] L138-202 — encoder/decoder + attention describe the architecture
```

Sources WITHOUT stable line numbers — PDFs, transcripts, and live URLs with no local cached copy — 
are exempt: keep the semantic locator (`p.N`, `[HH:MM:SS]`, URL anchor) and omit `L…`.

If you cannot produce either citation kind for a claim, you do not have a citation. Find one, 
weaken the claim ("the paper suggests..."), or drop it.

Footnotes go at the bottom of the page, below all sections. Number them sequentially in order of 
first reference.

### 6. Self-check before continuing

Re-read the draft once. Three passes:

1. **Unfootnoted claims** — scan for factual claims with no footnote (the most common failure mode 
   in long update sessions). For each, add a footnote or revise the wording.
2. **Missing line-ranges** — for every footnote whose target is a text-addressable raw file 
   (markdown / plaintext / code / cached HTML), confirm an `L…` token is present.  A text-source 
   footnote with no line-range is incomplete: go back to the raw file, find the lines, and add the 
   token. Exempt sources (PDF / transcript / live URL) are fine without one.
3. **Link resolution** — collect every `[[slug]]` you wrote in this page and confirm each resolves 
   to an existing `wiki/pages/<slug>.md` or to a page you are creating in this same update. Any 
   `[[slug]]` that resolves to neither is a hallucinated link: remove it, or create the page it points 
   to. This is the inline version of the broken-link check `wiki-lint` runs wiki-wide — catching it 
   now keeps the link graph trustworthy by construction.

Only when all three passes are clean do you move on to entity pages.

### 7. Update entity and concept pages

For each entity/concept touched by this source:

- **Page exists:** Read it, add to or update the relevant section, add this source to frontmatter 
  `sources` list, update `updated` date.  If the page has invalid frontmatter, for example if it's 
  missing the required `type:` key, then rebuild the frontmatter section. 
- **Page doesn't exist:** Create it:

Write `wiki/pages/<slug>.md`, using the Wiki Concept Page template.

### 8. Backlink audit — do not skip

Scan ALL existing pages in `wiki/pages/` for any that mention this source's entities/concepts but 
don't yet link to the new page. Add new cross-references to the new page. You can use `okf 
backlinks wiki/pages <slug>` to find these quickly.

A compounding wiki's value comes from bidirectional links.

**Before adding each `[[slug]]`, apply the Concept Identity rule:** the target must
resolve to a real page. When you mention an entity that *should* have a page but doesn't,
create the page rather than linking to a slug that resolves to nothing.

**Final link-resolution sweep.** Once every page this update touched is written (summary, 
entity/concept pages, backlinks), collect all `[[slug]]` references across *those* pages and 
confirm each resolves to an existing `wiki/pages/<slug>.md`. Fix any unresolved link before moving 
on — remove it or create its page.

### 9. Contradiction check — do not skip

Now that every page this update touched is written and you have its neighbors in context,
check for contradictions **before** committing. Read the **Contradiction Check** section in
`SCHEMA.md` for the full convention. This is a gate, not an annotation: a clean update
leaves no contradiction metadata on any page.

**Scope — what to compare (do NOT re-read the whole wiki):**
- each page you wrote/edited against itself (internal contradictions), and
- each page you wrote/edited against the pages you already read this update — the
  entity/concept pages from step 7 and the neighbor pages from the step 8 backlink audit.

A conflict with some distant page you never opened is out of scope here — the periodic
`wiki-lint` sweep is the backstop for that.

**Classify each contradiction you find:**

1. **Blocking** — a real factual conflict on the same entity under the same scope:
   incompatible dates, counts, names, or mutually-exclusive claims (e.g. the new source page
   says a model launched in 2024 but `[[that-model]]` already says 2023). For each blocking
   contradiction, write a single line into the affected page's frontmatter — the page you
   touched that carries the *newer* claim:
   ```yaml
   contradiction-check: failed — launch year conflicts with [[that-model]] (2024 vs 2023)
   ```
   Use `internal` in place of the `[[slug]]` for a within-page conflict. Then **stop — do
   not proceed to the commit step (step 12).** Surface the conflict (both claims, both
   locations) and offer the user these resolutions:
   - correct the newly-written page,
   - correct the counterpart page,
   - reconcile both with a scope qualifier,
   - or confirm it is not actually a conflict (it was a soft tension — see below).

   When a conflict is resolved, **remove the `contradiction-check` line** from the page.
   Only once no `contradiction-check: failed` line remains on any touched page do you
   continue.

2. **Soft** — a tension that is not a true conflict: differing emphasis, values within
   plausible version/measurement variance, or claims that hold under different scope. Do
   **not** write anything to any page and do **not** block. Note it for the step 11 summary
   so the user can act if they wish; the periodic `wiki-lint` sweep is the backstop.

### 10. Regenerate `wiki/pages/index.md`

Do **not** hand-edit the index. Every page you wrote this update already carries the important 
fields in its frontmatter — that is the index's source of truth. Regenerate it:

```
okf index wiki/pages
```

If the generator warns about a page with no frontmatter or a page lands in `Uncategorized`, fix 
that page's frontmatter and rerun.

### 11. Update `wiki/pages/overview.md`

Re-read the current overview (if it exists). If this source:
- Introduces a significant concept: add it to "Key Entities / Concepts"
- Shifts the overall understanding: update "Current Understanding"
- Raises a new question: add it to "Open Questions"

Update the frontmatter `generated:at:` datetime.

### 12. Record the operation

**Gate first:** do not suggest a commit while any page touched this update still carries a
`contradiction-check: failed` line (step 9). Resolve the blocking contradiction and remove
the line first — committed pages are always clean.

Per SCHEMA's **Operation Log & Commit Convention**:
- **Git wiki:** stage the wiki changes and suggest a commit (subject follows the repo's
  convention — default Conventional Commits `docs:` for an update — plus the trailer).
  Commit on the user's confirmation; never auto-commit.
  ```
  docs: summarize <source title>

  Wiki-Op: update
  ```
- **Non-git wiki:** append to `wiki/log.md`:
  ```
  ## [<today>] update | <source title>
  Pages written: <slug>
  Pages updated: <comma-separated list>
  ```

## Common Mistakes

- **Appending chronological updates instead of editing in-place** — Wiki pages are living documents, not journals. Do not add sections like `## April 27 update:` or `**Update:**` followed by new content. Update the relevant section in-place, bump the `updated` frontmatter date, and record what changed in the operation log (a commit on a git wiki, or `log.md` otherwise). The log is the historical record; pages are the current truth.
- **Skipping the backlink audit (step 8)** — A wiki's value compounds through bidirectional links. Always scan existing pages for entities this source introduces.
- **Inventing `[[slug]]` links** — Never write a cross-reference to a slug you have not confirmed exists or are creating now. A link that resolves to nothing is a hallucinated link. Verify against the existing page set (`ls wiki/pages/`); see the Concept Identity rule in `SCHEMA.md`.
- **Summarizing the abstract instead of synthesizing** — The Summary section should reflect your own synthesis, not a rephrased abstract.

### 13. Commit

1. Save the most recent commit hash into wiki/last_update.yml. Replace the file if it already exists. Use this template:
``` yaml
commit_hash: <hash>
```

2. Commit the changes to the repo, and push those changes to origin if there is an origin remote configured.

### 14. Report to user

- Summary page: `wiki/pages/<slug>.md`
- Entity/concept pages created or updated: <list>
- Pages that received backlinks: <list>
- Index and overview updated
- Soft tensions noted (step 9): <list any non-blocking tensions, or "none"> — not recorded on any page; act on them if you want


