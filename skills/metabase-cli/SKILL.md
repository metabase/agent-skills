---
name: metabase-cli
description: Drive a Metabase instance from the terminal via the `mb` CLI. Authenticate with named profiles; inspect databases (list, get, full metadata rollup, schemas, tables in a schema) and trigger manual schema sync / field-values rescan; inspect tables, fields; list/get/create/update/archive cards (questions, models, metrics) and run them as JSON/CSV/XLSX; list/get/create/update dashboards and patch dashcards; list/get/create collections and traverse the hierarchy by id, entity_id, or "root"/"trash" (with items and recursive tree); list/get/create/update/archive native query snippets, segments, and measures; author/update/run transforms and schedule transform-jobs; read/update settings; search content (cards, dashboards, collections, transforms, metrics); manage Enterprise workspaces; git-sync to/from a git remote (status, dirty, import, export, branches, stash, add/remove a collection from sync). Use whenever the user wants to interact with a Metabase from the terminal — "log into metabase", "what profiles do I have", "list cards", "run card 42 as CSV", "create a transform", "list dashboards", "move a dashcard", "list collections", "what's in collection 4", "show the collection tree", "list snippets", "create a segment", "archive a measure", "search metabase for X", "spin up a workspace", "import the latest changes", "add a directory to git sync", "set a setting", "what schemas are in this database", "trigger a sync", "rescan field values", or anything hitting `mb <verb>`.
allowed-tools: Bash(mb:*), Read, Write, Edit, AskUserQuestion
---

# metabase-cli

Load the workflow content from the CLI:

```bash
mb skills get core      # start here — auth, flag conventions, every command group
mb skills list          # enumerate specialized skills bundled with this CLI version
mb skills get <name>    # load a specialized skill (workspace, transform, git-sync, …)
```

Don't drive Metabase by `curl`ing `/api/...` directly — the CLI handles auth profiles, retries, schema validation, and credential redaction.
