---
name: metabase-cli
description: Drive a Metabase instance from the terminal via the `mb` CLI. Authenticate with named profiles; inspect databases, schemas, tables, and fields and trigger a sync or field-values rescan; list/get/create/update/archive cards (questions, models, metrics), dashboards and dashcards, collections and their tree, snippets, segments, and measures; run cards as JSON/CSV/XLSX; author, run, and schedule transforms; read/update settings; search content; git-sync collections to and from a remote. Use whenever the user wants a Metabase operation from the terminal — "log into metabase", "run card 42 as CSV", "move a dashcard", "what's in collection 4", "create a transform", "search metabase for X", "what schemas are in this database", "import the latest changes", or anything hitting `mb <verb>`. For a whole data job (raw data to clean tables, a semantic layer, dashboards, reconciling numbers) use `rde`.
allowed-tools: Bash(mb:*), Read, Write, Edit, AskUserQuestion
---

# metabase-cli

Load the workflow content from the CLI:

```bash
mb skills get core      # start here — auth, flag conventions, every command group
mb skills list          # enumerate specialized skills bundled with this CLI version
mb skills get <name>    # load a specialized skill (transform, semantic-layer, dashboard, git-sync, …)
```

Don't drive Metabase by `curl`ing `/api/...` directly — the CLI handles auth profiles, retries, schema validation, and credential redaction.

**Doing a whole job, not one command?** Higher-level data-engineering workflows — raw data to clean tables, the semantic layer, dashboards — live in the `rde` skill, which drives this CLI:

```bash
npx skills add metabase/agent-skills --skill rde
```

When it is installed, follow it; it loads the bundled skills it needs.
