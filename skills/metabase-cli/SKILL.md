---
name: metabase-cli
description: >
  Drive a Metabase instance from the terminal via the `mb` CLI: auth profiles, databases and schemas, schema sync and field-values rescan, tables, fields, cards (questions, models, metrics) run as JSON/CSV/XLSX, dashboards and dashcards, collections and their tree, snippets, segments, measures, transforms and transform-jobs, settings, search, git-sync. Use for any Metabase operation from the terminal: "log into metabase", "what profiles do I have", "list cards", "run card 42 as CSV", "create a transform", "list dashboards", "move a dashcard", "list collections", "what's in collection 4", "show the collection tree", "list snippets", "create a segment", "archive a measure", "search metabase for X", "import the latest changes", "add a directory to git sync", "set a setting", "what schemas are in this database", "trigger a sync", "rescan field values", or any `mb <verb>`. Whole data jobs go to `rde`.
allowed-tools: Bash(mb:*), Read, Write, Edit
---

# metabase-cli

Load the workflow content from the CLI:

```bash
mb skills get core      # start here — auth, flag conventions, every command group
mb skills list          # enumerate specialized skills bundled with this CLI version
mb skills get <name>    # load a specialized skill (transform, semantic-layer, dashboard, git-sync, …)
```

Command groups, in full: authenticate with named profiles; inspect databases (list, get, full metadata rollup, schemas, tables in a schema) and trigger a manual schema sync or field-values rescan; inspect tables and fields; list/get/create/update/archive cards (questions, models, metrics) and run them as JSON/CSV/XLSX; list/get/create/update dashboards and patch dashcards; list/get/create collections and traverse the hierarchy by id, entity_id, or "root"/"trash" (with items and recursive tree); list/get/create/update/archive native query snippets, segments, and measures; author/update/run transforms and schedule transform-jobs; read/update settings; search content (cards, dashboards, collections, transforms, metrics); git-sync to/from a git remote (status, dirty, import, export, branches, stash, add/remove a collection from sync).

Don't drive Metabase by `curl`ing `/api/...` directly — the CLI handles auth profiles, retries, schema validation, and credential redaction.

**Doing a whole job, not one command?** Higher-level data-engineering workflows — raw data to clean tables, the semantic layer, dashboards — live in the `rde` skill, which drives this CLI:

```bash
npx skills add metabase/agent-skills --skill rde
```

When it is installed, follow it; it loads the bundled skills it needs.
