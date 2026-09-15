# Data quality checks

Read this for every build that materialises a table.

## The suite, all eight after every model, before the next one starts

| Check | Query shape | Pass |
| --- | --- | --- |
| Duplicates on the declared key | `SELECT key FROM <model> GROUP BY 1 HAVING count(*) > 1`, as a count of keys; a composite grain gets a materialised concatenated key | 0 |
| Nulls in must-not-be-null columns | Keys, foreign keys, required timestamps, flags; where a text join miss is `''`, test `col IS NULL OR col = ''` | 0 |
| No cast failures | Source versus model non-null count per timestamp and numeric column, reported as the pair | Equal |
| Row-count parity | `<model_rows>/<source_rows>`; for a joined wide model, per source block, or on the driving table | Equal, or the delta is explained by a filter declared in the report |
| Grain assertion | `count(*) = count(DISTINCT key)` on every model | True |
| Non-negative amounts | `min(amount) >= 0` on every measure the business says cannot go below zero | True; a negative is a build error |
| No rows in the incomplete trailing period | `max(period) <= <last complete period>`, asserted in the model that derives periods ([modeling-decisions.md](modeling-decisions.md)) | True |
| Enum coverage | For every CASE over source values: null outputs where the source value was non-null | 0; the fix is a checkpoint on the mapping, never a `coalesce` |

Make mappings total by construction (normalise, then bucket).

## One query per layer

Each check is a `model|check` key and a text value, `UNION ALL`ed. Sort client-side; a trailing `ORDER BY` binds to the last branch in several dialects.

```sql
SELECT 'stg_acme_order|dup_pk' AS k, cast(count(*) AS varchar) AS v
  FROM (SELECT order_id FROM stg_acme_order GROUP BY 1 HAVING count(*) > 1) d
UNION ALL
SELECT 'stg_acme_order|rows', cast(count(*) AS varchar) || '/' || '<source_rows>' FROM stg_acme_order
```

## Report shape and blocking rule

```
DQ: stg_customer
  OK    Rows: 10000/10000
  FAIL  Cast errors in created_at: source 0 nulls -> model 120 nulls
```

- Any `FAIL` blocks the next model: checkpoint ([collaboration-contract.md](collaboration-contract.md)) with the failing check, its value, and two or three sample rows. Never lower a threshold, widen a cast, or add a `coalesce` to turn a `FAIL` green.
- Join match rate is checked before building: count matched and unmatched per candidate path, propose a floor as a default the user confirms, and checkpoint anything below it with the unmatched count, share, and up to five sample rows. Name a number, never "a significant portion".

## Semantic checks structural checks cannot replace

Report these as their own block.

| Check | Catches |
| --- | --- |
| Sum the derived measure, multiply back by the classifier's factor, compare to the source sum per class | A whole class in the wrong bucket after amortisation, allocation, or conversion |
| Ratio of derived to source per class | The long tail outside a tight cluster |
| Derived count against its theoretical ceiling: the population that could not qualify | A bug, or a business fact worth reporting |
| Values a measure must never take: negative amounts or counts, shares over 100 percent, dates past the horizon | Arithmetic and horizon errors |
| Row count per class of any new classification, shown to the user | Logic that misbehaves |
| One entity with real history traced from raw rows through every layer to the final number | Join and ordering bugs no aggregate reveals |
| One headline number against an independent figure for one period ([reconciliation.md](reconciliation.md)) | Errors self-consistency cannot see |
| The model's own declared identities, with a violation count, labelled structural | The arithmetic failing to close; not whether the figures are right |

## Traps catalogue

Ask each of every column, table, and join.

| Trap | Symptom | Probe |
| --- | --- | --- |
| Stale header field | Parent column recomputed on a schedule or copied at creation | Compare to aggregated children; read the children |
| Mutable field used as history | Every past period carries today's value | Is the column overwritten in place? Use a history source |
| Period-to-date accumulator | Meter or quota resets each period | Plot per entity over time; never sum across time or rows |
| One column, several meanings | `value` is a level for some types, a count for others | Group by the type column before aggregating |
| Units differ between systems | Whole units on one side, minor units on the other | Compare a matched row; normalise once in staging |
| Stored derived column | Computed daily, floored at zero, blank when unreported | Recompute from inputs and compare |
| Creation timestamp is not acquisition | Rows claimed from a pre-created pool keep its timestamp | Who creates the row, and what re-points it later? |
| Null versus zero | "no charge yet" coalesced with "a charge of zero" | Count each separately; never coalesce |
| Epoch units | Seconds, milliseconds, or microseconds | Convert one row and read the date |
| Mixed timezone awareness | Aware and naive columns shift differently under a reporting zone | Enumerate naive columns; normalise in staging |
| Modification timestamp as watermark | Hot paths write around the application | Prefer the domain timestamp or a change log |
| Day and period boundaries | Date columns carry no timezone; timestamps pinned to a fixed time | Write down whether a period includes its end, and effective versus entry date |
| Ingestion offset | Warehouse copy lags the upstream date the metric keys on | Compare max upstream date to max load date |
| Current-state table as history | Past periods unrecoverable | Version, snapshot, or change-log tables, or say none exist |
| Change log versus version table | A change log carries deletes; a trigger snapshot usually does not | Pick the one matching the question |
| History horizon | Change capture starts on a date | Record the earliest row per history table |
| Retention cliff | Pruned table gives derived history a hard edge | Record pruned tables, column, schedule |
| Filtered subset as full table | A view or load filter already narrowed it | Compare count and date range to the entity it claims |
| Soft deletes in several dialects | Deleted-at here, a status there, hard deletes elsewhere | Enumerate the dialect per table; filter accordingly |
| Re-delivered rows | Loader repeats rows | Dedup by key on the sync column; measure whether needed |
| Missing rows are not zeros | A gap period has no row | "No row" is a third state; flag, never impute |
| Case-insensitive collation | Merged in the source, split downstream | Distinct counts with and without `lower()` |
| Fan-out | Parent rows multiplied by a lines join | Pre-aggregate children, or count distinct on the parent key |
| Drop-out | Inner join to an optional child removes a subtype | Outer join; never assume one-to-one |
| Unenforced foreign keys | Orphan children | Match-rate probe |
| Mutually exclusive parent links | Each line links to one of two parents | Union both paths |
| Consumer-domain join keys | Email or name at a shared domain merges and splits people | Immutable id, else the coarser grain, and say so |
| Multi-parent ambiguity | No single child attribute at parent grain | Explicit attribution rule ([modeling-decisions.md](modeling-decisions.md)) |
| Zero-row table | Empty source | The zero-row rule in [collaboration-contract.md](collaboration-contract.md), never a silent skip |
| Sampled replica | Round row-count caps, skewed in time | Caveat every published number, or repoint at full data |
| Non-customer rows | Test, staff-owned, demo, seeded catalogue rows | Exclusion rule table ([ledgers-and-artifacts.md](ledgers-and-artifacts.md)) |
| Infrastructure tables | Schedulers, migration ledgers, request logs, feature flags, placeholder-amount rows | No business metrics on them |
| Terminal-looking status that is not | Pending cancellation still serving | Per-metric status mapping, written down, never inferred from the name |
