# Transform tests

Read before the first model that carries a rule, and before changing a deployed one. Tests need three things: the endpoint on the instance (v65 and later, and any head or EE build of master), the `transforms-testing` feature on its token, and a warehouse driver that supports testing (Postgres, MySQL/MariaDB, Redshift, ClickHouse, SQL Server, H2 — not Snowflake, not BigQuery). Establish that by running the command, never by reading a version tag: a dev or head build reports `vLOCAL_DEV` or a `-SNAPSHOT` tag that the CLI cannot parse, so it logs an unknown-version warning and proceeds, and an agent that gates on the tag itself would drop a working instance into the fallback. The fallback, and the three signals that call for it, are at the end. `mb transform-test` does not ship in the CLI's `latest` tag yet: if `mb transform-test --help` is unknown, install `@metabase/cli@alpha-transform-tests` — and if it refuses a `cast_type` column, the CLI predates the rename and needs the same upgrade.

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

- Inputs cover exactly the tables the transform reads: one for every source, none for a table it never reads, and never two for the same table. The declared set has to equal the read set, and `create` and `update` refuse the body before anything runs — a missing input would leave that read pointing at the real table and pass green on production data. A model that cross-joins `cfg_<domain>` declares it as an input, so the constant under test is visible in the test, and a second test runs the same model under the alternative value.
- `format: "rows"` by default: `columns` as `{name, cast_type}`, `rows` as objects, `null` where the source is null. Every row carries exactly the declared columns — a key that names no column, or a column a row omits, is refused; a column whose value is null is still present as a key. An empty `rows` list is legal and stands for a source table with no rows, which is a case worth pinning. `format: "sql"` builds a fixture a literal list would bloat: a calendar spine, a series of periods.
- `cast_type` is a `CAST` target, not the type the warehouse reports, and the two vocabularies diverge per engine: MySQL takes `SIGNED` and reports `BIGINT`, ClickHouse takes `Nullable(Int32)` where the column reads back as `Int64`. Never copy a `database_type` out of a run result into a `cast_type`, and expect a body to be warehouse-specific. It is not checked when the test is saved; the database refuses it at run time, as `setup-failed`.
- The transform's SQL runs unchanged against the fixture, so every column it reads exists in the input with a type that casts and compares as the real column does; read the real types from `mb table get <id> --include fields`, then write the cast target the engine takes for each.
- Fixture dates sit at fixed points relative to the `last_complete_period` in the `cfg_<domain>` input, never relative to today, so the test does not rot; a rule that reads `current_date` (a freshness check) is exercised on rows the clock cannot reach or left to the gate.
- In the model's SQL, alias every source table and qualify columns by the alias (`FROM raw_billing.invoice i ... i.amount`), never by the table name: the rewrite to temp tables leaves a table-name qualifier dangling and the run refuses it. Same in expectation SQL.

## Expectations

- `equals`: the output holds exactly the declared rows over exactly the declared columns, as a multiset, order ignored. Columns not named are not compared, so name the key and the columns the rule decides; leave load timestamps out. `format: "rows"` with `columns` (`{name, cast_type}`) and `rows` — the only form that runs. `format: "sql"` on an `equals` is accepted when saved and refused when run (`transform-test.unsupported-format`, 501): state the expected rows literally, or restate the rule as an `empty` over its violation.
- `empty`: a query that must return no rows. It may name only the transform's target (`<out_schema>.<model>`; the run redirects it to the output temp table) and the test's declared inputs — every other table is left exactly as written and reads the real one, so the run refuses it (`transform-test.unremapped-reference`) rather than letting a test touch production. The gate's `dup_key`, `null_required`, and `non_negative` branches wrapped so only violations return, or a rule stated as its violation: `SELECT * FROM analytics.mart_billing_fct_customer_month m WHERE m.state = 'churned' AND m.prior_mrr_usd = 0`.
- Names are unique within a test, case-sensitively, and name the rule, not the mechanism: `gap of exactly 1 month is retained`, `annual invoice spreads into 12 equal rows`.

Finished example, the test for a customer-month model under the gap rule (D7):

```json
{ "transform_id": 41, "name": "mart_billing_fct_customer_month: retention states",
  "description": "Cases: customer 1 new, retained, churned after a one-month gap, reactivation; customer 2 active through the last complete period, exit row in the partial period.",
  "inputs": [
    { "table": { "schema": "analytics", "name": "cfg_billing" }, "format": "rows",
      "columns": [ { "name": "gap_months", "cast_type": "INTEGER" }, { "name": "last_complete_period", "cast_type": "DATE" }, { "name": "cap_period", "cast_type": "DATE" } ],
      "rows": [ { "gap_months": 1, "last_complete_period": "2026-07-01", "cap_period": "2026-08-01" } ] },
    { "table": { "schema": "analytics", "name": "int_billing_invoice_line_spread" }, "format": "rows",
      "columns": [ { "name": "customer_id", "cast_type": "INTEGER" }, { "name": "revenue_month", "cast_type": "DATE" }, { "name": "recognized_usd", "cast_type": "NUMERIC(12,2)" } ],
      "rows": [ { "customer_id": 1, "revenue_month": "2026-05-01", "recognized_usd": 100 }, { "customer_id": 1, "revenue_month": "2026-06-01", "recognized_usd": 100 }, { "customer_id": 1, "revenue_month": "2026-08-01", "recognized_usd": 100 },
                { "customer_id": 2, "revenue_month": "2026-06-01", "recognized_usd": 50 }, { "customer_id": 2, "revenue_month": "2026-07-01", "recognized_usd": 50 } ] } ],
  "expectations": [
    { "type": "equals", "name": "one state per case", "format": "rows",
      "columns": [ { "name": "customer_id", "cast_type": "INTEGER" }, { "name": "period_month", "cast_type": "DATE" }, { "name": "state", "cast_type": "VARCHAR(32)" } ],
      "rows": [ { "customer_id": 1, "period_month": "2026-05-01", "state": "new" }, { "customer_id": 1, "period_month": "2026-06-01", "state": "retained" }, { "customer_id": 1, "period_month": "2026-07-01", "state": "churned" }, { "customer_id": 1, "period_month": "2026-08-01", "state": "reactivation" },
                { "customer_id": 2, "period_month": "2026-06-01", "state": "new" }, { "customer_id": 2, "period_month": "2026-07-01", "state": "retained" }, { "customer_id": 2, "period_month": "2026-08-01", "state": "churned" } ] },
    { "type": "empty", "name": "churn only follows a positive month",
      "sql": "SELECT m.customer_id, m.period_month FROM analytics.mart_billing_fct_customer_month m WHERE m.state = 'churned' AND m.prior_mrr_usd = 0" } ] }
```

The body is closed: `transform_id`, `name`, `description`, `inputs`, `expectations`, nothing else; `update` replaces `inputs` and `expectations` whole, and re-validates the whole test against the transform. Strip `id`, `entity_id`, `creator_id`, `created_at`, and `updated_at` from a `get --full` body before sending it back. Commands, the run report keys, and the `get --full` round-trip: `mb skills path transform`, Read "Transform tests".

## Cadence

- Write the tests after `transform create` and before the first `transform run --sync`; `transform-test create` already refuses a test whose inputs do not match what the SQL reads, so a clean create means the declaration is right and only the rules are still in question. A red expectation is fixed in the SQL file, patched, re-run; the model materialises only on green. Record the count and the result in the Models row `tests` column ([state.md](state.md)).
- After every source patch, the model's tests run before its gate. After a change to `cfg_<domain>`, every test in the domain's job runs (`mb transform-test list --transform <id>` per Models row).
- Changing a deployed model starts by running its tests as they stand. A new case: add the expectation, see it fail, fix, see it pass. A changed rule: the expectation's old and new rows are the change, shown in the hand-back and updated in the same patch, never deleted. A test that has to be deleted for a change to pass is a `[CHECKPOINT]`.
- Renaming or dropping a source table breaks the input declaration, so `update` on the test comes in the same patch as the SQL: a stale input is an `unused-inputs` refusal, not a silent pass.
- In staging, tests export with their transforms on the job branch; the hand-back names them so the reviewer runs them before importing. In production, a red test never materialises.

## Reading a failure

Separate the three outcomes; they mean different things and only one of them is a bug in the model.

**A refusal** — `create`, `update`, or `run` returns a non-2xx with an `error-code` of the form `transform-test.<name>`. Switch on the code, not the prose. `400` is the test's own authoring: `missing-inputs` (a table the SQL reads with no input), `unused-inputs` (an input for a table it never reads), `duplicate-input-table` (two inputs a reference cannot tell apart — the same table twice, or once bare and once in the default schema; names are compared case-agnostically), `unremapped-reference` (a real table or a dangling table-name qualifier survived the rewrite, in the transform or in a named expectation — alias and qualify by the alias), `unparseable-source`, `unknown-column` and `ambiguous-column` (an `equals` naming a column the output does not have, or one that matches several case aside). `422` means the test is fine and the run cannot happen here: `unsupported-transform` (a Python transform), `unsupported-driver` (Snowflake, BigQuery, anything else without the feature), `transform-failed` (the transform itself would not run on the fixture — fix the SQL, not the test), `setup-failed` (an input could not be materialized, usually a `cast_type` the engine rejects). `501` is `unsupported-format`, today only `equals` with `format: "sql"`.

**A run that happened** — `200`, and `run` exits non-zero unless it passed. The report is `{status, expectations, tables}`, `status` one of `passed` or `failed`, and `tables` mapping each temp table to the table it stood in for. Every expectation reports `{name, type, status}`; table names in any message are rewritten back to the names you wrote.

- A failed `equals`: `missing-rows` the rule did not produce, `extra-rows` it should not have, `row-counts` as `{actual, expected}`, and `cell-mismatches` per column — filled only when exactly one row is missing and exactly one is extra, since any larger diff has no honest pairing. These keys are present on a pass too, empty; `columns` reports each declared column with the `database_type` the output actually has, which is how you learn the cast target you should have written. `truncated` counts rows the 50-row report cap dropped. A decimal comes back as a string at the scale the warehouse gave it, so `"1.50"` against `"1.5"` is a scale difference, not a value one.
- A failed `empty`: `sample` holds the violating rows, `columns` describes them, `truncated` counts what the cap dropped.
- `status: "error"` on one expectation is that expectation's own SQL failing; `error` is `{type, message}` and the others still report.

**A run that never came back** — runs are tracked, and one whose process stops heartbeating is reaped as `timeout` after five minutes. Re-run it; a repeat means the fixture is too large to be a test.

A fixture is edited only when it was wrong, and the hand-back says which; an expectation is never loosened to pass.

## When tests cannot run

Three answers from the instance itself, not from its version string, send you here: `mb transform-test` is an unknown command and the CLI cannot be upgraded, a `402` says the token lacks `transforms-testing`, or a `422 transform-test.unsupported-driver` says the warehouse is one that cannot run tests (Snowflake and BigQuery today). Record `tests: unavailable` in STATE.md with which of the three it was, and prove each rule once through `q()`: the fixture as a `VALUES` CTE in place of the source in a copy of the model SQL, the expectation as a query over it, the result in the Models row `note`, the SQL kept in `./.scratch/<m>.test.sql` so it becomes the test once the block lifts. When transforms run in the company's own tool, the same cases go into that tool's test facility ([layering-and-naming.md](layering-and-naming.md), transformations that run outside Metabase).
