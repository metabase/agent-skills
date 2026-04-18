---
name: metabase-representation-format
description: Understands the Metabase Representation Format — a YAML-based serialization format for Metabase content (collections, cards, dashboards, documents, segments, measures, snippets, transforms). Use when the user needs to create, edit, understand, or validate Metabase representation YAML files, or when working with Metabase serialization/deserialization (serdes). Covers entity schemas, MBQL and native queries, visualization settings, parameters, and folder structure.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## Metabase Representation Format

Metabase represents user-created content as a tree of YAML files. Each file is one entity (a collection, card, dashboard, etc.). The format is **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

The format is defined by a spec and a set of YAML JSON Schemas, bundled alongside this file as `spec.md` and `schemas/` (upstream source: the `@metabase/representations` npm package).

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

`validate-schema` reads `serdes/meta` to pick the right schema for each file. The full rules (including nested entities and composite identity paths) are in `spec.md`.

## Reading the spec and schemas

This skill ships with a local snapshot of the spec and schemas alongside `SKILL.md`:

- `spec.md` — full v1 specification.
- `schemas/` — per-entity YAML JSON Schemas (`card.yaml`, `dashboard.yaml`, etc.).

Beyond the per-entity shapes summarized in this SKILL, `spec.md` also covers: MBQL query form (stages, field references, joins, expressions, aggregations, filter/expression operators, temporal bucketing, binning), native queries and template tags (`text`, `number`, `date`, `boolean`, `dimension`, `temporal-unit`, `card`, `snippet`, `table`), visualization settings, click behavior, and dashboard/card parameters. Reach for `spec.md` whenever edits touch any of those.

**Read on demand, not eagerly.** Open these files only when you are about to read or modify content files for the entities listed above — e.g. the user asks to edit a card, add a dashcard, tweak a transform, or similar work that implies YAML edits. Do not open them at session start or for tasks unrelated to representation YAML.

If the bundled copies look out of date with the upstream package, the skill's own `README.md` documents how to refresh them with `extract-spec` / `extract-schema`.

## Validating

Validate YAML files against the schemas:

```sh
npx @metabase/representations validate-schema --folder <path>
```

Pass the top-level export folder, or the git repository root. The tool walks the import paths listed above, reads `serdes/meta` on each file to pick the right schema, and exits non-zero on failure.

## Generating entity IDs

Every entity needs a 21-character NanoID for `entity_id`. Generate one with:

```sh
npx nanoid
# → LZfXLFzPPR4NNrgjlWDxn
```
