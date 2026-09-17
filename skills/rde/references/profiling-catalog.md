# Profiling catalog

Read before any modeling decision: naming a grain, writing a cast, choosing a join key, or agreeing a definition.

## Invariants

- Profile before designing: no table names, grains, or metric set until the tables on the path of a named question are profiled; a table on no path gets a row count and nothing more.
- Profile even when handed an implementation or documentation. Where a document disagrees with the data, the data wins; record the correction as a Decisions row ([state.md](state.md)) and build the corrected predicate.
- Warehouse unreachable: say so, record profiling as unavailable, never fabricate a distribution.
- Read raw and near-raw schemas plus what this build derived; state the split.
- Every decision carries its profiling evidence in its Decisions row.
- Never ask an open question profiling can turn into a confirmation: propose the mapping from the data and ask the user to correct rows.
- Sort results by materiality, not alphabetically. A join key is a hypothesis: state it, then show the match rate.

## Tools and limits

- Every probe runs through `q "<sql>"`, the helper in [state.md](state.md); it returns `status`, `error`, `cols`, and `rows`. Aggregate in the probe; never page rows through it.
- Bare-row queries return at most 2000 rows and aggregated queries at most 10,000. Both are admin settings; `--max-bytes 0` does not lift them. For a full extract create a native card, run `mb card query <id> --export-format csv`, then archive the card.
- `mb db get $DB --json` reports the engine. Write standard SQL and adapt to the warehouse dialect; on an engine that bills by scan, every probe carries a date predicate unless the decision needs the whole table.
- Column list per table: `mb table get <table-id> --include fields --json`, or `information_schema.columns` filtered by schema. Distribution of one column: `mb field summary <field-id> --json`.
- Loader detection: the loader-shape table in [staging-rules.md](staging-rules.md) reads the metadata columns present; whether the loader delivers duplicates is measured with the key-uniqueness probe, never assumed.

## Sampled replica and history horizon

1. Round row-count caps repeated across tables mean a sampled replica, usually skewed toward recent rows. List each truncated table, its cap, and the metric it blocks or degrades.
2. For every history, version, or change-log table record the earliest row; it bounds every point-in-time reconstruction, and two history tables routinely start on different dates.
3. Hunt for history sources before concluding none exist: `information_schema.tables` for names like `%_history`, `%_version`, `snap_%`; none found sends you to [entities-and-time.md](entities-and-time.md).

## Query catalog

Run the first three on every table on a question's path; the rest wherever the decision is not yet settled with evidence.

| Probe | Returns | Decides |
| --- | --- | --- |
| Row count per source table, one `UNION ALL` query for the schema | table, rows | Which tables exist and which are empty; an empty table on a question's path is a `[CHECKPOINT]` under the zero-row rule in [collaboration-contract.md](collaboration-contract.md) |
| Column inventory | name, type, nullability | The real column list ahead of any cast or rename |
| Key uniqueness | rows, distinct keys, null keys | Whether the declared key is the grain or dedup is required |
| Duplicate rate by candidate key | multi-row keys, worst offenders | Whether dedup is a rounding error or a structural rule |
| Foreign-key match rate | left rows, matched, unmatched, per path | Which relationships are real; below the confirmed floor is a checkpoint |
| Enum coverage | value, count, first and last seen | The mapping checklist; every non-zero value must map |
| Date field agreement | per status: rows, populated per candidate date, disagreements | Which date ends a lifecycle; a disagreement is a date-basis decision |
| Identifier domains and outliers | top email domains or name patterns; extreme child counts or lifetimes | Which rows are test, staff-owned, or demo |
| Trailing period completeness | rows and distinct entities per recent period | Whether the latest period is partial: the detectors in [modeling-decisions.md](modeling-decisions.md) |
| Baseline candidate discovery | tables named like the measure vocabulary, with row counts | Whether a reference exists ([reconciliation.md](reconciliation.md)); run before asking the user |
| Domain probes | per the domain file STATE.md names | The decisions that file lists under its Probes section |

## Probe shapes

Key uniqueness:

```sql
SELECT count(*) AS rows_total, count(DISTINCT order_id) AS keys_distinct, sum(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS key_nulls
FROM raw_acme.orders;
```

Enum coverage:

```sql
SELECT status, count(*) AS n, min(created_at) AS first_seen, max(created_at) AS last_seen
FROM raw_acme.orders GROUP BY 1 ORDER BY 2 DESC;
```

Foreign-key match rate, one query per path:

```sql
SELECT count(*) AS left_rows, count(c.customer_id) AS matched, count(*) - count(c.customer_id) AS unmatched
FROM raw_acme.orders o LEFT JOIN raw_acme.customers c ON c.customer_id = o.customer_id;
```

Date field agreement, per status, for two candidate end dates:

```sql
SELECT status, count(*) AS n, count(cancelled_at) AS has_cancelled_at, count(ended_at) AS has_ended_at,
       sum(CASE WHEN cancelled_at <> ended_at THEN 1 ELSE 0 END) AS disagree
FROM raw_acme.subscriptions GROUP BY 1 ORDER BY 2 DESC;
```

Trailing period completeness: the two detector queries in [modeling-decisions.md](modeling-decisions.md), run as written.

Close by writing each finding that caps a number (truncation, horizon, unit or currency, coverage gap, dedup need, text-typed timestamp, stale derived column) as its own Decisions row, so the check suite in [data-quality-checks.md](data-quality-checks.md) and every hand-back read from one list.
