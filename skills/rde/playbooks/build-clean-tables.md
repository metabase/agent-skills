# Build clean tables

Applies: an approved inventory, or one model added later (skip to step 3, add its Models row, tag it into the job), or one case a transform gets wrong (steps 4 and 5 on that model). Produces transforms, their rules pinned by transform tests, gated, hidden until final, scheduled, with a standing check alert.

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 pre-flight` `2 collections, tag, job` `3.<model> build` `4.<model> test` `5.<model> gate` `6.<table> metadata` `7 job, alert` `8 change` `reply`.

Read first: [`layering-and-naming.md`](../references/layering-and-naming.md), [`transform-tests.md`](../references/transform-tests.md), [`data-quality-checks.md`](../references/data-quality-checks.md), and the domain file STATE.md names.

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
mb transform-test create --file ./.scratch/<m>.test.json | jq '{id,name}'   # body: references/transform-tests.md; v65+. Refuses a mis-declared input set here, before any run
mb transform-test run <id> | jq '{status, failed: [.expectations[] | select(.status != "passed") | {name, status, "row-counts", "missing-rows", "extra-rows", "cell-mismatches", sample, error}]}'   # exit 1 unless passed
mb transform-test update <id> --file ./.scratch/<m>.test.patch.json   # inputs and expectations replace whole, and re-validate
mb transform-test list --transform <id> --fields id,name       # every test on a model
mb transform run <id> --sync | jq '{status:.final.status, table:.target_table_id, msg:.final.message}'
mb transform list --full | jq '[.data[] | select(.source.query.stages[0].native | test("<schema>.<name>")) | .id]'   # dependents
```

## 1. Pre-flight

Read STATE.md; confirm its tables exist (`mb table list --db-id $DB --fields id,name,schema`). Pre-flight fails if the pre-create gate in `SKILL.md` has not returned; run it here when an earlier playbook did not. Smoke-test the write path: transform `_rde_smoke` (one literal row into `out_schema`), `run --sync`, `delete-table --yes`, `transform delete --yes`; a permission or missing-schema error is a `[CHECKPOINT]` for the admin.

## 2. Collections, tag, job, rows

Reuse what exists; else one collection per layer, one tag per chain, one job over the tag at the loader's cadence (ask when data lands; default daily after, `[DECIDED, reversible]`). Ids into STATE.md; one Models row per model in dependency order, `cfg_<domain>` first when a constant exists. Materialization: `layering-and-naming.md`.

## 3. Build loop, one model at a time

SQL in `./.scratch/<m>.sql`; `<m>.desc` carries the five facts plus every constant per `layering-and-naming.md`, mirrored in the SQL header. Raw-table blocks: `staging-rules.md`; staging is a CTE unless shared or expensive. Validate on a slice (a bounded predicate on the driving table) through `q` until the shape and the step 5 checks pass; drop the predicate, create or patch; alias every source table and qualify columns by the alias (step 4 needs it). Then step 4; on green, `run --sync`, then hide the new table (`visibility_type: technical`) until its gate passes. `table: null`: `mb transform get <id> --fields target_table_id`. A failed run: fix the file, patch, run again; unreadable: `mb skills path transform`, Read "Iterating on a failing transform". MBQL source: `jq .source.query ./.scratch/t.json | mb query --file - --dry-run` replaces `q`.

At each layer boundary — staging, intermediate, dimensions, facts, and every later chain the inventory names — the turn ends on an `AskUserQuestion` carrying the decisions taken in that layer, recommendation first, batched per the contract. Do not open the next layer in the same response. A rule discovered mid-layer that changes a headline number is its own stop, taken where it was found, not saved for the boundary.

## 4. Test

For a model that carries a rule (every intermediate and final-layer model; a staging block only when it deduplicates or converts): one test body in `./.scratch/<m>.test.json` per `transform-tests.md`, one input per table the SQL reads (`cfg_<domain>` included), one expectation per rule in the header's Definition and Caveats and per `[DECIDED, reversible]` on the model; the domain file's cases. `transform-test create`, then `run`: red is fixed in `<m>.sql`, patched, run again; the fixture changes only when it was wrong, and the hand-back says so. On green write `tests` in the Models row (`3 pass`) and go to step 5; the model does not materialise on red. A model with nothing to test writes `tests: none` with the reason. Only an unknown `transform-test` command, a `402` on the token feature, or a `422 unsupported-driver` writes `tests: unavailable` and takes the `q()` fallback in `transform-tests.md` — never a version tag read off a head or dev build, which does not parse.

## 5. Gate

The eight checks as one query per `data-quality-checks.md`, at its cadence. A FAIL stops the chain. Judgment calls (`modeling-decisions.md`) are `[DECIDED, reversible]` from the profile, `[CHECKPOINT]` when irreversible; a decision taken here gets its case added to the step 4 test. Write the Checks and Models rows. Then `mb table update <table-id> --body '{"visibility_type":"technical"}'` on every raw, staging, and intermediate table the model read or wrote.

## 6. Metadata on final-layer tables

Per table, unhide it (`"visibility_type":null`), then in the order `semantic-layer-design.md` gives, bodies in [`build-semantic-layer.md`](build-semantic-layer.md). Under time pressure stop after keys, foreign keys, currency, and hidden plumbing, and say what remains.

## 7. Schedule, run once, leave a check

`mb transform-job transforms $JOB` lists every model; `mb transform-job run $JOB`, then `mb transform runs` until none is `started`: every member `succeeded`. Per layer, the standing check card and its `has_result` alert (bodies in `data-quality-checks.md`, Checks that outlive the build).

## 8. Change a deployed model

Copy the SQL to `<m>.prev.sql` (rollback is a patch with it). Run the model's tests as they stand (`transform-test list --transform <id>`, then `run` each): a green baseline, or a finding to report before touching anything. Add the case that motivated the change as a fixture row and its expectation, see it fail. Classify: logic only, patch and run; shape change, `mb transform delete-table <id> --yes` first; rename, re-point every definition and card on the old column, and every expectation that names it. Patch; run the tests; an expectation the changed rule moved is updated in the same step and its old and new rows go in the hand-back, never deleted (a test that has to go is a `[CHECKPOINT]`). Then find dependents in stored SQL, run their tests, run the job, re-gate each rebuilt table, re-verify their definitions per `semantic-layer-design.md`, add the timeline event (body in `validate-and-reconcile.md`), restate per the contract.

Finished example, a transform description (the SQL header mirrors it):

```
One row per customer per month (key: customer_id, period_month). Sources: int_billing_invoice_line_spread, cfg_billing. Definition: recognized recurring revenue per customer per month from spread invoice lines; state new/retained/lapsed/reactivated by the gap rule. Caveats: USD only; one-off charges flagged, not removed; newest month flagged incomplete. Constants: cfg_billing.gap_months = 1 (D7, open); cfg_billing.last_complete_period = 2026-08.
```

## Done when

Every Models row has `transform_id`, `table_id`, rows, `tests` (a pass count, `none` with a reason, or `unavailable`), no FAIL; the job ran once, every member `succeeded`; plumbing hidden; metadata done or its stop stated; check card and alert exist; STATE.md `next` is empty.

## Reply

The five-part hand-back in `collaboration-contract.md`; part one links `<base-url>/data-studio/transforms/<id>/inspect`; under part three: what one row of each table is, the constants decided, the tests per model (count and the cases they pin) and the checks and counts.
