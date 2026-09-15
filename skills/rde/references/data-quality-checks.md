# Data quality checks

Read for every build that materialises a table.

## The eight checks, one query per model

Substitute `<model>`, `<source>`, `<key>`, the required-column list, the cast-column list, the non-negative measure list, `<entity>`, and `<period>`; each branch is a `model|check` key and a text value; the `-- pass:` comment is the rule. Sort client-side; a trailing `ORDER BY` binds to the last branch in several dialects. Run it through `q()` ([state.md](state.md)).

```sql
SELECT '<model>|dup_key' AS k, cast(count(*) AS varchar) AS v   -- pass: 0
  FROM (SELECT <key> FROM <model> GROUP BY 1 HAVING count(*) > 1) d
UNION ALL
SELECT '<model>|null_required', cast(sum(CASE WHEN <key> IS NULL OR <required_col> IS NULL OR <required_col> = '' THEN 1 ELSE 0 END) AS varchar)   -- pass: 0; keys, foreign keys, required timestamps, flags
  FROM <model>
UNION ALL
SELECT '<model>|cast_<col>', cast((SELECT count(<col>) FROM <source>) AS varchar) || '/' || cast((SELECT count(<col>) FROM <model>) AS varchar)   -- pass: equal; one branch per cast timestamp and numeric column
UNION ALL
SELECT '<model>|rows', cast(count(*) AS varchar) || '/' || cast((SELECT count(*) FROM <source>) AS varchar)   -- pass: equal, or the delta is a filter declared in the header; per source block on a joined model
  FROM <model>
UNION ALL
SELECT '<model>|grain', CASE WHEN count(*) = count(DISTINCT <key>) THEN 'true' ELSE 'false' END   -- pass: true; a composite grain is one materialised key column
  FROM <model>
UNION ALL
SELECT '<model>|non_negative_<amount>', CASE WHEN min(<amount>) >= 0 THEN 'true' ELSE 'false' END   -- pass: true; one branch per measure that cannot go below zero
  FROM <model>
UNION ALL
SELECT '<model>|period_flag', cast(count(*) AS varchar)   -- pass: 0; on the model that derives periods; a table with no entity groups by a constant
  FROM (SELECT <entity> FROM <model> GROUP BY 1
        HAVING sum(CASE WHEN is_complete_period THEN 0 ELSE 1 END) <> 1
            OR max(CASE WHEN is_complete_period THEN <period> END) > max(CASE WHEN NOT is_complete_period THEN <period> END)) p
UNION ALL
SELECT '<model>|enum_<mapped_col>', cast(sum(CASE WHEN <code_col> IS NOT NULL AND <mapped_col> IS NULL THEN 1 ELSE 0 END) AS varchar)   -- pass: 0; one branch per CASE over source values
  FROM <model>
```

A failed enum branch is a decision on the mapping, never a `coalesce`; make mappings total by construction (normalise, then bucket).

## Report shape and blocking rule

```
DQ: stg_acme_customer (slice: created_at >= 2026-08-01)
  OK    rows 10000/10000
  FAIL  cast_created_at 10000/9880
```

- Any `FAIL` blocks the next model: stop per [collaboration-contract.md](collaboration-contract.md) with the failing check, its value, and two or three sample rows. Never lower a threshold, widen a cast, or add a `coalesce` to turn a `FAIL` green.
- Join match rate is checked before a join is built, with the foreign-key probe in [profiling-catalog.md](profiling-catalog.md): matched and unmatched per candidate path; the floor is 98 percent matched, a default to confirm; below it is a `[CHECKPOINT]` with the unmatched count, share, and up to five sample rows.
- Results per model go in STATE.md's Checks table ([state.md](state.md)) at deploy.

## Cadence

- Slice first: prove the logic on a bounded predicate (a recent window or one entity) held in a comment-marked line of the model SQL; iterate until the shape and the eight checks pass on the slice; then remove the predicate, materialise, and run the eight on the whole table once.
- Staging: one query per layer, every model's branches in one block, after the layer lands. Intermediate and above: per model, before the next model starts.
- An incremental target is checked on the whole table after every run, never on the increment alone ([layering-and-naming.md](layering-and-naming.md)).

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

## Traps that carry a probe

| Trap | Symptom | Probe |
| --- | --- | --- |
| Stale header field | Parent column recomputed on a schedule or copied at creation | Compare to aggregated children; read the children |
| Mutable field used as history | Every past period carries today's value | Is the column overwritten in place? A history source, or a snapshot ([entities-and-time.md](entities-and-time.md)) |
| Period-to-date accumulator | Meter or quota resets each period | Plot per entity over time; never sum across time or rows |
| Units differ between systems | Whole units on one side, minor units on the other | Compare a matched row; normalise once in staging |
| Null versus zero | "no charge yet" coalesced with "a charge of zero" | Count each separately; never coalesce |
| Epoch units | Seconds, milliseconds, or microseconds | Convert one row and read the date |
| Ingestion offset | Warehouse copy lags the upstream date the metric keys on | Compare max upstream date to max load date |
| Retention cliff | Pruned table gives derived history a hard edge | Record pruned tables, column, schedule; earliest row per history table |
| Fan-out | Parent rows multiplied by a lines join | Rows before and after; pre-aggregate children, or count distinct on the parent key |
| Drop-out | Inner join to an optional child removes a subtype | Rows before and after; outer join |
| Orphans | Unenforced foreign keys leave children with no parent | The foreign-key match-rate probe |
| Non-customer rows | Test, staff-owned, demo, seeded catalogue rows | The identifier-domain probe; the exclusion rule in [state.md](state.md) |

## Checks that outlive the build

Per layer, save the structural checks as one native card in the data-quality collection that returns rows only on failure, and attach an alert that fires on any row, on the job's cadence. Hand back the card and the alert with the tables; fuller controls: [reconciliation.md](reconciliation.md).

The card: the `dup_key`, `null_required`, `non_negative`, and `period_flag` branches of every model in the layer as integer counts, plus freshness per driving table, wrapped so only failures return:

```sql
SELECT k, n FROM (
  SELECT '<model>|dup_key' AS k, count(*) AS n FROM (SELECT <key> FROM <model> GROUP BY 1 HAVING count(*) > 1) d
  UNION ALL
  SELECT '<model>|freshness', CASE WHEN current_date - cast(max(<loaded_at>) AS date) > <cadence_days> THEN 1 ELSE 0 END FROM <model>
  UNION ALL ...
) c WHERE n > 0
```

The alert, once `mb setting get 'email-configured?' --json` reports `true` (else stop: an admin configures it):

```json
{ "payload": { "card_id": <card-id>, "send_condition": "has_result", "send_once": false },
  "subscriptions": [{ "cron_schedule": "0 0 7 * * ? *" }],
  "handlers": [{ "channel_type": "channel/email", "recipients": [{ "type": "notification-recipient/raw-value", "details": { "value": "<owner email>" } }] }] }
```

`mb alert create --file ./.scratch/dq-alert.json --json`. The cron is seven-field Quartz in the instance's report timezone, set after the job's run; `mb alert send <id>` with yourself as the only recipient proves the channel, then add the owner by read-modify-write (`mb skills path notification`, the Updating section).
