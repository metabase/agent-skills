---
tags: [skill-creator]
max_turns: 120
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

we're finally killing models on our metabase. the `mb` profile `prod` is our production instance, it's remote-synced read-only from the git repo in the current directory. can you go through every model, figure out which ones are just 1:1 wrappers of a table and which ones need a transform, and write me the migration plan + the list of things you need me to decide? don't change anything yet, neither in metabase nor in git — this is just the plan.
