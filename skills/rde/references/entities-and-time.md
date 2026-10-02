# Entities and time

Read when two sources describe one thing, when a model needs a period grid, when the source keeps no history, or when a question asks for retention, cohorts, or activation.

## Conforming an entity across sources

When two sources describe one thing, build one entity table with one key and every source id as a column; every fact reaches it by that key. Never widen each fact with its own copy of the attribute.

1. Find the crosswalk before asking: an id column on one side naming the other, a shared external id, a normalised email or domain (email rules in [domains/event-and-registration-data.md](domains/event-and-registration-data.md)).
2. Measure it with the foreign-key match-rate probe in [profiling-catalog.md](profiling-catalog.md): exact-match rate, unmatched share per side, duplicates per side. A crosswalk on ids passes at 98 percent matched (a default to confirm); below it, or any duplicate on the entity side, stops with the counts and sample rows.
3. Decide the key: the id from the system that creates the entity, stable and never reused; the other ids ride along as columns. The key choice and the fate of the unmatched (kept, source columns null, never dropped) are decisions per [collaboration-contract.md](collaboration-contract.md).
4. Build `<entity>` in the final layer: one row per entity, the key, every source id, the attributes people filter by, and `is_matched_<source>` per source.
5. Set the foreign key in metadata on every fact's conformed key column (`type/FK` with the target, [semantic-layer-design.md](semantic-layer-design.md)), so a breakout reaches the entity without a join and without a copy.

An attribute that changes over time (plan, tier, owner, segment) is joined by validity window ([modeling-decisions.md](modeling-decisions.md)), never copied from the entity's current row onto past facts.

## Calendar

Metabase buckets time itself; no date table is built for day, week, month, quarter, or year. Build a `calendar` table, one row per date, only when the company has a fiscal year, a non-default week start, or holiday rules: `date`, `fiscal_year`, `fiscal_quarter`, `fiscal_period`, `week_start_date`, `is_holiday`, and `is_complete_period` read from the constant in [modeling-decisions.md](modeling-decisions.md). Every periodic table joins it by its time column; the fiscal columns are the breakouts, and no question computes a fiscal period itself.

## History when the source keeps none

When the source overwrites attributes in place and keeps no change log, hunt for history sources first ([profiling-catalog.md](profiling-catalog.md)); then state the ceiling: which entities' attributes could have changed, the share of the measure they carry, and which periods are affected. Offer the two ways forward: current-state labelling, said on the model, or capturing history from now on:

- Build `snap_<source>_<entity>`: an append incremental transform (`target.type: "table-incremental"`, `target-incremental-strategy: {"type": "append"}`; body shape under Materialization in [layering-and-naming.md](layering-and-naming.md)), run daily by the job, one row per entity per `snapshot_date`, carrying the key and the attributes whose past values matter.
- Derive `int_<source>_<entity>_history` from it: one row per entity per run of equal attribute values, `valid_from_at = min(snapshot_date)`, `valid_to_at = lead(valid_from_at)` per entity, null on the open interval. Join it with the validity-window shape in [modeling-decisions.md](modeling-decisions.md).
- The first snapshot date is the history horizon. Every period before it carries current state; the model description, the metric description, and every hand-back say so, and a metric over those periods carries the label.
- Never backfill history by inference from current state, and never from a timestamp that only says when a row was last touched.

Snapshots for restatement detection use the same transform shape, one row per entity, period, and snapshot date ([reconciliation.md](reconciliation.md)).

## Dense entity-period spine

A spine is one row per entity per period with no gaps, so a missing period is a zero row and not a missing row. Build it once per domain; every state, motion, and retention table reads it.

- Periods: from the earliest period any entity is relevant to `cap_period`, taken from the source's distinct periods or the `calendar` table, generated in one model only.
- Bounds per entity: from its first relevant period to `min(<its last relevant period> + 1, cap_period)`, never the maximum date present; the one period past the last active one is the synthetic zero row a state machine reads as the exit.
- `cap_period = min(<latest period the model can legitimately produce>, <current period>)`, defined once in `cfg_<domain>`: the first term removes rows that forward-looking logic dates past today, the second keeps the partial current period, flagged by `is_complete_period` ([modeling-decisions.md](modeling-decisions.md)).
- Left-join the measures onto the spine with `coalesce(<measure>, 0)`, the one place a measure is coalesced; carry `is_active` (measure above zero, or an activity row in the period), the dominant attribute for the period by value with its rank, and `is_complete_period`.
- Assert one row per entity per period and the period-flag rule. The subscription-revenue spine is this spine with the domain's measure ([domains/subscription-revenue.md](domains/subscription-revenue.md)).

## Retention and cohorts

Every retention number is one shape with four parameters: the entity, the activity column that makes an entity active in a period (`is_active`, a paid invoice, a gift, a milestone event), the base period, and the follow period. Fix the basis (month over month or year over year), expose the other, record which the headline uses; year over year needs two complete years of history.

- Base set: entities active in the base period. Follow set: those of them active in the follow period.
- Logo retention: follow set over base set. Logo churn: one minus it.
- Value retention: net is the follow period's value of the base set over the base set's base value; gross caps each entity at its base value (`least(follow_value, base_value)`) before summing.
- Cohort: entities grouped by their first active period; a cohort table is one row per cohort per periods since, with the denominator fixed at the cohort's size.

```sql
SELECT b.period AS base_period, count(DISTINCT b.entity_id) AS base_n, count(DISTINCT f.entity_id) AS retained_n
FROM spine b
LEFT JOIN spine f ON f.entity_id = b.entity_id AND f.period = <b.period plus the follow offset> AND f.is_active
WHERE b.is_active AND b.is_complete_period AND <the follow period is complete>
GROUP BY 1;
```

States per entity-period from the spine with window functions, never a self-join: `lag(is_active)` and a running `sum(is_active)` per entity by period tell a first activation from a return. First match wins: active now, not before, never active: `new`; active now, not before, active earlier: `reactivated`; not active now, active before: `churned`; not active now: `inactive`; otherwise `retained`. One state per entity-period, asserted.

- Reactivation gap: a lapse of one period is churn followed by reactivation, the default; a longer grace period before churn is a named constant in `cfg_<domain>` the owner confirms, and the entity stays `retained` through the grace.
- A shift of plan, tier, product, or fund is a move, not churn: declare the pairs, flag them, keep them out of churn counts; a cancel-then-create pair during a migration is the same false pair.
- The subscription-revenue state machine (upgrade, downgrade, expansion, contraction on top of these states) is the special case in [domains/subscription-revenue.md](domains/subscription-revenue.md).
- Activation is a cohort measure: the cohort by signup period, the milestone event within a window as the activity column; the event and the window are defined in [domains/product-usage-events.md](domains/product-usage-events.md).

Every rate reads complete periods only, per the flagged-period rule in [modeling-decisions.md](modeling-decisions.md).
