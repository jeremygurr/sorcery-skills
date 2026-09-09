---
name: approved
description: Use after tickets have been implemented, but changes haven't been committed and the
  ticket hasn't been closed yet.
disable-model-invocation: true
---

# Approved

This means the user has approved the current changes in this repo, and is ready for a commit.

# Process

## 1. Commit and Push Changes

Commit the changes related to the ticket just implemented.
Push the changes if an origin remote is defined. 

## 2. Update wiki

Run the wiki-update skill. After it completes successfully and is committed, push it if a remote
origin exists. 


