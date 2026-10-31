# Edge cases: everything that hangs off a model

Four operations change what's attached to a model:

- **SWAP**: `replace-source` card→table.
- **ARCHIVE**: `PUT /api/card/:id {"archived":true}`, i.e. `mb card archive`.
- **DELETE**: `DELETE /api/card/:id`, Trash → "Delete permanently", or a remote-sync import of a repo that no longer has the file.
- **TYPE CHANGE**: model→question. This skill avoids it; users or the all-in-one endpoint may still do it.

## Matrix

| Object | SWAP | ARCHIVE | DELETE | TYPE CHANGE |
|---|---|---|---|---|
| Questions/models/metrics on M (MBQL, joins, `{{#M}}`) | rewritten to T | keep working (archived cards still resolve) | **break** ("Card not found") | keep working, but lose model-metadata merging (FK implicit joins, display names) |
| Dashcard showing M itself | **not swapped** | **hidden** (restored on unarchive) | **deleted** | still shows it, running M's original query live |
| Dashcard whose chart **series** include M | not swapped | series hidden | series row **deleted** | unchanged |
| Filter values sourced from M | **not swapped** | **reset** to the default source (raw update, no event; unarchive doesn't restore it) | link deleted; parameter JSON still points at M | works |
| Click behavior / link card / `/model/M` URL | not swapped | opens an archived item | broken | **`/model/` URLs show "not found"** |
| Alerts on M | stay on M | **deleted, and recipients are emailed** (API archive) | deleted | kept |
| Subscriptions including M's dashcard | unchanged | card omitted from sends | dashcard deleted | kept |
| Implicit actions | not swapped | archived; buttons **keep working** | deleted | **deleted** |
| Query actions (`model_id = M`) | not swapped | archived; buttons keep working | deleted | archived |
| Action buttons on dashboards (`dashcard.action_id`, `card_id` is null) | – | keep working | **deleted** | **deleted** |
| Model index | – | deindexed | deleted | deindexed |
| Sandbox with `card_id = M` | not swapped | still works | **deleted → group falls back to unrestricted (data exposure)** | works |
| Sandboxes on M's underlying tables | **not checked**; a new T has none | – | – | – |
| Persistence | – | pruned | pruned | pruned |
| `cache_config` on M | – | kept (inert) | orphaned | kept |
| Bookmarks | stay on M | **hidden** from the sidebar | **deleted** | kept, shown as a question |
| Verification / pin / official collection | – | – | deleted | kept |
| Metabot model list and suggested prompts | – | drops out | prompts deleted | drops out |
| Public link / static embed of M | – | 404 | 404 | works |
| Upload append/replace UI | – | gone | gone | gone (model-only UI) |
| Documents: smart links / embeds | embeds are document-owned card copies and get swapped; **smart links aren't** | archived link | broken | open as a question |
| Explorations using M | – | – | cascade-deleted | – |
| Remote-synced M | – | its file is removed at the next export (read-write sync); 400 "Used by remote synced content" if synced content still uses it | import hard-deletes cards missing from git | – |

There's **no automatic Trash purge**: archived models stay restorable until someone deletes them.

## Fixing the leftovers (cut-over, step 5)

Work in this order. Each fix happens *before* the model is archived.

### 1. Dashcards that show the model, or use it as a series

Use the model's **stand-in question** (SKILL.md, cut-over step 6): one verified question per model, named after it, on T.
Create it here if the model didn't get one for being opened directly. A table wrapper gets `source-table T` with the same `fields` and `order-by`; a new
transform gets just `source-table T`. Copy the old card's display and `visualization_settings`. Column-settings keys stay
valid when names match. Put it in the model's collection, or make it a dashboard question; ask which.

Name it after the model, and give it the **verified badge** once it's final:
`mb card verify <id> --text "Stands in for the <model name> model; reads <schema.table>"`. A model was the curated
entry point people trusted, so the question that takes its place should carry the badge, whether or not the model
itself was verified. Verify last: any later edit to the question's query withdraws the badge.

Swap it in with a careful read-modify-write. **`dashcards` and `tabs` are both whole-array replacements**: an omitted
tab is deleted together with its dashcards, and a partial `parameters` array archives subscriptions that used a dropped
parameter (and emails their creators).

1. `mb dashboard get <id> --full --max-bytes 0 > snapshots/…/dashboard-<id>.json`
2. In a copy, change only the target dashcard's `card_id` and its `parameter_mappings` targets (now pointing at T's
   fields; nothing rewrites these for you), or the card id inside its `series`.
3. `mb dashboard update <id> --file body.json`, where the body holds `dashcards`, `tabs` and `parameters` exactly as read except for that edit.
4. Re-read the dashboard. Assert that the dashcard ids and count, the tab ids and the parameter ids all equal the snapshot.

`mb dashboard update-dashcard` can't change `card_id`. It can change `series`.

### 2. Filters whose values come from the model

These are `values_source_type: card` with `values_source_config.card_id = M`, on dashboard parameters and on SQL cards'
parameters. Snapshot them first: archiving resets them, and unarchiving doesn't bring them back.

- **Default:** set `values_source_type: null` and drop `values_source_config`, when the filter now maps to a column of
  T whose values Metabase can list (`has_field_values: list`).
- Or point `card_id` at a question on T, with `value_field` and `label_field` refs into that question.
- Or use a static list, if that was the intent.

### 3. Links

- Click behaviors with `linkType: question, targetId: M`, and link cards with `entity {model:"dataset", id:M}`: retarget
  them to the replacement question, or to `{model:"table", id:T}`.
- Text cards, card and dashboard descriptions, and documents containing `/model/M`: rewrite them, and list what changed
  in the docs. The app-DB query is in `inventory-and-classification.md`.

### 4. Alerts

An alert can't be moved to another card, and a re-created alert is owned by **you**. It would then run with an admin's
permissions and email results that sandboxed or limited recipients could never see.

1. List the recipients in the plan, under what people will notice. Creating the new alert emails every recipient
   "you were added"; archiving the model later emails them that the old one was deleted.
2. Re-create it (same condition, schedule and recipients) on a replacement question, then immediately
   `PUT /api/notification/:id {"creator_id": <original creator>}` (superuser only) so it runs as before.
3. If the original creator is inactive or lacks view-data on T, don't re-create it. List it for its owner instead.

### 5. Actions and action buttons

- **Query actions** can be re-homed: `PUT /api/action/:id {"model_id": null, "collection_id": <data-actions collection id, or null for the data-actions root>}`.
  - The target must be the data-actions root or a data-actions (or data-apps) namespace collection; anything else gets a 400.
  - Model-less actions are Library content. When the Library is remote-synced, on a read-only instance they must arrive
    as YAML in the repo, and on a read-write instance the change is exported. [unverified end to end: rehearse first]
  - Buttons reference the action id, so they should keep working.
- **Implicit (basic) actions** require a model. Recreate them as query actions (`INSERT` / `UPDATE` / `DELETE` against
  the *source* table, never a transform output, which the next run overwrites) and swap the buttons' `action_id` (§1
  recipe). Or offer table data editing.
- **Public action forms** move with the action if it's re-homed.
- **Deferring** is possible but fragile. Archived actions keep working from their buttons until the purge, so the purge
  gate counts actions in **any** state and their buttons, and refuses while any remain.

### 6. Sandboxes

A sandbox card *is* the row/column filter. Its `attribute_remappings` target that card's template tags or columns.

- **A model used as a sandbox card** must never be materialized as the policy's replacement, and never archived until
  the policy is rebuilt. Build a replacement card that applies the same attribute-bound filters (same template tags or
  filter columns). Update `card_id` **and** every `attribute_remappings` target in one `PUT /api/mt/gtap/:id`. Then, on
  rehearsal, run the policy for at least two users with different attribute values and compare row counts with the old
  policy. If you can't reproduce it, keep the model.
- **Never hard-delete a card that a sandbox uses.**
- **A model built on a sandboxed table:** the new T needs equivalent policies (`POST /api/mt/gtap {group_id, table_id: T, card_id | attribute_remappings}`).
  New transform tables default to `view-data: blocked` for any group with a blocked or sandboxed table in that database,
  which fails closed. Configure them before the swap, or sandboxed users lose access.

### 7. Curated metric dimensions

Metrics built on M carry `dimensions` and `dimension_mappings` aimed at M's columns or its source fields. The swap
leaves them alone, and the next `GET /api/metric/:id` refresh flips unmatched mappings to `status/orphaned`, possibly
including the default time dimension.

- **Before the swap,** snapshot each affected metric: `GET /api/metric/<id>?include-orphaned=true` (without the flag,
  orphaned dimensions are hidden and every check passes), plus `mb card get <id> --fields dimensions,dimension_mappings`.
- **Synced metrics:** rewrite them in YAML (`git-sync-and-yaml.md`). Each mapping gets `target` set to T's field and a
  `table-id`. Each dimension gets `sources`, `group` and `lib/source: source/table-defaults`. Keep the `dimension-id`s,
  so the default and display-name edits survive.
- **Unsynced metrics:** the metrics API can't write dimensions. Either rehearse `PUT /api/card/<id>` with re-targeted
  `dimensions` / `dimension_mappings` on rehearsal first [unverified], or list the metrics and have their owners
  re-curate them in the UI from the snapshot. Record which in the docs.
- **After the swap,** check `GET /api/metric/<id>?include-orphaned=true` for `status/orphaned`, especially the default time dimension.

### 8. Snippets, documents, subscriptions, embeds

- **Snippets** containing `{{#M}}`: edit their SQL to the table name with `mb snippet update`, or in YAML if the snippet is synced.
- **Document smart links:** edit the document.
- **Subscriptions:** fixed by fixing the dashcard (§1). If the dashcard isn't replaced, archiving the model silently
  drops that card from every send of the subscription. List the subscriptions and their recipients in the docs either way.
- **Public link or embed of M:** create one on the replacement question and give embedders the new id. SDK pickers need `"table"` in `entityTypes`.

### 9. Things that can't be migrated

Record each of these in the docs and tell the people affected.

- **Bookmarks.** Tables can't be bookmarked, and you can't bookmark on someone else's behalf. List the holders per
  model, and point them to its stand-in question (named after the model), the table, or its Library folder.
- **Model indexes:** indexed-entity search is lost.
- **Verification:** tables can't be verified; publishing to the Library is their trust signal. Every replacement
  question that stands in for a model gets the verified badge (§1).
- **List view display**, and the model detail page.
- **Upload append/replace UI:** document `mb upload append|replace <table-id> --file <csv>`.
- **Metabot prompts** on the model: list them. For Metabot's curated mode, a published table counts at visibility layer
  `final`, or when its data authority is `authoritative`. Cards count when verified or in an official collection.

## Permissions

Nothing about access is inherited, synced or checked by the swap. In every mode, set it on the instance, **before** the
swap, exactly as the plan's access section says.

**What changes for people:**

- A model let users without "create queries" explore data they could view. A table does that only through **read
  access on its Library collection** (which grants query-builder access) or an explicit create-queries grant.
- A new transform table gets the **database-level** permissions; nothing is inherited from the model or its source
  table. **Table-level grants on the source table** (view-data or create-queries given per table) don't carry over:
  re-grant them on T, or those groups lose access.
- Groups with any blocked or sandboxed table in the database are **blocked on every new transform table** by default.
- Publishing a **wider existing table** exposes, to the Library collection's readers, columns the model hid.
  `visibility_type` is global metadata, not access control. "Do not include" breaks every existing question that uses
  the column, and SQL users can still select it. To keep columns hidden, use permissions (a sandbox with a column
  subset), or keep a narrow transform instead of swapping. Never change `visibility_type` on a shared table for this.
- **Impersonated groups:** a transform runs with the connection's credentials, not the group's warehouse role. Its
  table therefore holds rows that warehouse row-level security or column grants hid from that role. Don't grant an
  impersonated role `SELECT` on a transform table unless its sources have no RLS or column grants for that role.
  Otherwise keep the model, or build per-role transforms (ask).
- Alerts and subscriptions run as their creator, so creators need view-data on T.

**Recipe** (all through the helper; snapshot first; the delta is the one in the plan) [unverified: rehearse first]:

1. Snapshot `GET /api/permissions/graph/db/<db>` and `GET /api/collection/graph`.
2. **Ad-hoc access:** for each group that could read the model's collection, grant read on T's Library collection with
   `PUT /api/collection/graph`. Send the current `revision` and a minimal delta.
3. **Blocked or sandboxed groups:** set view-data on T with `PUT /api/permissions/graph` (current `revision`, minimal
   delta), or create the sandbox with `POST /api/mt/gtap`.
4. Spot-check as a non-admin in an affected group: open a dependent, then explore T.

## Scope questions this raises (ask in the interview)

- **Archived models that still feed active cards** (`swap-archived-feeder`): swap them too, or leave them? Their dependents keep working while they sit in the Trash.
- **Models in personal collections:** the swap touches their dependents anyway (the graph is unfiltered). Migrate, archive if unused, or leave?
- **Archived dependents** get rewritten too. That's usually fine, but say so.
