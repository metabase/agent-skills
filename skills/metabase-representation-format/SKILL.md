---
name: metabase-representation-format
description: Understands the Metabase Representation Format — a YAML-based serialization format for Metabase content (collections, cards, dashboards, documents, segments, measures, snippets, transforms). Use when the user needs to create, edit, understand, or validate Metabase representation YAML files, or when working with Metabase serialization/deserialization (serdes). Covers entity schemas, MBQL and native queries, visualization settings, parameters, and folder structure.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## Metabase Representation Format

Metabase represents user-created content as a tree of YAML files. Each file is one entity (a collection, card, dashboard, etc.). The format is **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

The format is defined by a spec bundled alongside this file as `spec.md` (upstream source: the `@metabase/representations` npm package). The same package ships a CLI (`npx @metabase/representations validate-schema`) that validates a tree of YAML files against the format.

## Entities

The format defines 11 entity types.

| Entity | SerDes Model | Description |
|--------|-------------|-------------|
| **Collection** | `Collection` | Folder-like container for organizing content. Hierarchy via `parent_id`. Namespaces: `null` (main), `"snippets"`, `"transforms"`. |
| **Card** | `Card` | Question, model, or metric. Holds an MBQL or native `dataset_query`. Display types: table, bar, line, pie, scalar, etc. Card types: `"question"`, `"model"`, `"metric"`. |
| **Dashboard** | `Dashboard` | Grid layout (24 columns) of cards with filter parameters and optional tabs. Contains `dashcards` array for card placement and `parameters` array for filter controls. |
| **Document** | `Document` | Rich text page using ProseMirror AST. Can embed cards via `cardEmbed` nodes and link to entities via `smartLink` nodes. |
| **Segment** | `Segment` | Saved filter definition scoped to a table. Definition is a pMBQL query with a single stage containing only `source-table` and `filters`. |
| **Measure** | `Measure` | Saved aggregation definition scoped to a table. Definition is a pMBQL query with a single stage containing only `source-table` and exactly one `aggregation`. |
| **Snippet** | `NativeQuerySnippet` | Reusable SQL fragment referenced in native queries via `{{snippet: Name}}`. |
| **Transform** | `Transform` | Materializes query or Python script results into a database table. Source is either MBQL/native query or Python script. |
| **TransformTag** | `TransformTag` | Label for categorizing transforms. Built-in types: `"hourly"`, `"daily"`, `"weekly"`, `"monthly"`, or `null` for custom. |
| **TransformJob** | `TransformJob` | Scheduled job (cron) that executes transforms matching specific tags. |
| **PythonLibrary** | `PythonLibrary` | Shared Python source file available to Python-based transforms. |

## Ownership and hierarchy

> **Critical — folder layout is decorative.** Where an entity lands in Metabase is decided **entirely** by its fields, not by where its YAML file sits in the tree. Moving a file without updating the fields changes nothing. Updating the fields without moving the file still works correctly. **Always treat the fields below as the source of truth.**

The fields that actually determine placement:

- **`collection_id`** (entity_id of a collection) — places the entity in that collection. `null` or omitted → root collection.
- **`parent_id`** on a **collection** — **this, and only this, sets the collection's own parent.** A collection's position in the folder tree is ignored on import; without `parent_id` (or with `parent_id: null`) the collection becomes a root-level collection, no matter how deep its folder is nested. To nest one collection under another, set `parent_id` to the parent collection's `entity_id`.
- **`dashboard_id`** / **`document_id`** on a **card** — nests a card under a dashboard or document. Such a card **must also** set `collection_id` to match the parent's `collection_id`. A card never sets both.

On disk, cards nested under a dashboard or document live in a subfolder next to the parent YAML (e.g. `my_dashboard/card.yaml` sitting next to `my_dashboard.yaml`) — but again, this is purely for human navigation; the fields are what Metabase reads.

## Import paths

Metabase only imports YAML from these top-level directories; anything outside is ignored:

- `collections/` — all user content (cards, dashboards, documents, snippets, transforms, etc.), partitioned by namespace: `main/`, `snippets/`, `transforms/`.
- `databases/` — **only** the `segments/` and `measures/` subdirectories under each table are imported.
- `python_libraries/` (also accepted as `python-libraries/`).
- `transforms/` — contains `transform_jobs/` and `transform_tags/`.

## `serdes/meta`

Every entity carries a top-level `serdes/meta` array that encodes its identity path. Each entry is `{id, model, label?}` — `label` is the slugified name and is present on entities keyed by NanoID. Example:

```yaml
serdes/meta:
- id: NDzkGoTCdRcaRyt7GOepg
  label: my_entity_name
  model: Card
```

`validate-schema` reads `serdes/meta` to determine which entity type each file represents. The full rules (including nested entities and composite identity paths) are in `spec.md`.

## Reading the spec

This skill ships with a local snapshot of the spec as `spec.md` alongside `SKILL.md`.

Beyond the per-entity shapes summarized in this SKILL, `spec.md` also covers: MBQL query form (stages, field references, joins, expressions, aggregations, filter/expression operators, temporal bucketing, binning), native queries and template tags (`text`, `number`, `date`, `boolean`, `dimension`, `temporal-unit`, `card`, `snippet`, `table`), visualization settings, click behavior, and dashboard/card parameters. Reach for `spec.md` whenever edits touch any of those.

**Read on demand, not eagerly.** Open `spec.md` only when you are about to read or modify content files for the entities listed above — e.g. the user asks to edit a card, add a dashcard, tweak a transform, or similar work that implies YAML edits. Do not open it at session start or for tasks unrelated to representation YAML.

If the bundled copy looks out of date with the upstream package, the skill's own `README.md` documents how to refresh it with `extract-spec`.

## Validating

Validate edits with the built-in CLI:

```sh
npx @metabase/representations validate-schema --folder <path>
```

Pass the top-level export folder, or the git repository root. The tool walks the import paths listed above, reads `serdes/meta` on each file to pick the right validation rules, and exits non-zero on failure. Prefer running this over manually cross-checking field shapes. It's essentially instant, so invoke it whenever useful — after each edit, between edits, whenever the shape of a file feels uncertain. No reason to batch.

## Generating entity IDs

Every entity needs a 21-character NanoID for `entity_id`. Generate one (or several) with the bundled CLI:

```sh
npx @metabase/representations generate-entity-id
# → LZfXLFzPPR4NNrgjlWDxn

npx @metabase/representations generate-entity-id --count 5
```

## Generating UUIDs

Some fields in the format require v4 UUIDs rather than NanoIDs — notably `lib/uuid` on MBQL aggregation clauses (referenced from `order-by` and later stages) and the `id` on dashboard/card parameters. Generate them with:

```sh
npx @metabase/representations generate-uuid
# → 1d4e9fdf-49ae-4fbe-ae27-05e7c6a5cfe8

npx @metabase/representations generate-uuid --count 3
```
