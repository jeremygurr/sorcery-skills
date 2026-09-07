---
name: setup-wizard-skills
description: "Configure this repo for the wizard skills: set up rules for analyzing this repo using the wiki first. Run once before first use of the other wizard skills."
disable-model-invocation: true
---

# Setup Wizard Skills

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm 
with the user, then write.

## Process

### 0. Verify prerequisites

Verify that the user has the `okf` command in their path. If not, tell them that they must install
okf before you can proceed with this setup. They can install it through brew, if they are running a 
mac: `brew install --cask okfcli/okf/okf` or from the github repo: `https://github.com/okfcli/okf`. 
Guide them through installed it if needed, but don't move forward until it is successfully installed.

### 1. Modify AGENTS file

Look inside of the AGENTS.md file at the root of this repo. 

If an `# Navigating this Repo` block already exists in the that file, update its contents in-place 
rather than appending a duplicate. Don't overwrite user edits to the surrounding sections.

The block:

```markdown
# Navigating this Repo

This repo consists of two sections: the wiki, and the source material. The wiki section is purely 
generated from the source material. The wiki section is found in the wiki folder at the root of 
this repo. The source material consists of all other files in this repo. 

When searching for information from this repo, unless a specific file was referenced in the query, 
and unless you are executing a wiki modification operation, use the wiki to find the relevant files:

1. Read `wiki/pages/index.md` first

Scan the full index to identify which pages are likely relevant. Do NOT answer from
general knowledge — the wiki is the source of truth here, even if you think you know the
answer.

2. Read relevant pages

Read the identified pages in full. Follow one level of cross-reference links (matched via the 
Parsing references in wiki pages rule) if they point to pages that seem relevant to the question.

3. Synthesize the answer

Write a response that is grounded in the wiki pages you read.
```

In the same way, add/replace the following block in the AGENTS.md file:

```markdown
# Subagent settings

- Maximum number of subagents at one time is 3. This adjusts max concurrency accordingly. 
```

### 2. Create directory structure

Create these directories at the repo root if they don't exist:

- wiki
- wiki/assets
- wiki/bin
- wiki/config
- wiki/pages

**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.

### 3. Copy assets

copy this skill's `assets/SCHEMA.md` to `<repo-root>/wiki/SCHEMA.md`.
copy this skill's `assets/bin/*` to `<repo-root>/wiki/bin/`.

### 4. Commit and push

1. Commit the changes.
2. If a remote named origin exists, push to it.

### 5. Done

Tell the user the setup is complete and that they should not need to run this skill again on this repo.

