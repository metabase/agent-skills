# Verification and rollback

There is no undo button. A swap can't be reversed (`cycle-detected`), cancel doesn't revert, and phase-1 ref rewrites
leave no revision. So the safety net is what you capture **before** each write.

## Snapshot before every write batch

Write the snapshot to `./.scratch/model-migration/snapshots/<wave>/<model_id>/`:

- **The model itself:** `mb card get <M> --full`, its actions in any state, its dashcards (with their dashboards'
  `tabs`), series, alerts, and the affected metrics' `dimensions` / `dimension_mappings`
  (`GET /api/metric/<id>?include-orphaned=true`).
- **The closure's definitions.**
  - App-DB path: select the full `report_card` rows (`dataset_query`, `visualization_settings`, `parameters`,
    `parameter_mappings`, `result_metadata`, `type`, `archived`, `collection_id`), plus `report_dashboard` and
    `report_dashboardcard` rows (dashboard `parameters`; dashcard `card_id`, `parameter_mappings`,
    `visualization_settings`, `action_id`), plus `parameter_card` rows for every entity in the closure, and the model itself.
  - API path: `mb card get <id> --full` and `mb dashboard get <id> --full` for every direct dependent and its dashboards.
- **Run bookkeeping:** run ids, start and end times, and the revision ids the run created (`revision` rows by the running user in that window).
- **"Before" results** for a sample: the model itself, its 10–20 most-viewed dependents, and every dependent that is verified or has an alert or subscription.

## Result checks

Use exports, never the JSON envelope. `mb card query <id> --json` caps rows (2,000 / 10,000) and may serve cached
results; `--export-format csv` re-runs the query uncapped.

```bash
d=./.scratch/model-migration/verify; mkdir -p $d/before $d/after
for id in $(cat $d/card_ids.txt); do mb card query "$id" --export-format csv --profile P > "$d/before/$id.csv"; done
# … swap …
for id in $(cat $d/card_ids.txt); do mb card query "$id" --export-format csv --profile P > "$d/after/$id.csv"; done
for f in $d/before/*.csv; do a="$d/after/$(basename "$f")"
  h1=$(tail -n +2 "$f" | LC_ALL=C sort | shasum -a 256); h2=$(tail -n +2 "$a" | LC_ALL=C sort | shasum -a 256)
  [ "$h1" = "$h2" ] && echo "OK   $(basename "$f")" || echo "DIFF $(basename "$f") $(($(wc -l <"$f")-1)) → $(($(wc -l <"$a")-1)) rows; header $( [ "$(head -1 "$f")" = "$(head -1 "$a")" ] && echo same || echo changed)"
done
```

- Sort before hashing, because row order isn't guaranteed. Compare headers separately. A changed header usually means
  display names changed (model overrides vs table metadata). That is expected if the user chose "accept table
  metadata", and a bug if they chose "promote".
- **Expected differences:**
  - A transform is a snapshot, so live-model results drift until the next refresh. Compare right after a run.
  - A wrapper with a `LIMIT` loses it.
  - Questions using `now()` or relative dates shift with time.
  - State these in the docs rather than treating them as failures.
- **Large results:** checksum in the warehouse. Compile the card's query with `mb query --compile`, then run
  `select count(*), md5(string_agg(md5(row(t.*)::text), '' order by md5(row(t.*)::text))) from (<sql>) t` (Postgres;
  adapt for other engines), before and after.
- **Model vs. table** (swap to an existing table): compare `mb card query <model> --export-format csv` with an ad-hoc
  `mb query` on `source-table <T>` over the same columns.
- **Transform vs. model:** do the same right after the first run. Also check key uniqueness and row count.

## Structural checks after each run

1. `GET /api/ee/replacement/runs/<id>` returns `status: succeeded`. For any other status, read `message` and treat the run as partially applied.
2. **Nothing references the model any more**, except what you'll fix as leftovers:
   - `mb dependency dependents card <M> --include-personal-collections` lists only leftover kinds: dashcards showing
     it, documents, sandboxes, actions;
   - the text-reference query (`inventory-and-classification.md`) returns 0 rows.
3. **Nothing is broken:**
   - `mb dependency broken table <T>`;
   - `mb dependency dependents table <T> --broken`;
   - `mb dependency breaking` instance-wide, compared with a baseline you took before the wave.
4. **Stale editors.** Re-run check 2 a few hours later, or at the start of the next session. Re-fix any card that was
   re-saved with the old source.
5. **Metric dimensions.** `GET /api/metric/<id>?include-orphaned=true` for each metric that was on the model: no `status/orphaned`, and the default time dimension is intact. Without the flag, orphaned dimensions are hidden and this check always passes.
6. **Access.** Spot-check as a non-admin in a group that used the model, or compare effective permissions: they can
   open the dependents and explore the table.

## Rollback

| Situation | Action |
|---|---|
| A swapped card is wrong | `POST /api/revision/revert {"entity":"card","id":<id>,"revision_id":<pre-run revision>}`, or restore from the snapshot with `mb card update <id> --file snapshot.json`, using only the fields you changed. Either one un-verifies a verified card; re-verify with `mb card verify <id>` |
| A whole run must be undone | Restore each phase-2 entity from its revision or snapshot. Phase-1 ref normalization is functionally neutral; leave it |
| A dashboard edit is wrong | `mb dashboard update <id>` with the snapshot's `dashcards`, `tabs` **and** `parameters`. All three are whole-array replacements |
| An archived model is needed again | `mb card update <id> --body '{"archived":false}'`. Its bookmarks and dashcards reappear. Alerts deleted at archive time **don't come back**, and neither do filter value sources reset at archive time: restore `values_source_type` / `values_source_config` from the snapshot's dashboard and card `parameters`, and recreate the alerts (original creator, `edge-cases.md` § 4) |
| A PR is wrong | **Before** that wave's first `replace-source` run: revert the merge commit and let the instance import it. Removing a transform's YAML deletes the transform but **not** its table. **After** cut-over, never revert a transforms or publish PR: that unpublishes tables, drops FK semantics that swapped dependents rely on, and stops refreshes of tables now in use. Fix forward with a new PR that corrects only the wrong file |
| A hard-deleted model | gone, along with its revisions, verification and alerts. Only the pre-purge snapshot (`snapshots/purge/<id>/`) remains, which is why the purge waits for the grace period, re-runs the gate, and snapshots each model right before deleting it |

Record every rollback in the migration docs.
