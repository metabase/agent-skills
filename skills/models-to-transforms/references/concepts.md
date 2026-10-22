# Concepts: models, published tables, transforms, the Library, source replacement

Product docs (current versions): `docs/data-modeling/models/models.md`, `…/models/model-persistence.md`,
`…/semantic-layer/library.md`, `…/semantic-layer/published-tables.md`, `…/transforms/*.md`,
`…/tools/replace-data-sources.md`, `docs/configuring-metabase/caching.md`. Public versions are at
https://www.metabase.com/docs/latest/ under the same paths.

## Model

A **model** is a card with `type = "model"`: a saved question (MBQL or SQL) meant to be the starting point for other
questions. The docs now say "Consider using Transforms instead of models", and that Metabase "will be gradually phasing
out models in favor of transforms".

What a model carries, and whether a published table has an equivalent:

| Model feature | On a published table? |
|---|---|
| Column metadata **local to the model**: display name, description, semantic type, FK target, "maps to DB column" for SQL models, visibility, formatting (`result_metadata` overrides) | Yes, as field metadata, but **global** for every user of the table |
| Makes SQL results explorable in the query builder | Natively; a transform output is a real table |
| **Actions**: implicit create/update/delete, query actions, dashboard action buttons | **No.** Query actions can live without a model (data actions). Implicit actions need a model. Table data editing is the table-side feature |
| **Model index** (search into individual records) | **No** equivalent |
| **List view** display, model detail page | No |
| **Verification** (badge, search boost) | No. Tables can't be verified; publishing to the Library is the trust signal |
| Shown in Browse > Models, boosted in search and pickers | Published tables appear **first** in data pickers and in the Library nav |
| **Upload append/replace UI** (models created by CSV upload) | No UI on the table. The API still works: `mb upload append|replace <table-id>` |
| `{{#123-model}}` references from SQL | The table is referenced by name |
| Model **persistence** (a cached copy in a `metabase_cache_*` schema, refreshed on one instance-wide cron) | The transform *is* the materialization. Persisted tables are excluded from sync and can't be a 1:1 target |
| Collection placement and permissions | Library > Data subcollections. Read access there grants query-builder access (below) |
| Grants ad-hoc query access to people without "Create queries" | Published tables do the same through Library collection read access |
| Bookmarks | **Tables can't be bookmarked**, and an admin can't create bookmarks for other users |
| Metabot: models are a source; "verified or curated only" mode counts verified models and models in official collections | A table counts as curated when it's published at visibility layer **Final**, or when its data authority is `authoritative` |
| Embedding pickers with `entityTypes: ["model"]` | Tables appear only if `"table"` is allowed |

## Published table and the Library

The **Library** is a curated subtree with three parts. **Data** holds published tables in subcollections. **Metrics**
holds metric cards. **Dashboards** holds dashboards. The Library also brings snippets and the glossary, and it can sync
to git.

**Publishing** puts a table into Library > Data (or a subcollection). Rules:

- Only admins and data analysts can publish.
- Publishing cascades **upstream** to tables the table depends on through FK remapping. Unpublishing cascades
  **downstream** to dependents. Archiving a Data subcollection unpublishes everything inside it.
- **Read access on the table's Library collection grants `create-queries: query-builder` on that table.** View-data
  still has to come from data permissions. So Library collection permissions decide who can explore a migrated table
  ad hoc, which is the job a model used to do.
- Table metadata for publishing: display name, description, owner (a user or any email), visibility layer
  (`data_layer`: final / internal / hidden; final is needed for Metabot curated mode), entity type, data source, data
  authority, field order, caveats.
- Field metadata: display name, description, semantic type, FK target, cast (coercion), visibility, filter widget
  (`has_field_values`), formatting settings, remapping, JSON unfolding, custom position.
- On current versions the user-set table state lives in an overlay, `metabase_table_user_settings` (and
  `metabase_field_user_settings` for fields). The raw `metabase_table.is_published` can say false while the table is
  published. The API (`mb table get`) returns the effective values.

## Transform

A **transform** is a query (MBQL or SQL) or a Python script that writes a **new table in the same database**. Metabase
then syncs that table.

- A transform runs when a **job** whose **tags** it carries fires (Quartz cron, system timezone), or manually.
- A job also pulls in dependencies that are stale.
- A run replaces the table. If a SQL run fails, the old table stays.
- Scheduled runs execute **as the transform's owner** (falling back to the creator). Manual runs execute as the requester.
- The type (MBQL / SQL / Python) can't be changed later.
- Incremental mode needs a checkpoint column, optionally a merge key and a lookback window.
- Supported engines: those whose driver advertises `transforms/table`. That covers PostgreSQL, MySQL/MariaDB, Redshift,
  Snowflake, BigQuery, ClickHouse and SQL Server. Not supported: Mongo (Python only), Athena, SQLite, the sample DB,
  the usage-analytics (audit) DB, and DB-routing databases.
- Remote sync serializes transforms, tags and tests. **Jobs don't sync.**

## Source replacement ("Replace data source", "Migrate models")

These are EE/Pro, admin-only routes under `/api/ee/replacement` (premium feature `dependencies`):

- `check-replace-source`: compatibility check, no side effects.
- `replace-source`: async; rewrites every usage of one source (card or table) as a query source to point at another,
  walking the dependency graph.
- `replace-model-with-transform`: creates a transform from the model's query, runs it, swaps, then converts the model
  to a question.

There is no `mb` verb for any of them; use `scripts/mb_rest.mjs`. Exact semantics, what is and isn't rewritten, and the
failure modes are in `replacement-api.md`.

## Caching vs. persistence vs. transform

- **Caching** stores query *results* in the app DB per policy: duration, schedule, adaptive, or none. Precedence is
  question > dashboard > database > default. Models have no caching UI of their own; the "Caching" card in a model's
  settings is persistence. A `cache_config` row with `model='question'` can still target a model id through the API.
- **Persistence** stores a model's rows in the warehouse on one instance-wide cron. It is deprecated in favor of transforms.
- **Transform** materializes on its own schedule and is a first-class table.

`transforms-and-scheduling.md` covers how to turn the first two into the third's schedule.

## Remote sync (git)

- **Read-only** instances import from a branch (often with auto-import every few minutes). Synced content can't be edited there.
- **Read-write** instances export to a branch.
- Synced content must be self-contained: it may depend only on synced content. Otherwise you get the errors
  "Uses content that is not remote synced." / "Used by remote synced content."
- What syncs:
  - collections marked synced, with their cards, dashboards, documents, model actions and timelines;
  - model-less (data) actions, as Library content;
  - the Library (published-table metadata included);
  - snippets and the glossary;
  - all transforms, tags and tests when transform sync is on.
- What doesn't sync: permissions, alerts, subscriptions, jobs, personal collections, bookmarks, metadata of unpublished tables.

Details and YAML shapes are in `git-sync-and-yaml.md`.
