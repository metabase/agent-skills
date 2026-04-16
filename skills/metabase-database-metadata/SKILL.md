---
name: metabase-database-metadata
description: Understands the Metabase Database Metadata Format — a YAML-based on-disk representation of databases, tables, and fields synced from a Metabase instance. Use when the user needs to read, edit, or understand metadata files produced by `@metabase/database-metadata`, or when reasoning about a project's schema (columns, types, FK relationships) through the `.metabase/databases` folder.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Metabase Database Metadata Format

Metabase represents database metadata — synced databases, their tables, and their fields — as a tree of YAML files. Files are **diff-friendly**: numeric IDs are omitted entirely, and foreign keys use natural-key tuples like `["Sample Database", "PUBLIC", "ORDERS"]` instead of database identifiers.

The format is defined by a specification hosted at [metabase/database-metadata](https://github.com/metabase/database-metadata) (see [`core-spec/v1/spec.md`](https://github.com/metabase/database-metadata/blob/main/core-spec/v1/spec.md)). The spec is the canonical reference — extract it on demand and read it before making non-trivial edits. The same repository also ships a CLI (`@metabase/database-metadata` on npm) that converts the raw JSON from `GET /api/database/metadata` into the YAML tree described by the spec.

## Conventions

By convention, metadata lives under `.metabase/` at the project root. **Assume it is already extracted**: a sync job refreshes it on a schedule or before the agent runs. The agent should read the tree, not refetch it.

- **`.metabase/databases/`** — the YAML tree. **This is the canonical source for the agent.** Read these files to understand the schema, columns, types, and FK relationships.
- **`.metabase/metadata.json`** — the raw API response. A single multi-megabyte JSON file with flat `databases` / `tables` / `fields` arrays. **Ignore this file.** It only exists so the CLI can regenerate the tree. Do not open it, grep it, or pass it to other tools — it will blow up the context for no benefit over the YAML.

**Do not run `GET /api/database/metadata` or `npx @metabase/database-metadata extract-metadata` unless the user explicitly asks to refresh the metadata.** The tree may be slightly stale, but that is the user's or CI's responsibility to refresh — not the agent's. If something seems out of date, mention it to the user rather than refetching silently.

## Entities

Three entity types, two file types:

| Entity | File | Description |
|--------|------|-------------|
| **Database** | `.metabase/databases/{db}/{db}.yaml` | A connected data source (Postgres, MySQL, BigQuery, etc.). Identified by name. |
| **Table** | `.metabase/databases/{db}/schemas/{schema}/tables/{table}.yaml` (or `.../tables/{table}.yaml` for schemaless DBs) | A physical table or view. Contains a `fields` array with all its columns nested inline. |
| **Field** | (nested inside a Table YAML, no separate file) | A column. Includes `base_type`, `database_type`, and optionally `effective_type`, `semantic_type`, `coercion_strategy`, `parent_id`, `fk_target_field_id`. |

## Foreign keys

Foreign keys use natural-key tuples, not numeric IDs:

- **Database FK**: the database name (string) — e.g. `"Sample Database"`
- **Table FK**: `[database, schema_or_null, table]` — e.g. `["Sample Database", "PUBLIC", "ORDERS"]`
- **Field FK**: `[database, schema_or_null, table, field, ...nested_field_names]` — e.g. `["Sample Database", "PUBLIC", "EVENTS", "DATA", "user", "name"]` for a JSON-unfolded column `DATA.user.name`

Field-level FKs show up as `parent_id` (nested field parent) and `fk_target_field_id` (referenced PK for FK columns).

## Type attributes on fields

- **`database_type`** — the raw native type string from the driver (`BIGINT`, `VARCHAR`, `JSONB`, etc.). Database-specific.
- **`base_type`** — the Metabase type matching the native type (`type/BigInteger`, `type/Text`, `type/Structured`, etc.).
- **`effective_type`** — the type Metabase treats the column as at query time. Only emitted when it differs from `base_type` (i.e. coercion is configured).
- **`coercion_strategy`** — the rule producing `effective_type` from `base_type` (e.g. `Coercion/ISO8601->DateTime`, `Coercion/UNIXMilliSeconds->DateTime`).
- **`semantic_type`** — business-domain label (`type/PK`, `type/FK`, `type/Email`, `type/Category`, `type/Latitude`, etc.). Drives UI and some analytical behavior.

See the extracted spec for the full type hierarchy and available coercion strategies.

## Extracting the spec

Extract the full spec to a file:

```sh
npx @metabase/database-metadata extract-spec --file <path>
```

Extract it to a temp location at the start of a session and reference it as needed — e.g. `mktemp -d` then point `--file` inside it.

## Refreshing the tree (user-initiated only)

The agent should not refresh metadata on its own. If the user explicitly asks for it, the pipeline is:

```sh
# 1. Refetch the JSON from a running Metabase
curl -sf "$METABASE_URL/api/database/metadata" \
  -H "X-API-Key: $METABASE_API_KEY" \
  -o .metabase/metadata.json

# 2. Rebuild the YAML tree
rm -rf .metabase/databases
npx @metabase/database-metadata extract-metadata .metabase/metadata.json .metabase/databases
```

Typically this is wired up in CI so the tree stays in sync automatically — the agent does not need to run it.
