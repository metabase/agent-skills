---
name: metabase-database-metadata
description: Understands the Metabase Database Metadata Format — a YAML-based on-disk representation of databases, tables, and fields synced from a Metabase instance. Use when the user needs to read, edit, or understand metadata files produced by `@metabase/database-metadata`, or when reasoning about a project's schema (columns, types, FK relationships) through the `.metadata/databases` folder.
model: opus
allowed-tools: Read, Edit, Glob, Grep, Bash, AskUserQuestion
---

## Metabase Database Metadata Format

Metabase represents database metadata — synced databases, their tables, and their fields — as a tree of YAML files. Files are **diff-friendly**: numeric IDs are omitted entirely, and foreign keys use natural-key tuples like `["Sample Database", "PUBLIC", "ORDERS"]` instead of database identifiers.

The format is defined by a specification bundled alongside this file as `spec.md` (upstream source: [metabase/database-metadata](https://github.com/metabase/database-metadata)). The same project ships a CLI (`@metabase/database-metadata` on npm) that converts the raw JSON downloaded from a Metabase workspace page into the YAML tree described by the spec.

## Canonical layout

All metadata for a project lives under a top-level `.metadata/` directory:

- **`.metadata/databases/`** — the YAML tree. **This is the canonical source for the agent.** Read these files to understand the schema, columns, types, and FK relationships.
- **`.metadata/table_metadata.json`** — the raw JSON downloaded from the Metabase workspace page. Potentially multi-megabyte (or multi-gigabyte) JSON with flat `databases` / `tables` / `fields` arrays. **Never open, grep, or pass it to tools.** It exists only as input to the extractor.
- **`.metadata/field_values.json`** — sampled distinct values per field, also downloaded from the Metabase workspace page. Optional but recommended; produces small per-field YAML files inside the tree (one per low-cardinality field) that the agent reads when it needs example values or filter vocabularies.

The `.metadata/` directory should be gitignored. On large warehouses the extracted metadata can reach gigabytes — committing it would make the repo painful or unusable.

## First-time setup

Do not run any of the steps below proactively at session start. Only run them when the user **explicitly asks** to fetch metadata, set up the workflow, or requests something that plainly requires knowledge of the database schema (e.g. "write a query against ORDERS", "describe what tables exist").

When setup is triggered:

### 1. Ensure `.metadata/` is gitignored

Read the repo's `.gitignore` and confirm `.metadata/` is listed. If it isn't, **ask the user before modifying `.gitignore`** — e.g.:

> `.metadata/` is not in `.gitignore`. Committing it would bloat the repo (metadata can be gigabytes). Shall I add it?

Only edit `.gitignore` after the user confirms.

### 2. Obtain the metadata files

Ask the user to download both files from the Metabase workspace page (Workspaces → the relevant workspace → "Download table_metadata.json" / "Download field_values.json") and place them at `.metadata/table_metadata.json` and `.metadata/field_values.json`. `field_values.json` is optional — skip it if the user doesn't need example values per field — but `table_metadata.json` is required.

Do not try to fetch them via API — there is no agent-runnable endpoint for these; the workspace page is the only source.

### 3. Extract

Once `.metadata/table_metadata.json` (and optionally `.metadata/field_values.json`) is in place:

```sh
mkdir -p .metadata
rm -rf .metadata/databases
npx @metabase/database-metadata extract-table-metadata .metadata/table_metadata.json .metadata/databases
# Only when field_values.json is present:
npx @metabase/database-metadata extract-field-values .metadata/table_metadata.json .metadata/field_values.json .metadata/databases
```

Then read the YAML tree under `.metadata/databases/` to answer the user's question.

## Session start behaviour

At the start of a session, do not run any fetch commands. Just observe what's on disk:

- If `.metadata/table_metadata.json` **and** `.metadata/databases/` both exist, **assume the tree is sufficiently up to date** and use it directly. Do not refetch.
- If the tree is missing or only partial, do nothing until the user asks for something that needs it — then fall into the first-time-setup flow above.

If something in the tree looks stale or inconsistent while you're using it, mention it to the user and let them decide whether to refetch. Never refresh silently.

## Refreshing (user-initiated only)

If the user explicitly asks to refresh metadata, ask them to re-download `table_metadata.json` (and `field_values.json` if they were using it) from the Metabase workspace page, then re-run the extract step. Always remove `.metadata/databases` before re-extracting so stale files are not left behind.

## Entities

Three entity types, two file types:

| Entity | File | Description |
|--------|------|-------------|
| **Database** | `.metadata/databases/{db}/{db}.yaml` | A connected data source (Postgres, MySQL, BigQuery, etc.). Identified by name. |
| **Table** | `.metadata/databases/{db}/schemas/{schema}/tables/{table}.yaml` (or `.../tables/{table}.yaml` for schemaless DBs) | A physical table or view. Contains a `fields` array with all its columns nested inline. |
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

## Reading the spec

This skill ships with a local snapshot of the spec as `spec.md`, alongside `SKILL.md`.

**Read it on demand, not eagerly.** Open `spec.md` only when you actually need detail beyond what `SKILL.md` summarizes — e.g. the full base-type / semantic-type hierarchy, the complete list of coercion strategies, or the exact folder-path rules. Do not open it at session start, and do not open it for tasks unrelated to the metadata tree.

If the bundled copy looks out of date with the upstream package, the skill's own `README.md` documents how to refresh it with `extract-spec`.
