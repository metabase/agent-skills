# Build clean tables

Applies: an approved inventory, or one model added later (skip to step 3, add its Models row, tag it into the job). Produces transforms, gated, hidden until final, scheduled, with a standing check alert.

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 pre-flight` `2 collections, tag, job` `3.<model> build` `4.<model> gate` `5.<table> metadata` `6 job, alert` `7 change` `reply`.

Read first: [`layering-and-naming.md`](../references/layering-and-naming.md), [`data-quality-checks.md`](../references/data-quality-checks.md), and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`.

```bash
source ./.scratch/probe.sh                                  # q(): references/state.md
mb collection create --body '{"name":"stg_billing"}' --namespace transforms
mb transform-tag create --body '{"name":"rde_billing"}'
mb transform-job create --body '{"name":"rde_billing daily","schedule":"0 0 3 * * ?","tag_ids":['$TAG']}'
q "SELECT * FROM (<model sql, slice predicate on>) t LIMIT 5" # pass: status completed
src() { jq -n --rawfile s "$1" --argjson db $DB '{type:"query",query:{"lib/type":"mbql/query",database:$db,stages:[{"lib/type":"mbql.stage/native",native:$s}]}}'; }
jq -n --argjson src "$(src ./.scratch/<m>.sql)" --rawfile d ./.scratch/<m>.desc --argjson db $DB '{name:"<m>",description:$d,collection_id:<layer-collection-id>,tag_ids:['$TAG'],source:$src,target:{type:"table",database:$db,schema:"<out_schema>",name:"<m>"}}' > ./.scratch/t.json
mb transform create --file ./.scratch/t.json | jq '{id,target}'
jq -n --argjson src "$(src ./.scratch/<m>.sql)" '{source:$src}' > ./.scratch/patch.json
mb transform update <id> --file ./.scratch/patch.json       # source-only patch
mb transform run <id> --sync | jq '{status:.final.status, table:.target_table_id, msg:.final.message}'
mb transform list --full | jq '[.data[] | select(.source.query.stages[0].native | test("<schema>.<name>")) | .id]'   # dependents
```

## 1. Pre-flight

Read STATE.md; confirm its tables exist (`mb table list --db-id $DB --fields id,name,schema`). Smoke-test the write path: transform `_rde_smoke` (one literal row into `out_schema`), `run --sync`, `delete-table --yes`, `transform delete --yes`; a permission or missing-schema error is a `[CHECKPOINT]` for the admin.

## 2. Collections, tag, job, rows

Reuse what exists; else one collection per layer, one tag per chain, one job over the tag at the loader's cadence (ask when data lands; default daily after, `[DECIDED, reversible]`). Ids into STATE.md; one Models row per model in dependency order, `cfg_<domain>` first when a constant exists. Materialization: `layering-and-naming.md`.

## 3. Build loop, one model at a time

SQL in `./.scratch/<m>.sql`; `<m>.desc` carries the five facts plus every constant per `layering-and-naming.md`, mirrored in the SQL header. Raw-table blocks: `staging-rules.md`; staging is a CTE unless shared or expensive. Validate on a slice (a bounded predicate on the driving table) through `q` until the shape and the step 4 checks pass; drop the predicate, create or patch, `run --sync`, then hide the new table (`visibility_type: technical`) until its gate passes. `table: null`: `mb transform get <id> --fields target_table_id`. A failed run: fix the file, patch, run again; unreadable: `mb skills path transform`, Read "Iterating on a failing transform". MBQL source: `jq .source.query ./.scratch/t.json | mb query --file - --dry-run` replaces `q`.

## 4. Gate

The eight checks as one query per `data-quality-checks.md`, at its cadence. A FAIL stops the chain. Judgment calls (`modeling-decisions.md`) are `[DECIDED, reversible]` from the profile, `[CHECKPOINT]` when irreversible. Write the Checks and Models rows. Then `mb table update <table-id> --body '{"visibility_type":"technical"}'` on every raw, staging, and intermediate table the model read or wrote.

## 5. Metadata on final-layer tables

Per table, unhide it (`"visibility_type":null`), then in the order `semantic-layer-design.md` gives, bodies in [`build-semantic-layer.md`](build-semantic-layer.md). Under time pressure stop after keys, foreign keys, currency, and hidden plumbing, and say what remains.

## 6. Schedule, run once, leave a check

`mb transform-job transforms $JOB` lists every model; `mb transform-job run $JOB`, then `mb transform runs` until none is `started`: every member `succeeded`. Per layer, the standing check card and its `has_result` alert (bodies in `data-quality-checks.md`, Checks that outlive the build).

## 7. Change a deployed model

Copy the SQL to `<m>.prev.sql` (rollback is a patch with it). Classify: logic only, patch and run; shape change, `mb transform delete-table <id> --yes` first; rename, re-point every definition and card on the old column. Find dependents in stored SQL, run the job, re-gate each rebuilt table, re-verify their definitions per `semantic-layer-design.md`, add the timeline event (body in `validate-and-reconcile.md`), restate per the contract.

Finished example, a transform description (the SQL header mirrors it):

```
One row per customer per month (key: customer_id, period_month). Sources: int_billing_invoice_line_spread, cfg_billing. Definition: recognized recurring revenue per customer per month from spread invoice lines; state new/retained/lapsed/reactivated by the gap rule. Caveats: USD only; one-off charges flagged, not removed; newest month flagged incomplete. Constants: cfg_billing.gap_months = 1 (D7, open); cfg_billing.last_complete_period = 2026-08.
```

## Done when

Every Models row has `transform_id`, `table_id`, rows, no FAIL; the job ran once, every member `succeeded`; plumbing hidden; metadata done or its stop stated; check card and alert exist; STATE.md `next` is empty.

## Reply

The five-part hand-back in `collaboration-contract.md`; part one links `<base-url>/data-studio/transforms/<id>/inspect`; under part three: what one row of each table is, the constants decided, the checks and counts.
