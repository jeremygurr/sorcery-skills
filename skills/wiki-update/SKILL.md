---
name: wiki-update
description: Use after source material in this repo has changed. This will update the wiki pages. 
disable-model-invocation: true
---

# Wiki Update

Ingests any new source material into the wiki. Read it, then write a summary 
page, update wiki pages, and maintain the index and overview.

It can optionally take as a parameter one or more source paths to update. If files are given, then
skip the logic that computes which files need to be updated, and use this file list instead.

The steps from the sections below must be executed like this:
- Pre-Processing Steps (controller agent)
- Source Page Processing Steps (worker agents if processing in parallel, controller agent if processing
  sequentially)
- Post-Processing Steps (controller agent)

The controller agent refers to the current agent. Worker agents are basic delegates which may be
spawned later as instructed.

## Pre-Processing Steps

### 1. Figure out list of source files to process

We need a list of files that changed (added, modified, moved, or deleted) since the last wiki
update.

If: one or more file paths were given to this skill as a parameter, then use those files and skip to
the next step. 

If: the wiki/last_update.yml file exists
Then: 
  - read the file, grab the value of commit_hash from it
  - figure out the hash of the commit that FOLLOWED this commit_hash
  - do a show-files-only diff between the HEAD of the current branch and that commit hash to get a
    list of files changed since the wiki update was last run.
Else: 
  the list of files changed is all source files in the repo (includes all files outside of the 
  /wiki folder). 

Exclude from this list .gitignore, AGENTS.md, and everything that matches whats in the .gitignore
file.

If: a raw/ folder exists at the top of this repo
Then: exclude from the update list all files/folders NOT in raw/

Each of these files in the list is called a source material file and represents a file that has been
changed, either created, modified, or deleted.

### 2. Launch processing agents

Run the Source Page Processing Steps below for each file. 

If: There are more than 3 files in the list 
    And the maximum concurrency for subagents > 1
Then: Process each file in parallel by a subagent. 
Else: Process each file sequentially.

## Source Page Processing Steps

### 1. Load the SCHEMA

Do this if the wiki/SCHEMA.md file hasn't already been read:

If: wiki/SCHEMA.md doesn't exist
Then: Tell the user they need to run the setup-wizard-skills skill first, and abort this skill.
Else: read the wiki/SCHEMA.md file.

### 2. Read the source in full

If it's a modified or created file: read all content. For long sources, read in sections. Do not skip.

### 3. Generate the slug from what you know about this file's identity

Lowercase, hyphens, no special characters.
Example: "Attention Is All You Need" → `attention-is-all-you-need`

### 4. Delete file and its references if deleted

If this file was deleted:
- Delete the corrosponding wiki page if it exists.
- Search for any references or links to this page, and remove those also. 
- Skip the remaining Source Paeg Processing steps for this file, since the other steps only apply to
  source files that still exist.

### 5. Update references if moved

If this file was moved:
- Update the corrosponding wiki page if it exists.
- Search for any references or links to this page, and update those to point to the new location. 
- If there are no modifications to the source file itself, skip the remaining Source Page Processing
  Steps for this file, since the other steps only apply to source files that had their content
  changed.

### 6. Write/Update the source summary page

If the file was modified or created:
- Write `wiki/pages/<slug>.md`, using the Wiki Resource Page template, replacing it if necessary.

### 7. Cite as you write — do not skip

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

### 8. Self-check before continuing

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

### 9. Update entity and concept pages

For each entity/concept touched by this source:

- **Page exists:** Read it, add to or update the relevant section, add this source to frontmatter 
  `sources` list, update `updated` date.  If the page has invalid frontmatter, for example if it's 
  missing the required `type:` key, then rebuild the frontmatter section. 
- **Page doesn't exist:** Create it:

Write `wiki/pages/<slug>.md`, using the Wiki Concept Page template.

### 10. Backlink audit — do not skip

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

### 11. Contradiction check — do not skip

Now that every page this update touched is written and you have its neighbors in context, check for
contradictions. Read the **Contradiction Check** section in `SCHEMA.md` for the full convention.
This is a gate, not an annotation: a clean update leaves no contradiction metadata on any page.

**Scope — what to compare (do NOT re-read the whole wiki):**
- each page you wrote/edited against itself (internal contradictions), and
- each page you wrote/edited against the pages you already read this update — the
  entity/concept pages from earlier and the neighbor pages from the backlink audit.

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
   not proceed to the commit step.** Surface the conflict (both claims, both
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
   **not** write anything to any page and do **not** block. Note it for the step 13 summary
   so the user can act if they wish; the periodic `wiki-lint` sweep is the backstop.

### 12. Update all references to this file if it was modified

If the subject file was modified and not newly created, then it may have references to it in
existing wiki pages. Find all references to this file and check to see if they need to be updated.
In particular, if there are line number references, those may need to be updated to new line numbers
if that text has shifted because of the modification. 

### Common Mistakes

- **Appending chronological updates instead of editing in-place** — Wiki pages are living 
  documents, not journals. Do not add sections like `## April 27 update:` or `**Update:**` followed 
  by new content. Update the relevant section in-place, bump the `updated` frontmatter date, and 
  record what changed in the operation log (a commit on a git wiki). The log is the historical 
  record; pages are the current truth.
- **Skipping the backlink audit (step 10)** — A wiki's value compounds through bidirectional links. 
  Always scan existing pages for entities this source introduces.
- **Inventing `[[slug]]` links** — Never write a cross-reference to a slug you have not confirmed 
  exists or are creating now. A link that resolves to nothing is a hallucinated link. Verify against 
  the existing page set (`ls wiki/pages/`); see the Concept Identity rule in `SCHEMA.md`.
- **Summarizing the abstract instead of synthesizing** — The Summary section should reflect your 
  own synthesis, not a rephrased abstract.

## Post Processing Steps

These steps are run after all of the Source Page Processing Steps have been completed for all files.

### 1. Regenerate `wiki/pages/index.md`

Do **not** hand-edit the index. Every page you wrote this update already carries the important 
fields in its frontmatter — that is the index's source of truth. Regenerate it:

```
okf index wiki/pages
```

If the generator warns about a page with no frontmatter or a page lands in `Uncategorized`, fix 
that page's frontmatter and rerun.

### 2. Update `wiki/overview.md`

Re-read the current overview (if it exists).

Create or update it as described in the SCHEMA.md doc. 

### 3. Record the operation

**Gate first:** do not suggest a commit while any page touched this update still carries a
`contradiction-check: failed` line (step 11). Resolve the blocking contradiction and remove
the line first — committed pages are always clean.

Per SCHEMA's **Operation Log & Commit Convention**:
stage the wiki changes and suggest a commit (subject follows the repo's convention — default
Conventional Commits `docs:` for an update — plus the trailer).
```
docs: summarize <source title>

Wiki-Op: update
```

### 4. Commit

1. Save the most recent commit hash into wiki/last_update.yml. Replace the file if it already exists. Use this template:
``` yaml
commit_hash: <hash>
```

2. Commit the changes to the repo, and push those changes to origin if there is an origin remote configured.

### 5. Report to user

- Summary page: `wiki/pages/<slug>.md`
- Entity/concept pages created or updated: <list>
- Pages that received backlinks: <list>
- Index and overview updated
- Soft tensions noted (step 11): <list any non-blocking tensions, or "none"> — not recorded on any page; act on them if you want

