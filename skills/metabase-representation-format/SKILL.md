---
name: metabase-representation-format
description: Understands the Metabase Representation Format — a YAML-based serialization format for Metabase content (collections, cards, dashboards, documents, segments, measures, snippets, transforms). Use when the user needs to create, edit, understand, or validate Metabase representation YAML files, or when working with Metabase serialization/deserialization (serdes). Covers entity schemas, MBQL and native queries, visualization settings, parameters, and folder structure.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Metabase Representation Format

Metabase represents user-created content as a tree of YAML files. Each file is one entity (a collection, card, dashboard, etc.). The format is **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

The format is defined by a spec and a set of JSON Schemas, both shipped with the `@metabase/representations` npm package. Extract them on demand (see below) rather than copying them into the repo.

## Entities

The format defines 11 entity types. Each entity has a YAML JSON Schema.

| Entity | SerDes Model | Schema File | Description |
|--------|-------------|-------------|-------------|
| **Collection** | `Collection` | `schemas/collection.yaml` | Folder-like container for organizing content. Hierarchy via `parent_id`. Namespaces: `null` (main), `"snippets"`, `"transforms"`. |
| **Card** | `Card` | `schemas/card.yaml` | Question, model, or metric. Holds an MBQL or native `dataset_query`. Display types: table, bar, line, pie, scalar, etc. Card types: `"question"`, `"model"`, `"metric"`. |
| **Dashboard** | `Dashboard` | `schemas/dashboard.yaml` | Grid layout (24 columns) of cards with filter parameters and optional tabs. Contains `dashcards` array for card placement and `parameters` array for filter controls. |
| **Document** | `Document` | `schemas/document.yaml` | Rich text page using ProseMirror AST. Can embed cards via `cardEmbed` nodes and link to entities via `smartLink` nodes. |
| **Segment** | `Segment` | `schemas/segment.yaml` | Saved filter definition scoped to a table. Definition is a pMBQL query with a single stage containing only `source-table` and `filters`. |
| **Measure** | `Measure` | `schemas/measure.yaml` | Saved aggregation definition scoped to a table. Definition is a pMBQL query with a single stage containing only `source-table` and exactly one `aggregation`. |
| **Snippet** | `NativeQuerySnippet` | `schemas/snippet.yaml` | Reusable SQL fragment referenced in native queries via `{{snippet: Name}}`. |
| **Transform** | `Transform` | `schemas/transform.yaml` | Materializes query or Python script results into a database table. Source is either MBQL/native query or Python script. |
| **TransformTag** | `TransformTag` | `schemas/transform_tag.yaml` | Label for categorizing transforms. Built-in types: `"hourly"`, `"daily"`, `"weekly"`, `"monthly"`, or `null` for custom. |
| **TransformJob** | `TransformJob` | `schemas/transform_job.yaml` | Scheduled job (cron) that executes transforms matching specific tags. |
| **PythonLibrary** | `PythonLibrary` | `schemas/python_library.yaml` | Shared Python source file available to Python-based transforms. |

## Extracting the spec and schemas

Extract the full spec to a file:

```sh
npx @metabase/representations --extract-spec --file <path>
```

Extract JSON schemas to a folder:

```sh
npx @metabase/representations --extract-schema --folder <path>
```

Extract both to a temp folder at the start of the session and reference them as needed — e.g. `mktemp -d` then point `--file` and `--folder` inside it.

## Validating

Validate YAML files against the schemas:

```sh
npx @metabase/representations validate-schema --folder <path>
```

Pass the top-level export folder, or the git repository root. The tool finds YAML files in recognized import directories, reads `serdes/meta` to pick the right schema, and exits non-zero on failure.

## Generating entity IDs

Every entity needs a 21-character NanoID for `entity_id`. Generate one with:

```sh
npx nanoid
# → LZfXLFzPPR4NNrgjlWDxn
```
