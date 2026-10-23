# Remote sync, YAML shapes, and the PR

If the `metabase-representation-format` skill is available, load it for the full serialization spec. This file covers
only what the migration touches, and the traps.

## What lives where in a remote-sync repo

| Content | Path | Synced when |
|---|---|---|
| Cards (question/model/metric), dashboards with their dashcards inline, documents | `collections/main/<collection path>/<slug>.yaml`; dashboard questions sit in `<dashboard_slug>/` next to the dashboard | the collection is synced |
| Collections | `collections/main/<slug>.yaml` beside the folder | synced |
| Library | `collections/main/library/{data,metrics,dashboards}/…`; Data subcollections have `type: library-data` | Library synced |
| Transforms, and their tests | `collections/transforms/<transforms folder>/<name>.yaml`; tests in `<transform_slug>/<test>.yaml` | transform sync on: **all** transforms |
| Transforms-namespace folders | `collections/transforms/<slug>.yaml` with `namespace: transforms` | same |
| Transform tags | `transforms/transform_tags/<name>.yaml`. Built-in tags (hourly/daily/weekly/monthly) have fixed entity ids and no file | same |
| **Transform jobs** | **nowhere. Jobs never sync** | – |
| Published-table metadata | `databases/<db_slug>/schemas/<schema>/tables/<table>/<table>___tableusersettings.yaml`; schemaless DBs use `databases/<db>/tables/<t>/` | the table is published in a synced Library collection |
| Field metadata | `…/tables/<table>/fields/<field>___fieldusersettings.yaml`; FK display remaps in `<field>___dimension.yaml` | same |
| Segments / measures on a table | `…/tables/<table>/segments/*.yaml`, `…/measures/*.yaml` | same. A segment on an *unpublished* table silently doesn't sync |
| Actions | model actions sit with their model's collection; **model-less** (data) actions are Library content | model actions: their collection is synced. Model-less actions: the Library is synced |
| Timelines | with their collection | the collection is synced |
| Never synced | users, groups, permissions, alerts, subscriptions, jobs, personal collections, bookmarks, metadata of unpublished tables | – |

## Reference encoding

| Kind | YAML form |
|---|---|
| Database | its display name: `database: Analytics DW` |
| Table | `[db, schema, table]` |
| Field (MBQL 5) | `[field, {opts}, [db, schema, table, column]]` |
| Field in a card-sourced or later stage | `[field, {base-type: …}, "column_name"]` |
| Dashboard `parameter_mappings[].target` (legacy form) | `[dimension, [field, [db, schema, table, col], {source-field: …}|null], {stage-number: N}?]` |
| Card, dashboard, collection, segment, measure, tag | 21-character `entity_id` |
| User | email. An unknown email is **created as an inactive user** on import |

Import resolution rules:

- An `entity_id` reference that doesn't resolve **fails the whole import**.
- An unknown table or field reference is synthesized as an **inactive stub**. A later transform run that finds the table
  by db/schema/name activates it [unverified end to end: test on rehearsal before relying on a one-PR flow].

## YAML for the migration

### Transform (new file)

```yaml
name: <table_name>                       # convention: same as target.name
description: '<grain, key, caveats>. Replaces the <Model name> model.'
entity_id: <new 21-char NanoID>          # never reuse the model's
collection_id: <transforms-folder entity_id>
creator_id: <email>
owner_user_id: <email of an account that can run the source query on schedule>
source:
  type: query
  query:
    database: <db name>
    stages:
    - lib/type: mbql.stage/native        # or an MBQL stage, with source-table: [db, schema, table]
      native: |
        select …                         # the model's SQL; drop ORDER BY; tables only, no {{#card}}
    lib/type: mbql/query
source_database_id: <db name>
target: {type: table, database: <db name>, schema: <schema>, name: <table_name>}
tags:
- entity_id: <new NanoID>                # the link row
  position: 0
  tag_id: <tag entity_id>                # a tag whose job is ACTIVE on the instance
indexes: []
serdes/meta: [{model: Transform}]
```

Mint NanoIDs with any 21-char `[A-Za-z0-9_-]` generator. Check that the id appears nowhere in the repo.

### Transform tag (only if new)

```yaml
name: <tag>
entity_id: <NanoID>
serdes/meta: [{model: TransformTag}]
```

The job that runs the tag is created on the instance (`mb transform-job create --body '{"name":…,"schedule":"0 0 7 * * ? *","tag_ids":[…]}'`) and recorded in the docs.

### Published table: TableUserSettings

```yaml
table_id: [<db>, <schema>, <table>]
is_published: true
collection_id: <Library Data subfolder entity_id>
display_name: <usually the model's name>
description: '<model description, improved>'
description_set: true
data_layer: final                        # needed for Metabot curated mode
data_layer_set: true
owner_email: <optional>                  # or owner_user_id
serdes/meta: [{model: TableUserSettings}]
```

Optional keys: `entity_type`, `data_authority`, `caveats(+_set)`, `field_order`.

### Field metadata: FieldUserSettings

Write a file only for columns whose desired metadata differs from what sync infers.

```yaml
field_id: [<db>, <schema>, <table>, <column>]
display_name: <from the model, if agreed>
description: <…>
description_set: true
semantic_type: type/FK
semantic_type_set: true
fk_target_field_id: [<db>, <schema>, <pk table>, <pk column>]   # point at a published table
fk_target_field_id_set: true
settings: {view_as: link, link_url: '…'}                          # column formatting, from the model
serdes/meta: [{model: FieldUserSettings}]
```

**Existing file?** Edit it in place and keep every key it already has. On import, FieldUserSettings **clears every
user-settable column the file omits**, and for all models the spec defaults apply to absent keys (for example the
`*_set` flags reset to false). A fresh minimal file written over an existing one wipes the overrides. Leave out
`visibility_type` unless the user asked for it: on a shared table it is global, and "Do not include" breaks other
content (`edge-cases.md` § Permissions).

These are the keys Metabase's own model→transform conversion copies (description, display_name, semantic_type,
fk_target_field_id, settings, visibility_type), minus `visibility_type`, which needs an explicit decision. **FK semantics on the table must exist before the swap**, or
`check-replace-source` fails.

### Synced dependent card: `source-card` → `source-table`

```diff
-    source-card: <model entity_id>
+    source-table: [<db>, <schema>, <table>]
     filters:
     - - '='
       - {}
-      - [field, {base-type: type/Text}, status]
+      - [field, {}, [<db>, <schema>, <table>, status]]
```

- In the stage whose source was the model, name refs become field paths. Non-type options such as `temporal-unit`,
  `binning`, `join-alias` and `source-field` are kept. Later stages keep name refs. Apply the same rule inside `joins[]`.
- Native: replace `{{#<id>-slug}}` with the literal `schema.table`, and delete the `card` template tag.
- Dashboards: rewrite `parameter_mappings[].target` to the field-path form. Drop or retarget `values_source_config.card_id = <model>`.

### Metrics: rewrite the dimension blocks too

```yaml
dimension_mappings:
- dimension-id: <keep the existing uuid>
  table-id: [<db>, <schema>, <table>]
  target: [field, {base-type: type/DateTime}, [<db>, <schema>, <table>, created_at]]
  type: table
dimensions:
- id: <same uuid>
  name: created_at
  group: {display-name: <table display name>, id: <uuid>, type: main}
  sources: [{type: field, field-id: [<db>, <schema>, <table>, created_at]}]
  status: status/active
  lib/source: source/table-defaults
```

Don't rely on absent keys being left alone: spec defaults fill them, and for some models omitted columns are cleared.
Write the full blocks. Whether `dimensions: null` re-seeds the dimensions is [unverified]; test on rehearsal. The most robust route is to re-point the metric on a read-write
rehearsal instance, open it so the dimensions re-seed, re-curate, and export.

## Import semantics that matter

| Repo change | Effect on a read-only instance at the next import |
|---|---|
| New file | entity created with that `entity_id` |
| Changed file | updated. For FieldUserSettings, columns the file omits are **cleared**; for every model, spec defaults fill absent keys. Edit files in place, keeping their keys |
| Removed card/dashboard/document file in a synced collection | **hard delete** (no Trash) and its cascades |
| Removed transform/tag/test file | deleted globally |
| Removed `___tableusersettings` / `___fieldusersettings` | table unpublished, overrides lost |
| Archived synced item | its file is removed on the next export. No exporter writes `archived: true` |
| Local unsynced transform, tag or test on the instance | **blocks every full import** ("deletion conflict") until resolved or forced |

After a merge, watch `mb git-sync status --profile <p> --json` (`current_task.status`, `current_task.error_message`,
`current_task.conflicts`, `is_dirty`) and `mb git-sync has-remote-changes --json` (`local_version` vs `remote_version`).
A `conflict` or `error` blocks **all** further imports from the branch, so resolve it before anything else.

## PR structure (mode A)

Per wave, batched by Library folder or transforms folder:

1. **PR "add transforms"**: transform YAML, plus new transforms folders, tags and tests. After the merge and import, run
   each transform once on the instance (`mb transform run <id> --sync`, with approval) and verify the rows.
2. **PR "publish"**:
   - TableUserSettings and FieldUserSettings for the new tables, and for existing tables that are becoming published
     replacements;
   - FK and entity-key fixes;
   - metadata promotions agreed in the interview;
   - synced dependents rewritten;
   - metric dimension blocks.

   Wrapper-only waves need just this PR.
3. **Instance-side cut-over** (Phase 6), then the docs.
4. If models themselves are synced: leaving git means a **hard delete** on every instance that imports the branch. A
   read-only instance can't move or archive a synced card, and moving a card out of sync scope on a read-write instance
   also removes its file. So keep synced models synced and unarchived until the purge date. Then, after the full purge
   gate and pre-purge snapshot (SKILL.md Phase 8), open **PR "drop models"** to remove their files (mode A), or archive
   and export (mode B). Setting `archived: true` in the YAML might import as "moved to Trash"; that is [unverified], so
   test it on rehearsal before offering it.

Use a one-PR shape (transform plus publish together) only if the rehearsal instance proved that stub-table import works
on this version.

### Authoring routes

- **Rehearsal instance tracking a feature branch** (best): on the rehearsal profile, run `mb git-sync create-branch <branch>`
  (this switches the tracked branch) or `mb git-sync stash --new-branch <branch> -m "…"`, then build there. Run
  `mb git-sync export-preflight`, then `mb git-sync export -m "…"`. On servers with the branch guard, `--branch` must
  name the branch already tracked, or you get a 409. Revert serializer churn the change didn't cause (timestamps, ids,
  data-app files), open the PR, and switch the instance back to its usual branch after the merge.
  - Make sure the rehearsal instance doesn't write into the production warehouse, unless the user accepts that.
- **Hand-written YAML** in the exported shape. Then:
  - validate it with the `metabase-representation-format` skill's schema check, if available;
  - resolve every `entity_id` you reference;
  - ideally import it into a disposable instance before opening the PR.

### Hand-authoring MBQL transforms

The API returns numeric ids, but YAML needs `[db, schema, table, column]` paths. Take `mb card get <M> --fields dataset_query`,
then resolve each id: `mb field get <id> --fields name,table_id`, `mb table get <table_id> --fields name,schema,db_id`,
and `mb db get <db_id> --fields name`. Write `[field, {opts}, [db name, schema, table, column]]`, keeping non-type opts
(`temporal-unit`, `binning`, `join-alias`, `source-field` → also a path).

If the model has joins or expressions and there's no rehearsal instance to export from, prefer a SQL transform whose
column aliases equal the model's keys exactly (quoted). Then hand-write the transform test with unqualified SQL.

### Docs and other consumers

- The migration docs go in a folder outside the serialized top-level directories (`collections`, `databases`,
  `transforms`, `actions`, `snippets`, `glossary`, `data_apps`, …), e.g. `docs/model-migration/`, in a docs-only PR.
- Every instance importing the branch gets the transforms. Built-in tags (hourly/daily/weekly/monthly) have fixed entity
  ids, so any active job on them there runs your transforms too, writing into whatever warehouse that instance points
  at. List the consumers' jobs on the tags you use (`mb transform-job list --full --profile <x>`). Either disable those
  jobs there, or use a new tag with a job only on the target.

### PR body

Follow the repo's house style, which you can read from recent merged PRs. Include:

- a short summary;
- a table of *Model (id) | Replaced by | Library folder | Schedule (tag → job) | Owner*;
- how the SQL or MBQL differs from the model (dropped `ORDER BY`, explicit columns, inlined upstream);
- verification: row counts, checksums, metric values before and after, and what you did **not** test;
- post-merge steps: which transforms to run, which jobs to create, how to check the import;
- the attribution line the repo uses.
