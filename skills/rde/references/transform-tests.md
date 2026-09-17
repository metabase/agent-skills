# Transform tests

Read before the first model that carries a rule, and before changing a deployed one. Requires the instance at v64 or later; the fallback for older instances is at the end.

## What a test is, and what it is for

A transform test runs the transform against fixtures instead of its real sources: one input per table the transform reads, the transform run into a temp table, each expectation checked against that output, the temp tables dropped. Nothing reads or writes a real table, the transform need not have run, and a test takes seconds. Query transforms only (native SQL or MBQL); a Python transform has no test.

The gate ([data-quality-checks.md](data-quality-checks.md)) checks the data that landed: shape, parity, grain, on the rows that exist today. A test checks the logic: it pins a rule on rows chosen to exercise it, including cases the data does not hold yet (a customer whose gap is exactly the threshold, a refund line, a placeholder string in a lossy cast), and it fails the moment a patch or a constant changes the behaviour. The gate runs on every model, tests on every model that carries a rule; neither replaces the other, and neither replaces reconciliation ([reconciliation.md](reconciliation.md)).

## What to test

One test per model that carries a rule; one expectation per rule. The rules to pin are the ones the header's Definition and Caveats name, plus every `[DECIDED, reversible]` recorded for the model: the decision's alternative is what a future patch will try, and the expectation is what tells the user the number moved because the rule did.

| Rule | Fixture rows | Expectation |
| --- | --- | --- |
| Which row wins ([modeling-decisions.md](modeling-decisions.md)) | one group per case: a plain supersede, the family's breaking case, a group of only fragments | `equals` on the key and `is_selected` |
| Attribute ladder | one row per rung, one that falls through to the default | `equals` on the key, the attribute, and `<attribute>_source` |
| State and motion per period | one entity per state; the gap exactly at the constant and one beyond it | `equals` on entity, period, state |
| Flagged incomplete period | a source whose newest period is the partial one | `empty` over the `period_flag` failure query |
| Amortisation, allocation, conversion | one document per cadence, plus one mid-cycle change | `equals` on document, period, amount; `empty` where the spread does not sum to the total |
| Exclusion rule | one row per predicate, one that matches none | `equals` on the key and the flag column |
| Dedup, unit or epoch conversion, placeholder nulls in staging | one duplicate group, a minor-unit amount, an epoch, a `"N/A"`, a lossy text value | `equals` on the source column beside the cast |
| Invariants the gate also checks | any of the above | `empty` on the `dup_key`, `null_required`, and `non_negative` shapes over the output |

A staging block that neither deduplicates nor converts has nothing to test; a wide table tests each rule it inlines. The domain file STATE.md names carries the cases its rules need. A fixture is small enough to read at a glance: one case per row, ids numbered in case order, the case list in the test's `description`. A fixture of hundreds of copied production rows is a second gate, not a test, and carries personal data into the test body ([collaboration-contract.md](collaboration-contract.md)).

## Fixture rules

- Inputs cover exactly the tables the transform reads: one for every source, none for a table it never reads; the run refuses a missing input and an unused one. A model that cross-joins `cfg_<domain>` declares it as an input, so the constant under test is visible in the test, and a second test runs the same model under the alternative value.
- `format: "rows"` by default: `columns` with the warehouse's own type names in `database_type` (a `CAST` target: `INTEGER`, `NUMERIC(12,2)`, `TIMESTAMP`, `VARCHAR(255)`), `rows` as objects, `null` where the source is null. `format: "sql"` builds a fixture a literal list would bloat: a calendar spine, a series of periods.
- The transform's SQL runs unchanged against the fixture, so every column it reads exists in the input with a type that casts and compares as the real column does; read the real types from `mb table get <id> --include fields`.
- Fixture dates sit at fixed points relative to the `last_complete_period` in the `cfg_<domain>` input, never relative to today, so the test does not rot; a rule that reads `current_date` (a freshness check) is exercised on rows the clock cannot reach or left to the gate.
- In the model's SQL, alias every source table and qualify columns by the alias (`FROM raw_billing.invoice i ... i.amount`), never by the table name: the rewrite to temp tables leaves a table-name qualifier dangling and the run refuses it. Same in expectation SQL.

## Expectations

- `equals`: the output holds exactly the declared rows over exactly the declared columns, as a multiset, order ignored. Columns not named are not compared, so name the key and the columns the rule decides; leave load timestamps out. `format: "rows"` with `columns` and `rows`, or `format: "sql"` when the expected rows are easier to state as a query over the inputs (the source sum per document, say).
- `empty`: a query that must return no rows, over the output named as the transform's target (`<out_schema>.<model>`; the run redirects it) or over a declared input, never a real table. The gate's `dup_key`, `null_required`, and `non_negative` branches wrapped so only violations return, or a rule stated as its violation: `SELECT * FROM analytics.mart_billing_fct_customer_month m WHERE m.state = 'churned' AND m.prior_mrr_usd = 0`.
- Names are unique within a test and name the rule, not the mechanism: `gap of exactly 1 month is retained`, `annual invoice spreads into 12 equal rows`.

Finished example, the test for a customer-month model under the gap rule (D7):

```json
{ "transform_id": 41, "name": "mart_billing_fct_customer_month: retention states",
  "description": "Cases: customer 1 new, retained, churned after a one-month gap, reactivation; customer 2 active through the last complete period, exit row in the partial period.",
  "inputs": [
    { "table": { "schema": "analytics", "name": "cfg_billing" }, "format": "rows",
      "columns": [ { "name": "gap_months", "database_type": "INTEGER" }, { "name": "last_complete_period", "database_type": "DATE" }, { "name": "cap_period", "database_type": "DATE" } ],
      "rows": [ { "gap_months": 1, "last_complete_period": "2026-07-01", "cap_period": "2026-08-01" } ] },
    { "table": { "schema": "analytics", "name": "int_billing_invoice_line_spread" }, "format": "rows",
      "columns": [ { "name": "customer_id", "database_type": "INTEGER" }, { "name": "revenue_month", "database_type": "DATE" }, { "name": "recognized_usd", "database_type": "NUMERIC(12,2)" } ],
      "rows": [ { "customer_id": 1, "revenue_month": "2026-05-01", "recognized_usd": 100 }, { "customer_id": 1, "revenue_month": "2026-06-01", "recognized_usd": 100 }, { "customer_id": 1, "revenue_month": "2026-08-01", "recognized_usd": 100 },
                { "customer_id": 2, "revenue_month": "2026-06-01", "recognized_usd": 50 }, { "customer_id": 2, "revenue_month": "2026-07-01", "recognized_usd": 50 } ] } ],
  "expectations": [
    { "type": "equals", "name": "one state per case", "format": "rows",
      "columns": [ { "name": "customer_id", "database_type": "INTEGER" }, { "name": "period_month", "database_type": "DATE" }, { "name": "state", "database_type": "VARCHAR(32)" } ],
      "rows": [ { "customer_id": 1, "period_month": "2026-05-01", "state": "new" }, { "customer_id": 1, "period_month": "2026-06-01", "state": "retained" }, { "customer_id": 1, "period_month": "2026-07-01", "state": "churned" }, { "customer_id": 1, "period_month": "2026-08-01", "state": "reactivation" },
                { "customer_id": 2, "period_month": "2026-06-01", "state": "new" }, { "customer_id": 2, "period_month": "2026-07-01", "state": "retained" }, { "customer_id": 2, "period_month": "2026-08-01", "state": "churned" } ] },
    { "type": "empty", "name": "churn only follows a positive month",
      "sql": "SELECT m.customer_id, m.period_month FROM analytics.mart_billing_fct_customer_month m WHERE m.state = 'churned' AND m.prior_mrr_usd = 0" } ] }
```

The body is closed: `transform_id`, `name`, `description`, `inputs`, `expectations`, nothing else; `update` replaces `inputs` and `expectations` whole. Commands, the run report keys, and the `get --full` round-trip: `mb skills path transform`, Read "Transform tests".

## Cadence

- Write the tests after `transform create` and before the first `transform run --sync`; a red expectation is fixed in the SQL file, patched, re-run; the model materialises only on green. Record the count and the result in the Models row `tests` column ([state.md](state.md)).
- After every source patch, the model's tests run before its gate. After a change to `cfg_<domain>`, every test in the domain's job runs (`mb transform-test list --transform <id>` per Models row).
- Changing a deployed model starts by running its tests as they stand. A new case: add the expectation, see it fail, fix, see it pass. A changed rule: the expectation's old and new rows are the change, shown in the hand-back and updated in the same patch, never deleted. A test that has to be deleted for a change to pass is a `[CHECKPOINT]`.
- In staging, tests export with their transforms on the job branch; the hand-back names them so the reviewer runs them before importing. In production, a red test never materialises.

## Reading a failure

`run` exits non-zero and `--json` says what each expectation found. A failed `equals`: `missing-rows` the rule did not produce, `extra-rows` it should not have, `cell-mismatches` per column when exactly one row differs on each side; a failed `empty`: `sample` holds the violating rows. `error` on one expectation is that expectation's own SQL failing; the others still report. A refusal names an authoring error: an input missing or unused, a column the output lacks, a table-name qualifier that survived the rewrite. A `422` is the transform itself failing on the fixture: fix the SQL, not the test. A fixture is edited only when it was wrong, and the hand-back says which; an expectation is never loosened to pass.

## Below v64, or outside Metabase

On an instance below v64 `mb transform-test` refuses; record `tests: unavailable` in STATE.md and prove each rule once through `q()`: the fixture as a `VALUES` CTE in place of the source in a copy of the model SQL, the expectation as a query over it, the result in the Models row `note`, the SQL kept in `./.scratch/<m>.test.sql` so it becomes the test after an upgrade. When transforms run in the company's own tool, the same cases go into that tool's test facility ([layering-and-naming.md](layering-and-naming.md), transformations that run outside Metabase).
