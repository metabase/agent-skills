---
name: metabase-representation-format
description: Understands the Metabase Representation Format — a YAML-based serialization format for Metabase content (collections, cards, dashboards, documents, segments, measures, snippets, transforms). Use when the user needs to create, edit, understand, or validate Metabase representation YAML files, or when working with Metabase serialization/deserialization (serdes). Covers entity schemas, MBQL and native queries, visualization settings, parameters, and folder structure.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## What is the Metabase Representation Format

Metabase represents user-created content as a tree of YAML files. Each file is one entity (a collection, card, dashboard, etc.). The format is **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

The full specification is in `spec.md` in this skill folder. Always Read it before creating or editing representation YAML files. The spec covers entity keys, folder structure, MBQL queries, native queries, visualization settings, click behaviors, parameters, and all entity types with examples.

## Entities

The format defines 11 entity types. Each entity has a YAML JSON Schema in the `schemas/` folder.

| Entity | SerDes Model | Schema File | Description |
|--------|-------------|-------------|-------------|
| **Collection** | `Collection` | `schemas/collection.yaml` | Folder-like container for organizing content. Hierarchy via `parent_id`. Namespaces: `null` (main), `"snippets"`, `"transforms"`. |
| **Card** | `Card` | `schemas/card.yaml` | Question, model, or metric. Holds an MBQL or native `dataset_query`. Display types: table, bar, line, pie, scalar, etc. Card types: `"question"`, `"model"`, `"metric"`. |
| **Dashboard** | `Dashboard` | `schemas/dashboard.yaml` | Grid layout (24 columns) of cards with filter parameters and optional tabs. Contains `dashcards` array for card placement and `parameters` array for filter controls. |
| **Document** | `Document` | `schemas/document.yaml` | Rich text page using ProseMirror AST. Can embed cards via `cardEmbed` nodes and link to entities via `smartLink` nodes. |
| **Segment** | `Segment` | `schemas/segment.yaml` | Saved filter definition scoped to a table. Definition must use `type: query` with only `source-table` and `filter` clauses. |
| **Measure** | `Measure` | `schemas/measure.yaml` | Saved aggregation definition scoped to a table. Definition must use `type: query` with only `source-table` and exactly one `aggregation` clause. |
| **Snippet** | `NativeQuerySnippet` | `schemas/snippet.yaml` | Reusable SQL fragment referenced in native queries via `{{snippet: Name}}`. |
| **Transform** | `Transform` | `schemas/transform.yaml` | Materializes query or Python script results into a database table. Source is either MBQL/native query or Python script. |
| **TransformTag** | `TransformTag` | `schemas/transform_tag.yaml` | Label for categorizing transforms. Built-in types: `"hourly"`, `"daily"`, `"weekly"`, `"monthly"`, or `null` for custom. |
| **TransformJob** | `TransformJob` | `schemas/transform_job.yaml` | Scheduled job (cron) that executes transforms matching specific tags. |
| **PythonLibrary** | `PythonLibrary` | `schemas/python_library.yaml` | Shared Python source file available to Python-based transforms. |

Common schemas referenced by entity schemas live in `schemas/common/`:
- `id.yaml` — entity_id (NanoID), user_id (email), database_id (name), table_id, field_id
- `query.yaml` — MBQL and native query structure with expression validation
- `ref.yaml` — field, expression, aggregation, metric, measure, segment references
- `parameter.yaml` — parameter definitions and targets
- `temporal_bucketing.yaml` — datetime bucketing and extraction units

## Entity Identification

Every entity has:
- **`entity_id`** — 21-character NanoID (alphabet: `A-Za-z0-9_-`). Stable across renames/moves. Unique per entity type.
- **`serdes/meta`** — Array encoding the identity path. Each entry has `id`, `model`, and optionally `label` (slugified name). The last entry's `model` field determines the entity type.

Generate a NanoID:
```bash
head -c 21 /dev/urandom | base64 | tr -dc 'A-Za-z0-9_-' | head -c 21
```

Foreign key references use human-readable names instead of numeric IDs:
- **Database FK**: database name string (e.g., `"Sample Database"`)
- **Table FK**: `[database, schema, table]` array (e.g., `["Sample Database", "PUBLIC", "ORDERS"]`)
- **Field FK**: `[database, schema, table, field, ...]` array (4+ elements for JSON paths)
- **Collection/Card/Dashboard FK**: entity_id (NanoID)
- **User FK**: email address

## Folder Structure

Metabase imports entities from these directories only:
- `collections/**/*.yaml` — cards, dashboards, documents, snippets, collections
- `databases/**/segments/**/*.yaml` — segment definitions
- `databases/**/measures/**/*.yaml` — measure definitions
- `python_libraries/**/*.yaml` (also `python-libraries/`) — Python library files
- `transforms/**/*.yaml` — transform jobs and tags

**Important**: directory structure is for readability only. The authoritative source for collection membership is each entity's `collection_id` field. Collections are organized by namespace: `main/` (regular content), `snippets/` (SQL snippets), `transforms/` (transform entities).

## Queries

**MBQL queries** (portable, built with graphical query editor):
- `source-table`: Table FK array or card entity_id string
- `filter`, `aggregation`, `breakout`, `order-by`, `limit`, `expressions`, `joins`
- Field references: `[field, Field-FK, options-or-null]`
- Expression references: `[expression, "Name"]`
- Aggregation references: `[aggregation, index]`

**Native queries** (raw SQL):
- `native.query`: SQL string with `{{template_tag}}` placeholders
- `native.template-tags`: map defining each tag's type, display name, and default
- Template tag types: `text`, `number`, `date`, `boolean`, `dimension`, `temporal-unit`, `card`, `snippet`, `table`

See spec.md sections "MBQL Query" and "Native Query" for full syntax.

## Schema Validation

Use `@metabase/representations` as a CLI tool to validate YAML files against the schemas:

```sh
npx @metabase/representations validate-schema --folder ./my-export
```

Omit `--folder` to validate the current directory. The tool:
1. Finds YAML files in the recognized import directories
2. Reads `serdes/meta` to determine the entity model
3. Validates against the corresponding JSON Schema
4. Reports OK/FAIL per file with error details
5. Exits with code 1 if any failures

## Key Rules

- Every entity YAML file must have a `serdes/meta` array with the correct `model` value
- `entity_id` must be a valid 21-character NanoID
- `collection_id` determines collection membership (not the file path)
- Cards with `dashboard_id` or `document_id` are nested under that container
- A card should never have both `dashboard_id` and `document_id` set
- Segment definitions: only `source-table` + `filter` (no aggregation, joins, expressions)
- Measure definitions: only `source-table` + exactly one `aggregation` (no filter, joins, expressions)
- Dashboard grid: 24 columns, `col + size_x <= 24`, cards cannot overlap
- Snippet `serdes/meta` uses model `NativeQuerySnippet` (not `Snippet`)
