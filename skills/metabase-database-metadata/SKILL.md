---
name: metabase-database-metadata
description: Retrieves and caches database metadata (databases, tables, fields, field values) from a Metabase instance. Use when you need to understand the data model available in a Metabase instance — for example, before writing queries, building dashboards, or creating cards that reference specific tables and fields.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion, WebFetch
---

## What this skill does

Fetches database metadata from a Metabase instance via the serialization export API. The export includes all databases, tables, fields, and field values — everything needed to understand the data model.

## Prerequisites

You need:
- The **URL** of the Metabase instance (e.g., `https://my-company.metabaseapp.com`)
- An **API key** with **Administrator** permissions

## How to retrieve metadata

Before fetching, ask the user:

1. **Where to store the metadata?** Default is `.metadata_cache` in the working directory. The user can specify a different folder path.
2. **Add the folder to `.gitignore`?** Default is **yes**. If the working directory is a git repo, add the folder to `.gitignore` unless the user declines.
3. **Provide the URL and API key directly** so you can make the call, or **get a script command** to run themselves?

### Option 1: Direct call

Make a POST request:

```
POST {METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata
```

Headers:
- `x-api-key: {API_KEY}`

The `dirname=metadata` parameter controls the name of the root folder inside the archive (defaults to `<instance-name>-<YYYY-MM-dd_HH-mm>` otherwise). Using a fixed name makes extraction predictable.

The response is a `.tar.gz` archive. **The download may take several minutes** depending on the size of the instance.

### Option 2: Script for the user

There is a ready-made script at `scripts/fetch-metadata.py` in this skill folder. Tell the user to run it with their URL and API key as arguments:

```
! python3 <path-to-skill>/scripts/fetch-metadata.py <METABASE_URL> <API_KEY> .metadata_cache
```

The script downloads the export, extracts it into the specified folder, keeps only the `databases/` directory (discarding `collections/`, `transforms/`, `settings.yaml`, etc.), and cleans up the archive. Using a script avoids line-wrapping issues that break long cURL commands when pasted inline. It uses only Python standard library modules so it works on macOS, Linux, and Windows without extra dependencies.

## Storing the metadata

Database metadata represents a point-in-time snapshot of the data model. It can change as databases evolve. Treat it as a **cache**, not a source of truth.

If the user agreed to add the folder to `.gitignore` (the default), append the folder path to `.gitignore` in the working directory.

## Using the metadata

Once cached, the metadata is available at `<folder>/databases/` (e.g. `.metadata_cache/databases/`). Each database folder contains YAML files describing tables, fields, field values, and relationships. Read these files to understand:

- Which databases are connected
- What tables exist in each database and schema
- What fields each table has, including types and semantic types
- What values categorical fields contain (field values)

This information is essential when writing MBQL or native queries, building dashboards, or creating any Metabase content that references the data model.

## Refreshing the cache

The cache can become stale. Re-run the export to refresh it. If the user reports that a table or field is missing, suggest refreshing the cache first.
