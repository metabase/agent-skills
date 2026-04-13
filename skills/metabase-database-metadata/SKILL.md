---
name: metabase-database-metadata
description: Retrieves and caches database metadata (databases, tables, fields, field values) from a Metabase instance. Use when you need to understand the data model available in a Metabase instance — for example, before writing queries, building dashboards, or creating cards that reference specific tables and fields.
model: opus
allowed-tools: Read, Glob, Grep
---

## What this skill does

Fetches database metadata from a Metabase instance via the serialization export API. The export includes all databases, tables, fields, and field values — everything needed to understand the data model.

## Prerequisites

You need:
- The **URL** of the Metabase instance (e.g., `https://my-company.metabaseapp.com`)
- An **API key** with **Administrator** permissions

## How to retrieve metadata

Ask the user to run the `fetch-metadata.sh` script in this skill's folder, passing the Metabase URL and API key as arguments:

```bash
fetch-metadata.sh <url> <api-key>
```

Do **not** run the script yourself — the user provides their credentials directly to it.

The metadata will be written to `metadata/databases` in the working directory. The download may take several minutes depending on the size of the instance.

## Storing the metadata

Database metadata represents a point-in-time snapshot of the data model. It can change as databases evolve. Treat it as a **cache**, not a source of truth.

## Using the metadata

Once cached, the metadata is available at `metadata/databases/`. Each database folder contains YAML files describing tables, fields, field values, and relationships. Read these files to understand:

- Which databases are connected
- What tables exist in each database and schema
- What fields each table has, including types and semantic types
- What values categorical fields contain (field values)

This information is essential when writing MBQL or native queries, building dashboards, or creating any Metabase content that references the data model.

## Refreshing the cache

The cache can become stale. Re-run the script to refresh it. If the user reports that a table or field is missing, suggest refreshing the cache first.
