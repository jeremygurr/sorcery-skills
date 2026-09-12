---
name: sorcery-setup
description: "Configure this repo for the sorcery skills: set up rules for analyzing this repo using the wiki first. Run once before first use of the other sorcery skills."
disable-model-invocation: true
---

# Sourcery Setup

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm 
with the user, then write.

In *clean* mode (sorcery-setup clean), the following folders must be deleted before proceeding with
this setup:
  - wiki/bin

## Process

### 1. Check for incomplete or outdated installation of sorcery skills

If an older copy of this skill — the setup-wizard-skills folder or the wizard-setup folder —
exists in ~/.pi/agent/skills, tell the user that this skill has been renamed to sorcery-setup and
the old folder or link should be removed. 

They may use the link_pi_skills function from the README.md file to relink the skills:

They just need to run it against their sourcery-skills/skills folder: 
  `link_pi_skills sourcery-skills/skills`

Help them if needed. 

If any of these skills/folders are missing from ~/.pi/agent/skills:
- approved
- wiki-audit
- wiki-lint
- wiki-merge
- wiki-update

Then: Tell the user they need to link the skills from the sorcery repo to this folder. Assist
them if necessary.

### 2. Verify prerequisites

Verify that the user has the `okf` command in their path. If not, tell them that they must install
okf before you can proceed with this setup. 

Ways to install okf:
1. If they have a mac: `brew install --cask okfcli/okf/okf`
2. `go install github.com/okfcli/okf/cmd/okf@latest`
3. Build from source: `git clone https://github.com/okfcli/okf.git && cd okf && make build`

Guide them through getting okf installed if needed, but don't move forward until it is successfully installed.

If they don't have `zg` installed, suggest that they install it to speed up these skills.
If they don't have `rg` installed, suggest that they install it to speed up these skills.

### 3. Modify AGENTS file

Look inside of the AGENTS.md file at the root of this repo. 

If an `# Navigating this Repo` block already exists in the that file, update its contents in-place 
rather than appending a duplicate. Don't overwrite user edits to the surrounding sections.

The block:

```markdown
# Navigating this Repo

This repo consists of two sections: the wiki, and the source material. The wiki section is purely 
generated from the source material. The wiki section is found in the wiki/pages folder at the root of 
this repo. The source material consists of all other files outside of the wiki/ folder in this repo. 

When searching for information from this repo, unless a specific file was referenced in the query, 
and unless you are executing a wiki modification operation, use the wiki to find the relevant files:

## Wiki Search Process

1. Read `wiki/pages/index.md` first

Scan the full index to identify which pages are likely relevant. Do NOT answer from
general knowledge — the wiki is the source of truth here, even if you think you know the
answer.

2. Read relevant pages

Read the identified pages in full. Follow one level of cross-reference links (matched via the 
Parsing references in wiki pages rule) if they point to pages that seem relevant to the question.

3. Read the relevant source documents mentioned in the wiki pages you read

4. Synthesize the answer

Write a response that is grounded in the source materials you read. Trust the source materials above
the wiki. The wiki is only there to guide you to the source materials.

## Other Searches

You do NOT need to do any additional searching beyond this unless the user explicitly says to. You
don't need to try and grep the entire repo to see what the wiki might have missed. 
```

Also add this block to the AGENTS.md file, but only if the Subagent Settings
section is not already there:

```markdown
# Subagent Settings

Maximum number of subagents at one time is 1, unless the user otherwise specifies. This adjusts max
concurrency accordingly. 
```

Also add this block, the same way — only if a Managing Documentation section is not already there:

```markdown
# Managing Documentation

Whenever creating or editing documentation, in either html or markdown, make sure to always use
links when referring to related files in this repo. If a concept is discussed in the documentation
that is implemented elsewhere in the repo, make links to those related files or folders. Use line
numbers in the links where appropriate (example ../src/Main.java#L14-17). 

When reading over documentation that is missing good links, or has invalid links, suggest fixing it. 

If the user ever asks about or wants to change a file in the wiki folder (or any of its subfolders),
then first read the wiki/WIKI-SCHEMA.md file for instructions about the wiki conventions. Then make
the requested changes according to those conventions.
```

### 4. Create directory structure

Create these directories at the repo root if they don't exist:

- wiki
- wiki/assets
- wiki/bin
- wiki/config
- wiki/pages
- wiki/reports

**Critical:** `wiki/pages/` is flat. All pages live here as `<slug>.md`. No subdirectories. Slugs are lowercase, hyphen-separated.

### 5. Copy assets

- Copy this skill's `assets/WIKI-SCHEMA.md` to `<repo-root>/wiki/WIKI-SCHEMA.md`.
- Copy this skill's `assets/bin/*` to `<repo-root>/wiki/bin/`.

For all of these file copies, replace any existing files and don't ask for verification, just do it.

### 6. Commit and push

1. Commit the changes. Don't ask for verification.
2. If a remote named origin exists, push to it.

### 7. Done

Tell the user: "Run this skill again if there is a change in the sorcery repo".

