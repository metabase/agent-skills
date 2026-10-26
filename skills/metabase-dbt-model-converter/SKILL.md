---
name: metabase-dbt-model-converter
description: Converts a dbt project's compiled manifest.json into Metabase Transform YAML files. Use when you want to migrate dbt models to Metabase Transforms, convert dbt SQL models to representation-format YAML, or import dbt models into Metabase.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## What this skill does

Converts a dbt project's compiled `manifest.json` into Metabase representation-format Transform YAML files. The output is ready for `serdes import` into Metabase.

This is a pure JSON-to-YAML transformation. No dbt compilation, no Metabase API calls, no database connections.

## Prerequisites

You need:
- A **compiled `manifest.json`** from your dbt project (produced by `dbt compile`)
- The **creator email** to assign as the transform owner (e.g., `admin@example.com`)

If you haven't compiled the dbt project yet, you need to run `dbt compile` in the dbt project directory.

## How to convert

```bash
npx @metabase/dbt-model-converter \
  --manifest path/to/manifest.json \
  --creator-id admin@example.com \
  --output-dir ./output
```

This produces one YAML file per eligible model under `output/collections/transforms/`.

### What gets converted

- Model nodes with materialization `table`, `view`, `incremental`, or `materialized_view`
- The compiled SQL is used as-is — all Jinja is already resolved by `dbt compile`

### What gets skipped

- **Ephemeral models** — dbt inlines these into downstream models; the compiled SQL of non-ephemeral models already contains the compiled, fully-inlined SQL.
- **Seeds, snapshots, sources, tests** — these are not dbt-managed transformations.

## Validating the output

You can validate the generated YAML against the representations schema:

```bash
npx @metabase/representations validate-schema --folder ./output
```

## Warnings

**"Model X has no compiled SQL"** — The model node in dbt's manifest has no `compiled_code` (dbt >= 1.4) or `compiled_sql` (legacy) field.

**"compiled SQL contains Jinja markers"** — The compiled SQL contains `{{` or `{%`, which means the SQL is likely invalid and will not execute correctly. This can happen when a `{% raw %}` block is used in the source model, preventing Jinja from evaluating its contents.

## Limitations

- **Incremental strategy is not mapped.** `dbt compile` evaluates `is_incremental()` as `False`, so the compiled SQL is the full-refresh version.
- **Tags are not mapped** in v1. dbt tags don't automatically become TransformTags.
- **TransformJobs** (scheduled execution) are not created.
