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

## 2. Close current ticket if there is one

If a ticket was just implemented, then close it.

## 3. Update wiki

In a subagent with a clean context: Run the wiki-update skill.

If the child agent need clarification or a decision made that requires the users input, pass along
the question to the user, and they can tell you how to answer the child. 

