# Profiling catalog

Read this before any modeling decision: naming a grain, writing a cast, choosing a join key, or agreeing a metric definition.

## Invariants

- Profile before designing. No table names, grains, or metric set until the inventory is filled.
- Profile even when handed an implementation or documentation. Where a document disagrees with the data, the data wins; record the correction in its own inventory section and build the corrected predicate.
- Warehouse unreachable: say so, record profiling as unavailable, never fabricate a distribution.
- Read raw and near-raw schemas only, plus derived schemas built in this piece of work; state the split.
- Every checkpoint (block in [collaboration-contract.md](collaboration-contract.md)) carries its profiling evidence, attached to the decision it resolves in the assumption ledger ([ledgers-and-artifacts.md](ledgers-and-artifacts.md)).
- Never ask an open question profiling can turn into a confirmation: propose the mapping from the data and ask the user to correct rows.
- Sort results by materiality, not alphabetically. A join key is a hypothesis: state it, then show the match rate.

## Tools and limits

- Probes run through `mb query` with a native body (`mb skills get core`).
- Bare-row queries return at most 2000 rows and aggregated queries at most 10,000. Both are admin settings; `--max-bytes 0` does not lift them. Write probes that aggregate. For a full extract create a native card, run `mb card query <id> --export-format csv`, then archive the card.
- `mb db get <id>` reports the engine. Write standard SQL and adapt to the warehouse dialect.

## Inventory record, one per table

| Field | Record |
| --- | --- |
| Rows | Count, and whether it is real or a cap; a round count is truncation |
| Grain | "one row per X" plus the column set proven unique |
| Role | Why this table is in the build |
| Key columns | The ones a metric reads |
| Timestamps | Each column with earliest and latest value |
| Join keys | Direction and match rate, e.g. `orders.customer_id` to `customer.id`, 9,940 of 10,000 matched |
| Null rate | Every key and timestamp column |
| Enum distributions | Every status-like column |
| Loader metadata columns | Which are present |
| Caveats | Unit traps, non-customer rows, history horizons, placeholder values |

## Read the real column list per table

```sql
SELECT table_name, column_name, data_type, is_nullable, ordinal_position
FROM information_schema.columns
WHERE table_schema = 'raw_acme'
ORDER BY table_name, ordinal_position;
```

Or via Metabase metadata:

```bash
mb table get <table-id> --include fields --json
mb field summary <field-id> --json
```

Loader detection from the metadata columns present, and the loader-shape rules: [staging-rules.md](staging-rules.md), How a loader shapes a table; whether the loader delivers duplicates is measured with the key-uniqueness probe below, never assumed.

## Sampled replica and history horizon

1. Round row-count caps repeated across tables mean a sampled replica, usually skewed toward recent rows. List each truncated table, its cap, and the metric it blocks or degrades.
2. For every history, version, or change-log table record the earliest row; it bounds every point-in-time reconstruction and time series, and two history tables routinely start on different dates.
3. Hunt for history sources before concluding none exist: `information_schema.tables` for names like `%_history`, `%_version`, `snap_%`.

## Query catalog

Run the first two always; the rest wherever the decision is not yet settled with evidence.

| Probe | Returns | Decides |
| --- | --- | --- |
| Row count per source table | table, rows | Which tables exist and which are empty; a zero-row table is a checkpoint under the zero-row rule in [collaboration-contract.md](collaboration-contract.md) |
| Column inventory | name, type, nullability | The real column list ahead of any cast or rename |
| Key uniqueness | rows, distinct keys, surplus | Whether the declared key is the grain or dedup is required |
| Duplicate rate by candidate key | multi-row keys, worst offenders | Whether dedup is a rounding error or a structural rule |
| Null rate per key column | null count and share | Whether a column can be a key, join target, or required field |
| Foreign-key match rate | left rows, unmatched, share, per path | Which relationships are real; below the confirmed floor is a checkpoint |
| Enum coverage | value, count, first and last seen | The mapping checklist; every non-zero value must map |
| Enum-pair coverage | pairs of two related enums, with counts | Coverage for a CASE over a pair; a missed pair is a silent null |
| Status by reason matrix | counts and amount sums per status and reason | Which states count toward a measure and which need an override |
| Unmapped child references | child rows with no lookup row, sample, amount | Whether real value flows through unclassifiable rows |
| Date field agreement | per status: rows, populated per candidate date, disagreements | Which date ends a lifecycle; disagreement means the user decides |
| Multi-child cardinality | child count distribution per parent | Whether a collapse-to-one rule is needed; where a join fans out |
| Identifier domains and outliers | top email domains or name patterns; extreme child counts or lifetimes | Which rows are test, staff-owned, or demo |
| Trailing period completeness | rows and distinct entities per recent period | Whether the latest period is partial and where the cap belongs |
| Baseline candidate discovery | tables named like the measure vocabulary, with row counts | Whether a baseline exists; run before asking the user |
| Domain-specific probes | per the domain file the router named | The decisions that file lists under Probes for this domain |

## Probe shapes

Key uniqueness, null keys, surplus:

```sql
SELECT count(*) AS rows_total,
       count(DISTINCT order_id) AS keys_distinct,
       sum(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS key_nulls
FROM raw_acme.orders;
```

## Questions never answered with a default

Each fails silently when guessed: the always-stop table in [collaboration-contract.md](collaboration-contract.md) and the period cap in [modeling-decisions.md](modeling-decisions.md); checkpoint with the profiled evidence and wait.

## Close with a data-quality register

Close the inventory with a numbered register, one loadable row per fact: truncation, missing tables, exclusion corrections, horizons, units and currency, coverage gaps, dedup needs, text-typed timestamps, stale derived columns, sourceless dimensions. It seeds the assumption ledger and the check suite in [data-quality-checks.md](data-quality-checks.md).
