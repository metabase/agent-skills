---
tags: [skill-creator]
max_turns: 80
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

before we migrate models 7106 (Access Requests) and 6389 (Simple Team Roster (Employee)) off of models on profile `prod`: what exactly happens to their bookmarks, the dashboards they're on, alerts, subscriptions, action buttons, filters that use them, and people's access once we swap everything to tables and archive them? give me the concrete list for these two and what you'd do about each item. read-only please, don't change anything.
