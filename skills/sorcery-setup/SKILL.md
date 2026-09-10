---
name: sorcery-setup
description: "Configure this repo for the sorcery skills: set up rules for analyzing this repo using the wiki first. Run once before first use of the other sorcery skills."
disable-model-invocation: true
---

# Sourcery Setup

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm 
with the user, then write.

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

Also add this block to the AGENTS.md file, but only if the Subagent Settings
section is not already there:

```markdown
# Subagent Settings

Maximum number of subagents at one time is 1, unless the user otherwise specifies. This adjusts max concurrency accordingly. 
```

Also add this block, the same way — only if a Wiki Gates section is not already there:

```markdown
# Wiki Gates

`wiki/bin/hooks/pre-commit` gates every commit in this repo. It blocks a staged page that carries
an unresolved contradiction flag, a structural problem (missing frontmatter, a broken link, a slug
collision), or a link defect (an unresolvable source-path target, a `#L` range that runs past the
end of the file, a malformed `[[slug]]`). All three checks are deterministic, no LLM.

The hooks are version-controlled but git only uses them when this clone's local config points at
them — `core.hooksPath` is local config and is NOT version-controlled, so run this once per clone:

    sh wiki/bin/hooks/install.sh      # sets git config core.hooksPath wiki/bin/hooks

This fails silently if skipped: git falls back to `.git/hooks` and no gate fires.
`git commit --no-verify` bypasses the gate for an intentionally dirty commit.
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

Copy this skill's `assets/WIKI-SCHEMA.md` to `<repo-root>/wiki/WIKI-SCHEMA.md`, replacing any pre-existing
files. Don't ask for verification, just do it.
Copy this skill's `assets/bin/*` to `<repo-root>/wiki/bin/`, replacing any pre-existing files. This
includes `assets/bin/hooks/`, which lands at `<repo-root>/wiki/bin/hooks/`. Don't ask for
verification, just do it.
Make sure `wiki/bin/hooks/pre-commit` and `wiki/bin/hooks/install.sh` are executable (`chmod +x`).

### 6. Enable the git hooks

The hooks are version-controlled, but git only uses them when this clone's local config points at
them — `core.hooksPath` lives in `.git/config`, which is not version-controlled. Run the installer:

    sh wiki/bin/hooks/install.sh

Then verify: `git hook run pre-commit`. Don't skip this: without it git falls back to `.git/hooks`,
the wiki gates never fire, and nothing warns you.

### 7. Commit and push

1. Commit the changes. Don't ask for verification.
2. If a remote named origin exists, push to it.

### 8. Done

Tell the user: "Run this skill again if there is a change in the sorcery repo".

