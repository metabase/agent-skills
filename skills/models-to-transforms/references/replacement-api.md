# Source replacement API: exact behavior

Code: `enterprise/backend/src/metabase_enterprise/replacement/` (api, runner, source_check, field_refs, source_swap,
usages, timeout) and `src/metabase/source_swap/`. All routes require a superuser and the `dependencies` premium
feature. There is no `mb` verb for them, so call them with `scripts/mb_rest.mjs`.

## Endpoints

| Call | Body | Result |
|---|---|---|
| `POST /api/ee/replacement/check-replace-source` | `{"source_entity_type":"card","source_entity_id":M,"target_entity_type":"table","target_entity_id":T}` | `{success, errors?, column_mappings?}`. **No side effects**: safe on production. The helper allows it without `--allow-write` |
| `POST /api/ee/replacement/replace-source` | same | `202 {run_id}`. `400 "Sources are not replaceable"` (with `errors`) if the check fails. `409` if a run is active |
| `POST /api/ee/replacement/replace-model-with-transform` | `{card_id, transform_name, transform_target:{type:"table",database,schema,name}, target_collection_id?, transform_tag_ids?}` | `202 {run_id}`. **Not used by this skill** (see the end of this file) |
| `GET /api/ee/replacement/runs[?is-active=true]` | – | runs, newest first. `?is-active=false` always returns `[]` (finished runs hold NULL); omit the param and filter yourself |
| `GET /api/ee/replacement/runs/:id` | – | `{id,status,is_active,progress,message,source_*,target_*,start_time,end_time}` |
| `POST /api/ee/replacement/runs/:id/cancel` | – | cancels. Done work stays applied |

Statuses: `pending | started | succeeded | failed | canceled | timeout`. A finished run has `is_active: null`.
`message` holds the error text. For partial swap failures it reads `"N of M entities failed …"` and lists at most 10 entities.

Entity types that actually work are **`card` and `table`**. `transform` appears only in run rows; passing it as an input errors.

## Compatibility check (`check-replace-source`)

The check fails when any of these holds:

1. **Same ref.** `success:false`, with no errors.
2. **Different database** (`database-mismatch`). A model can only be replaced by a table in its own database.
3. **Cycle** (`cycle-detected`). The target transitively depends on the source. This happens, for example, when the
   transform reads the model. It also makes a reverse swap (table→model) impossible for any wrapper model.
4. **Columns.** Every source column needs a target column with the same **match key**, which is
   `lib/desired-column-alias`, falling back to `name`. The match is an exact, **case-sensitive** string comparison.
   Display names are ignored. Extra target columns are fine.
   - A **missing column** shows up only in `column_mappings`, as a row with `source` and no `target`. Nothing is added
     to `errors`, so always inspect `column_mappings`.
   - Per-column errors:
     - `column-type-mismatch`: compatible type *families* are fine. DateTime→Date fails (a date column can replace a datetime source only the other way round); Text↔UUID is compatible.
     - `missing-foreign-key`: the model column is `type/FK` and the table column isn't.
     - `foreign-key-mismatch`: both are FKs, but to different targets.
     - `missing-primary-key`: table→table only. Entity keys never gate a card→table swap.
5. **Table sources only.** `incompatible-implicit-joins` (other tables have FKs into the source) and
   `affects-gtap-policies` (sandboxes). **Neither check runs for a model source.** Check sandboxes on the model's
   underlying tables yourself.

The check does **not** look at permissions, row equality, whether the target is published, archived or active, or `has_field_values`.

Common real-world failures, and their fixes:

- **The table lacks FK semantics the model had.** Set `semantic_type: type/FK` and `fk_target_field_id` on the table's
  fields first. On a read-only synced instance that is FieldUserSettings YAML, merged before the swap.
- **Long column names.** Model aliases are truncated to about 60 bytes with a hash suffix, while the table field keeps
  its full name, so the column counts as missing. This shows up in uploads with long CSV headers and JSON-unfolded
  fields. Neither the swap nor metadata can fix it. Ask the user: rewrite the dependents by hand, keep the model, or
  archive it if unused.
- **Transform output names differ from the model's keys.** Redshift lower-cases identifiers, BigQuery escapes non-alphanumerics,
  and aliases are truncated. See `transforms-and-scheduling.md`.
- **Implicit-join columns** inside a "wrapper" model, such as `account__via__account_id__name`. The model is not really
  a wrapper; classify it as derived MBQL.

## What `replace-source` (card → table) rewrites

Algorithm:

1. Take the **entire transitive closure** of dependents from the dependency graph. It is **unfiltered**: archived
   content, other users' personal collections and the trash are all included.
2. **Phase 1** normalizes field refs on *every* transitive dependent. It uses raw updates, so it creates no revision
   and no remote-sync change event (transforms excepted). An exception here aborts the run.
3. **Phase 2** swaps the source on *direct* dependents. Each entity is wrapped in try/catch and creates a revision
   attributed to the running admin. Failures are collected, and the run ends `failed` with the list.

| Thing pointing at the model | Rewritten? |
|---|---|
| MBQL question/model/metric with `source-card M` at any stage, including joins | **Yes**: becomes `source-table T`, refs become T's field ids, `table_id` is recomputed |
| Implicit joins through the model's FK columns | **Yes**, provided T's column carries the FK metadata |
| Native `{{#M}}` / `{{#M-slug}}`, also inside `[[ ]]` | **Yes**: replaced by the quoted `"schema"."table"`, and the card tag is removed. Column names in the SQL must exist on T |
| Query transforms reading M | Yes, and it publishes a transform update. Python transforms are not rewritten |
| Dashcard `parameter_mappings` of dependent cards, click-behavior parameter mappings | Yes |
| Card `visualization_settings` keys | Partly (phase 1 converts ref keys to name keys) |
| Grandchildren (dependents of dependents) | Phase-1 normalization only. Their source stays the (now swapped) child |
| **Dashcards that show M itself** | **No**. They keep showing the old card |
| **Filters whose dropdown values come from M** (`values_source_config.card_id`), on dashboards and SQL cards | **No** (only for card→card swaps) |
| **Click behaviors that link to M, link cards, `/model/<id>` URLs** | **No** |
| **Snippets** containing `{{#M}}` | **No** |
| **Curated metric `dimensions` / `dimension_mappings`** | **No**. On the next refresh, unmatched mappings flip to `status/orphaned`, possibly including the default time dimension |
| Documents (smart links), sandboxes, actions, alerts, subscriptions, bookmarks, verification, cache config, model index, Metabot prompts, public link, embedding | **No**. All are keyed by the card id |
| Dashcard-level `column_settings` keyed by field refs | No [unverified whether they go stale] |

**The ref-resolution trap.** A dependent ref whose column name doesn't exist on T silently keeps its old shape. The
result is a broken query, not a failed run. So a run can succeed and still break dependents when the check was skipped
or a column was renamed.

## Operational facts

- **One active run instance-wide.** A second request gets 409, but its run row is inserted *before* the check and stays
  `pending` forever. Check `GET /runs?is-active=true` first.
- **Timeout** is 30 minutes after the run row is inserted. A job checks every 10 minutes. The worker notices a cancel
  or timeout only every 50 progress items, where total progress is 2 × the number of dependents. With fewer than 25
  dependents, a cancel lands after all the swaps.
- **Not transactional.** Partial failures stay applied, cancel doesn't revert, and there is no reverse swap
  (`cycle-detected`). Roll back per entity from your snapshot, or from revisions (`POST /api/revision/revert`), and
  only for phase-2 changes.
- **Stale editors.** Someone with an old editor tab can re-save a swapped card with `source-card M` again. There is no
  locking. Re-check after each run.
- **Dependency freshness.** The graph is computed asynchronously, and some cards fail analysis. Their references to M
  have no edge, so the run misses them. Before each run, also scan the query text. On the app-DB path, run the regex
  query in `inventory-and-classification.md`. On the API path, run `mb card list --filter using_model --model-id M`,
  which covers only **unarchived** cards in M's database, and say that archived cards weren't scanned. Fix those by hand.
- **Verification.** Swapped dependents stay verified, because the run uses raw updates. A dependent you re-point by hand
  with `mb card update` loses verification ("Unverified due to edit"), so re-verify it or tell the owner.
- **Remote sync.** The runner bypasses the read-only lock. Make sure the closure contains **no synced entity** before
  running it on a read-only instance: no `remote_sync_object` row with status other than `removed` (`create`, `update`
  and `delete` rows are synced content with local changes), and nothing in `synced_collections`. Synced dependents must
  be rewritten in the PR first; once merged and imported, they no longer depend on M. On a read-write sync instance
  the swap may touch synced dependents. Their changes are tracked and ship with the next export; review `mb git-sync dirty`.
- **Throughput.** About 500 transitive dependents took roughly a minute in practice. Estimate from the closure size,
  and warn about anything above a few thousand items.
- **Checking many models.** `check-replace-source` walks the dependency graph for its cycle check, so it isn't free on
  a big instance. Run it per wave, close to the swap, and sequentially with a short pause, rather than for every model
  at planning time. The inventory's `swap-check-fails` / `needs FK` flags give the planning-time estimate.

## Polling recipe

```bash
H="node <skill>/scripts/mb_rest.mjs --profile <p>"
$H GET "/api/ee/replacement/runs?is-active=true"          # must be []
$H POST /api/ee/replacement/check-replace-source --body-file check.json   # read-only POST, allowed without a flag
$H POST /api/ee/replacement/replace-source --body-file swap.json \
   --allow-write "POST /api/ee/replacement/replace-source"            # only after the user approved this run
# poll every 5–10 s until is_active is null; then read status + message
$H GET /api/ee/replacement/runs/<run_id>
```

## Why not `replace-model-with-transform`

It looks like the whole migration in one call. It isn't.

- It **creates the transform with no remote-sync gate**. On a read-only synced instance that is a transform git
  doesn't have, and the next full import stops with a deletion conflict until someone force-imports.
- It **skips `check-replace-source`** and the target-exists guard, so it can overwrite a table.
- It **doesn't check `type = model`**, so it demotes any card it is given.
- It doesn't publish, describe, set the owner deliberately, or schedule (no tags by default). It copies only six column
  overrides into FieldUserSettings, with no event, so nothing reaches git.
- Its last step converts the model to a question. That **deletes the model's dashboard action buttons and implicit
  actions** and archives its query actions. Indexed-entity search stops, and `/model/<id>` links show "not found".
- A 409 (another run active) leaves an orphan transform behind. A failed swap leaves the transform, the table and some
  swapped dependents in place, with the model unconverted. Retrying creates a *second* transform on the same table.

It is acceptable only on a non-synced, read-write instance, for a single model, when the user has explicitly chosen it
and accepted those effects. Even then it offers nothing the build-then-swap path lacks. Never call it for a model whose
target table already exists, or for which you have already built a transform: it would add a second writer to that table.

## Without the dependencies feature

Some instances lack the `dependencies` token feature: there is no dependency graph and no `/api/ee/replacement`. The
migration still works; you do the rewriting the swap would have done. Run the inventory with `--no-deps`. Dependents
then come from query text: `card list --filter using_model` on the API path (unarchived cards only), or a regex scan of
`report_card.dataset_query` on the app-DB path, which includes archived cards.

For each dependent card of M, in a snapshot-then-write loop with approval:

1. Read it: `mb card get <id> --fields dataset_query,visualization_settings,parameters --max-bytes 0`.
2. **MBQL:** in the stage that read M (stage 0, or a join), replace `source-card: M` with `source-table: T`. Turn that
   stage's name refs (`["field", {...}, "col"]`) into T's field-id refs (`["field", {...}, <T field id for col>]`); look
   the ids up with `mb table fields <T>`. Later stages keep their name refs. Implicit joins (`source-field`) must point
   at T's FK field id.
3. **Native:** replace `{{#M}}` / `{{#M-slug}}` with the quoted `schema.table`, and delete the `card` template tag.
4. Write it with `mb card update <id> --file body.json`. A query change **un-verifies** a verified card, so re-verify
   it (`mb card verify <id>`) or tell its owner.
5. For dashboards holding those cards, rewrite each dashcard's `parameter_mappings` targets and click-behavior targets
   to T's fields. Use the read-modify-write in `edge-cases.md` § 1, which sends `tabs` too.
6. Verify with exports (`verification-and-rollback.md`).

Gates change accordingly. The cut-over verification and the archive gate become: `using_model` returns 0, and the text scan returns 0.
