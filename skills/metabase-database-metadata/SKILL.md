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

Ask the user whether they'd like to:

1. **Provide the URL and API key directly** so you can make the call, or
2. **Get a cURL command** with placeholders to run themselves

### Option 1: Direct call

Make a POST request:

```
POST {METABASE_URL}/api/ee/serialization/export?all_collections=false&field_values=true&dirname=metadata
```

Headers:
- `x-api-key: {API_KEY}`

The `dirname=metadata` parameter controls the name of the root folder inside the archive (defaults to `<instance-name>-<YYYY-MM-dd_HH-mm>` otherwise). Using a fixed name makes extraction predictable.

The response is a `.tar.gz` archive.

### Option 2: Script for the user

There is a ready-made script at `scripts/fetch-metadata.sh` in this skill folder. Tell the user to run it with their URL and API key as arguments:

```
! bash <path-to-skill>/scripts/fetch-metadata.sh <METABASE_URL> <API_KEY>
```

The script downloads `metabase-export.tar.gz` into the current working directory. Using a script avoids line-wrapping issues that break long cURL commands when pasted inline.

## Storing the metadata

Database metadata represents a point-in-time snapshot of the data model. It can change as databases evolve. Treat it as a **cache**, not a source of truth.

1. Create a `.metadata_cache` folder in the working directory
2. Extract the archive contents into `.metadata_cache`
3. If the working directory is a git repo, add `.metadata_cache` to `.gitignore`

```bash
mkdir -p .metadata_cache
tar -xzf metabase-export.tar.gz --strip-components=1 -C .metadata_cache
# Only keep the databases folder — discard everything else
find .metadata_cache -mindepth 1 -maxdepth 1 ! -name databases -exec rm -rf {} +
rm -rf .metadata_cache/databases/internal_metabase_database
rm metabase-export.tar.gz
```

Only the `databases/` folder is relevant — the archive also includes `collections/`, `transforms/`, `settings.yaml`, etc., which should be discarded. The `internal_metabase_database` is Metabase's internal storage and should also be removed.

## Using the metadata

Once cached, the metadata is available at `.metadata_cache/databases/`. Each database folder contains YAML files describing tables, fields, field values, and relationships. Read these files to understand:

- Which databases are connected
- What tables exist in each database and schema
- What fields each table has, including types and semantic types
- What values categorical fields contain (field values)

This information is essential when writing MBQL or native queries, building dashboards, or creating any Metabase content that references the data model.

## Refreshing the cache

The cache can become stale. Re-run the export to refresh it. If the user reports that a table or field is missing, suggest refreshing the cache first.
