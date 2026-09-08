---
name: approved
description: Use after tickets have been implemented, but changes haven't been committed and the
  ticket hasn't been closed yet.
disable-model-invocation: true
---

# Process

## 1. Load the SCHEMA

If: wiki/SCHEMA.md doesn't exist
Then: Tell the user they need to run the setup-wizard-skills skill first, and abort this skill.
Else: read the wiki/SCHEMA.md file if it hasn't been read already. 

## 2. Commit and Push Changes

Commit the changes related to the ticket just implemented.
Push the changes if an origin remote is defined. 

## 3. Update wiki

Run the /wiki-update skill. After it completes successfully and is committed, push it if a remote
origin exists. 


