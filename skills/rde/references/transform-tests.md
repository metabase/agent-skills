# Transform tests

Read before the first model that carries a rule and before changing a deployed one. Tests need `mb transform-test`, which not every CLI release ships (When tests cannot run). Where it ships, verbs and body shapes are in the `transform` skill, "Transform tests", and deeper planning (fixture casts, hand-derived expected rows, coverage matrices, mutation probes) in the `transform-test-plan` skill, read when logic is intricate or the user asks for a plan.

## What a test is

It runs the transform against fixtures instead of its sources: one input per table it reads, the output into a temp table, each expectation checked, temp tables dropped. Nothing real is read or written, the transform need not have run, it takes seconds. Query transforms only (native SQL or MBQL), never Python. The gate checks the data that landed; a test pins a rule on rows chosen to exercise it, including cases the data lacks yet (a lapse exactly at the grace window, a refund line, an `"N/A"` in a lossy cast), and fails the moment a patch or constant changes behaviour. Neither replaces the other, nor reconciliation.

## What to test

Logic that is easy to get wrong (window functions, date math, state machines, ladders, spreading and allocation, dedup with a breaking case), and every model a headline reads. A block that only renames and casts has nothing to test (`tests: none, rename only`). One expectation per rule in the description and per decision recorded for the model (its alternative is what a future patch will try), plus the domain note's Test cases.

| Rule | Fixture rows | Expectation |
| --- | --- | --- |
| Which row wins | a plain supersede, the breaking case, a group of only fragments | `equals` on key and the deciding columns |
| Attribute ladder | one row per rung, one falling to the default | `equals` on key, attribute, `<attribute>_source` |
| State per period | one entity per state; a lapse at the grace window and one beyond | `equals` on entity, period, state |
| Incomplete period | a source whose newest period is partial | `empty` over the `period_flag` failure query |
| Spreading, allocation, conversion | one document per cadence, one mid-cycle change | `equals` on document, period, amount; `empty` where the spread misses the total |
| Exclusion | one row per predicate, one matching none | `equals` on key, flag, `exclusion_reason` |
| Staging dedup, units, epochs, placeholders | a duplicate group, a minor-unit amount, an epoch, an `"N/A"` | `equals` on key and converted columns |
| Gate invariants | any of the above | `empty` over `dup_key`, `null_required`, `non_negative` shapes |

## Fixtures

- Small enough to read at a glance: one case per row, ids in case order, the case list in `description`. Always include the edges: a zero case per outer join and aggregation, a group of two or more per grouping and join, one dirty row per defect the source can carry. Copied production rows are a second gate, not a test, and carry personal data.
- Expected rows are derived by hand from the fixture's story, never captured from output (that only proves the transform equals itself).
- Inputs cover exactly the tables the transform reads, one each; `create` and `update` refuse a mismatch before anything runs (a missing input would read the real table). A model reading `cfg_<domain>` declares it, and a second test runs the decision's alternative value.
- `format: "rows"` by default: `columns` as `{name, cast_type}`, rows with exactly the declared keys (nulls still present). Empty `rows` is an empty source, worth pinning. `format: "sql"` for inputs a literal list would bloat (a spine).
- `cast_type` is a `CAST` target, not the reported type, and differs per engine (MySQL takes `SIGNED` and reports `INTEGER`; ClickHouse takes `Nullable(Int32)`, reads back `Int64`). Read real types with `mb table get <id> --include fields`, write the engine's cast target; a wrong one fails at run time as `setup-failed`.
- Dates are fixed points, never relative to today; a `current_date` rule is exercised on rows the clock cannot reach, or left to the gate.
- In the model's SQL and in expectation SQL, alias every table and qualify columns by alias, never by table name: the temp-table rewrite leaves table-name qualifiers dangling and the run refuses them.

## Expectations

- `equals`: exactly the declared rows over the declared columns, as a multiset. Name the key and the columns the rule decides; leave volatile columns out. Only `format: "rows"` runs; `format: "sql"` on `equals` saves but is refused at run (`unsupported-format`).
- `empty`: a query that must return nothing, naming only the target and declared inputs (anything else reads the real table and is refused: `unremapped-reference`). Open its SQL with a `--` line naming the invariant and what it catches.
- Names state the rule: `lapse at the grace window stays retained`. A failure leads with the name.
- Never author an expectation you expect to fire. A tolerated oddity is a row in the `equals`, noted in the build list with its real-data count.

Shape, for a customer-month movements model:

```json
{"transform_id": <transform-id>, "name": "customer_months: movement states",
 "description": "Cases: customer 1 new, expansion, churn after a zero month, reactivation; customer 2 new, retained, exit row after its last month.",
 "inputs": [
  {"table": {"schema": "<out_schema>", "name": "cfg_billing"}, "format": "rows",
   "columns": [{"name": "grace_days", "cast_type": "INTEGER"}], "rows": [{"grace_days": 0}]},
  {"table": {"schema": "<out_schema>", "name": "int_billing__customer_revenue_months"}, "format": "rows",
   "columns": [{"name": "customer_id", "cast_type": "INTEGER"}, {"name": "revenue_month", "cast_type": "DATE"}, {"name": "mrr_usd", "cast_type": "NUMERIC(12,2)"}],
   "rows": [{"customer_id": 1, "revenue_month": "2026-05-01", "mrr_usd": 100}, {"customer_id": 1, "revenue_month": "2026-06-01", "mrr_usd": 150}, {"customer_id": 1, "revenue_month": "2026-08-01", "mrr_usd": 100},
            {"customer_id": 2, "revenue_month": "2026-06-01", "mrr_usd": 50}, {"customer_id": 2, "revenue_month": "2026-07-01", "mrr_usd": 50}]}],
 "expectations": [
  {"type": "equals", "name": "one movement per customer-month", "format": "rows",
   "columns": [{"name": "customer_id", "cast_type": "INTEGER"}, {"name": "month", "cast_type": "DATE"}, {"name": "movement", "cast_type": "VARCHAR(32)"}],
   "rows": [{"customer_id": 1, "month": "2026-05-01", "movement": "new"}, {"customer_id": 1, "month": "2026-06-01", "movement": "expansion"}, {"customer_id": 1, "month": "2026-07-01", "movement": "churned"}, {"customer_id": 1, "month": "2026-08-01", "movement": "reactivation"},
            {"customer_id": 2, "month": "2026-06-01", "movement": "new"}, {"customer_id": 2, "month": "2026-07-01", "movement": "retained"}, {"customer_id": 2, "month": "2026-08-01", "movement": "churned"}]},
  {"type": "empty", "name": "churn only follows a positive month",
   "sql": "-- a churned month with no prior revenue is a phantom exit\nSELECT m.customer_id FROM <out_schema>.customer_months m WHERE m.movement = 'churned' AND m.prior_mrr_usd = 0"}]}
```

The body is closed (`transform_id`, `name`, `description`, `inputs`, `expectations`); `update` replaces inputs and expectations whole and re-validates; strip `id`, `entity_id`, `creator_id`, `created_at`, `updated_at` from a `get --full` body before sending it back.

## Cadence

- Write tests after `transform create`, before the first run; a clean `create` proves the input declaration. Red is fixed in the SQL, never in the test; the model runs into its table only on green. Record the count in the build list.
- After every source patch, the model's tests run before its gate; after a `cfg_<domain>` change, the tests of every model reading it.
- Changing a deployed model starts by running its tests as they stand. A new case: add it, see it fail, fix, see it pass. A changed rule: the expectation's old and new rows are the change, shown in the hand-back, never deleted; a test that must be deleted is a stop. A renamed or dropped source table means the test's `update` ships in the same patch.
- Once per new test, prove it has teeth: corrupt one expected cell, run, see `cell-mismatches` name that column, revert (every `empty` passes on an empty output).
- On staging, tests export with their transforms; the hand-back names them for the reviewer.

## Reading a result

**A refusal** (`transform-test.<code>`; switch on the code): `400` is the test's authoring: `missing-inputs`, `unused-inputs`, `duplicate-input-table`, `unremapped-reference` (alias and qualify), `unparseable-source`, `unknown-column`, `ambiguous-column`. `422` means the run cannot happen here: `unsupported-transform` (Python), `unsupported-driver`, `transform-failed` (fix the SQL, not the test), `setup-failed` (usually a `cast_type`). `501`: `unsupported-format`.

**A run that happened** (`run` exits non-zero unless passed; report `{status, expectations, tables}`):

- failed `equals`: `missing-rows`, `extra-rows`, `row-counts {actual, expected}`, and `cell-mismatches` (only when exactly one row is missing and one extra); `columns` gives each column's actual `database_type`, the cast target you should have written. Decimals come back as strings at the warehouse's scale (`"1.50"` vs `"1.5"` is scale, not value). `truncated` counts rows past the 50-row cap.
- failed `empty`: `sample` holds violating rows. `status: "error"` on one expectation is its own SQL failing.

```bash
source ./.scratch/probe.sh
mb transform-test run <test-id> --profile "$PROFILE" --json | jq '{status, failed: [.expectations[] | select(.status != "passed") | {name, status, "row-counts", "missing-rows", "extra-rows", "cell-mismatches", sample, error}]}'
```

**A run that never came back**: reaped as `timeout` after five minutes; re-run; a repeat means the fixture is too large.

Fixtures change only when they were wrong (said in the hand-back); expectations are never loosened. A test exposing a live bug is never softened: report the damage at fixture and warehouse scale ("908 of 2,050 orders dropped"), then fix, or hold the correct expectation and record the red with the minimal fix.

## When tests cannot run

Establish availability by running the command, never from a version string (dev builds report tags the CLI cannot parse). If `mb transform-test --help` is unknown, or the CLI refuses a `cast_type` key, the installed release lacks it: `npm view @metabase/cli dist-tags` shows whether any published release ships it; offer to install that one only on the user's yes, and otherwise take the fallback. The warehouse matters too: Snowflake and BigQuery cannot run tests today (orient reads the engine), so say so at the proposal point. Fallback signals: no release with the command (or the user declines one), a `402` (the license lacks transform testing), or `422 unsupported-driver`. Record `tests: unavailable` with the signal and prove each rule once through `q()`: the fixture as a `VALUES` CTE in place of the source in a copy of the SQL, the expectation as a query over it, the result in the build list's note, the SQL kept in `./.scratch/<model>.test.sql` for later. Transforms run in the company's own tool put the same cases in its test facility.
