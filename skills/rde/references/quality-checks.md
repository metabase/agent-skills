# Quality checks

Read for every build that materializes a table. The gate checks the data that landed; the model's rules are pinned first, on fixtures, by its tests (`references/transform-tests.md`). A failure on a case a test covers means the fixture did not match the source; a failure on an uncovered case becomes a fixture row before the SQL is fixed.

## The gate

Read the domain note's Invariants first: each becomes a check or a test.

| Check | Applies | Pass | On failure |
| --- | --- | --- | --- |
| `dup_key` | every model | 0 | blocks |
| `null_required` | key, foreign keys, required timestamps, flags | 0 | blocks |
| `row_parity` | only a model 1:1 with its source (per source block of a wide model) | equal, or the delta is a filter `scope:` declares | blocks |
| `cast_<col>` | every lossy cast | non-nulls before = after | blocks |
| `freshness` | driving sources | watermark within the load cadence | blocks: the data has not arrived |
| `period_flag` | models with periods | at most one incomplete period per entity, the newest | blocks |
| `roll_forward` | movement tables | opening + movements = closing per entity and period | blocks: a build bug |
| `enum_<col>` | mappings over source values | 0 unmapped codes | a decision on the mapping, never a `coalesce` |
| `non_negative_<col>` | measures that cannot go negative (a measure `scope:` declares signed, such as refunds or credits, is exempt) | 0 | blocks |
| `relationship_<fk>` | foreign keys | at or above the profiled baseline | reported below it; a stop below the agreed floor |

Never lower a threshold, widen a cast, or `coalesce` a failure green; make mappings total by construction (normalise, then bucket). A blocking failure stops the chain with the check, its value, and two or three sample rows.

One query per model through `q()`; each branch returns a `model|check` key and a text value, sorted client-side (a trailing `ORDER BY` binds to the last branch in several dialects):

```sql
SELECT '<model>|dup_key' AS k, cast(count(*) AS varchar) AS v FROM (SELECT m.<key> FROM <out_schema>.<model> m GROUP BY 1 HAVING count(*) > 1) d
UNION ALL SELECT '<model>|null_required', cast(sum(CASE WHEN m.<key> IS NULL OR m.<required_col> IS NULL THEN 1 ELSE 0 END) AS varchar) FROM <out_schema>.<model> m
UNION ALL SELECT '<model>|row_parity', cast((SELECT count(*) FROM <out_schema>.<model>) AS varchar) || '/' || cast((SELECT count(*) FROM <raw_schema>.<source>) AS varchar)
UNION ALL SELECT '<model>|cast_<col>', cast((SELECT count(s.<raw_col>) FROM <raw_schema>.<source> s) AS varchar) || '/' || cast((SELECT count(m.<col>) FROM <out_schema>.<model> m) AS varchar)
UNION ALL SELECT '<model>|period_flag', cast(count(*) AS varchar) FROM (SELECT m.<entity> FROM <out_schema>.<model> m GROUP BY 1
  HAVING sum(CASE WHEN m.is_complete_period THEN 0 ELSE 1 END) > 1
      OR max(CASE WHEN m.is_complete_period THEN m.<period> END) > max(CASE WHEN NOT m.is_complete_period THEN m.<period> END)) p
UNION ALL SELECT '<model>|enum_<mapped>', cast(sum(CASE WHEN m.<code> IS NOT NULL AND m.<mapped> IS NULL THEN 1 ELSE 0 END) AS varchar) FROM <out_schema>.<model> m
UNION ALL SELECT '<model>|non_negative_<col>', cast(sum(CASE WHEN m.<col> < 0 THEN 1 ELSE 0 END) AS varchar) FROM <out_schema>.<model> m
```

A table with no entity groups the period check by a constant. Results go in the state file's build list.

## Cadence

- Slice first (build §3), then the whole table once.
- Staging: one query per layer after it lands. Intermediate and final: per model, before the next starts. Incremental: the whole table after every run.
- Before a join is built: the match-rate probe per candidate path, against the floor in `references/time-and-entities.md`, Conformed entities; below it, a stop with unmatched count, share, and up to five samples.

## Beyond structure

Structure proves well-formed, not right. Report these as their own block; the first four are also test expectations.

| Check | Catches |
| --- | --- |
| Derived measure summed back to the source, per class | a class in the wrong bucket after spreading, allocation, or conversion |
| Derived-to-source ratio per class | the long tail outside a tight cluster |
| A derived count against its theoretical ceiling | a bug, or a business fact worth reporting |
| Impossible values: negative amounts or counts, shares over 100%, dates past the horizon | arithmetic and horizon errors |
| Row count per class of a new classification, shown to the user | misbehaving logic |
| One real entity traced from raw rows through every layer | join and ordering bugs no aggregate shows |
| One headline against an independent figure (`playbooks/reconcile.md`) | what self-consistency cannot see |

## Traps worth a probe

| Trap | Symptom | Probe |
| --- | --- | --- |
| Stale header field | parent column recomputed on a schedule or copied at creation | compare to aggregated children |
| Mutable field used as history | every past period carries today's value | is it overwritten in place? find history or snapshot |
| Period-to-date accumulator | a meter resets each period | plot per entity; never sum across periods |
| Units differ between systems | whole units vs minor units | compare one matched row; normalise in staging |
| Null vs zero | "no charge yet" merged with "zero charge" | count apart; never coalesce |
| Epoch units | seconds, ms, or µs | convert one row, read the date |
| Ingestion offset | the copy lags the upstream date the metric keys on | max upstream date vs max load date |
| Retention cliff | a pruned table gives history a hard edge | record pruned tables and earliest rows |
| Fan-out | parents multiplied by a lines join | rows before and after; pre-aggregate children or count distinct parents |
| Drop-out | an inner join to an optional child drops a subtype | rows before and after; outer join |
| Orphans | unenforced FKs leave parentless children | the match-rate probe |
| Non-customer rows | test, staff, demo, seeded rows | identifier domains; the exclusion flag |

## The standing check

Per domain, one saved native question returning rows only on failure, with an alert on the job's cadence; fuller controls in `references/reconciliation.md`. It holds the key, required, non-negative, relationship, and roll-forward branches of every model as integer counts, plus freshness per driving table:

```sql
SELECT c.k, c.n FROM (
  SELECT '<model>|dup_key' AS k, count(*) AS n FROM (SELECT m.<key> FROM <out_schema>.<model> m GROUP BY 1 HAVING count(*) > 1) d
  UNION ALL SELECT '<model>|freshness', CASE WHEN current_date - cast(max(m.<loaded_at>) AS date) > <cadence_days> THEN 1 ELSE 0 END FROM <out_schema>.<model> m
  UNION ALL ...
) c WHERE c.n > 0
```

Save it with `mb card create` (native, `display: "table"`, the domain's data-quality collection). Alert once `mb setting get 'email-configured?'` is `true` (else a stop for the admin):

```json
{"payload": {"card_id": <check-card-id>, "send_condition": "has_result", "send_once": false},
 "subscriptions": [{"cron_schedule": "<7-field Quartz cron after the job's run>"}],
 "handlers": [{"channel_type": "channel/email", "recipients": [{"type": "notification-recipient/raw-value", "details": {"value": "<your address>"}}]}]}
```

`mb alert create --file …`, `mb alert send <alert-id>` to yourself to prove the channel; add the owner only after a stop confirming recipients, by read-modify-write (list fields replace whole). Mechanics: `notification` skill, Alerts and Updating.
