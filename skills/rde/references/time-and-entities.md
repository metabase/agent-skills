# Time and entities

Read when a model has periods, the source keeps no history, two sources describe one thing, or a question needs a spine or fiscal calendar. Retention and cohorts: `references/methods/retention-and-cohorts.md`.

## Snapshot against flow

A point-in-time value (balance, active count, ending MRR) is valid in the partial current period and feeds every "current" headline. Flows (new customers, recognised revenue, churn) and every rate or period-over-period comparison read complete periods only. Never sum a snapshot across periods.

## The incomplete period

Emit the trailing partial period, flagged; never drop it. Every model with periods carries `is_complete_period`, derived from the data, never hand-set:

- The watermark is the latest time the source has fully loaded (max event time, or the loader's sync time when events arrive late) minus the measured lateness bound (a high percentile of `received_at − event time`).
- A period is complete once the watermark passes its end: last complete = `date_trunc('<unit>', <watermark> − <lateness>) − interval '1 <unit>'`, computed in the first model that materializes periods, or as a derived column of `cfg_<domain>` when several models read it.
- The table's description carries `required filters: is_complete_period for rates and trends`; its caveats name the partial period. Where people build questions in the query builder, a `Complete periods` segment makes it one click.
- A stale loader is a pipeline failure, not churn: freshness fails when `current_date − <watermark date>` exceeds a threshold from the load cadence, and the build stops ("the data has not arrived"). Never build on it; never move the boundary silently.
- Warning check: the newest complete period's rows or entities below 80 percent of the trailing average (only when the trailing twelve are steady, none below half the average) says the watermark lies.

Every hand-back with a periodic model says which period is last complete and why: "Rates and trends run through August; September is on the table, flagged incomplete, and only current-state headlines read it."

## Attributes that change: validity windows

Plan, tier, owner, segment join facts by validity window, never from the entity's current row:

```sql
FROM <out_schema>.orders o
LEFT JOIN <out_schema>.int_<domain>__plan_history h
  ON h.customer_id = o.customer_id AND o.ordered_at >= h.valid_from_at AND (h.valid_to_at IS NULL OR o.ordered_at < h.valid_to_at)
```

Half-open windows, null end on the open interval (never a far-future date), overlaps checked per key before the join, match rate after.

## History when the source keeps none

Look first (`references/profiling.md`, Samples and horizons). History cannot be backfilled, so capture starts in the first build session:

- `snap_<source>__<entity>`: an append incremental transform over the raw source, run daily by the job, one row per entity per `snapshot_date` with the key and the attributes whose past matters; a hard delete recorded with `deleted_at`.
- `int_<source>__<entity>_history`: one row per run of equal values, `valid_from_at = min(snapshot_date)`, `valid_to_at = lead(valid_from_at)` per entity, null when open.
- The first snapshot date is the horizon, in the caveats of every table and every hand-back that reads earlier periods (which carry current state). Meanwhile state the ceiling: which entities could have changed, their share of the measure, the periods affected.
- Never backfill by inference from current state or from a last-touched timestamp.

## Conformed entities

Two sources describing one thing (billing customer, app account, CRM company) get one entity table with one key and every source id as a column; every fact reaches it by that key, never by its own copy of an attribute.

1. Find the crosswalk before asking: an id naming the other side, a shared external id, a normalised email or domain.
2. Measure it with the match-rate probe: exact-match rate, unmatched share per side, duplicates per side. An id crosswalk passes at 98 percent matched (default to confirm; self-typed matches such as email take the domain note's threshold); below it, or any duplicate on the entity side, is a stop with counts and samples.
3. The key comes from the system that creates the entity; other ids ride along; the unmatched stay with null source columns and `is_matched_<source>`. The match rate goes in the hand-back.
4. Set `type/FK` with its target on every fact's conformed key, so breakouts reach the entity without a join or a copy.

On a mature instance a new source joins the existing entity keys.

## Dense entity-period spine

Only where movement states or retention need it: one row per entity per period, no gaps, so a missing period is a zero row. Built once per domain.

- Each entity from its first relevant period to one past its last, capped at the period containing the watermark (never `current_date`, so fixture tests do not rot); the period past the last active one is the exit row.
- Measures left-joined with `coalesce(<measure>, 0)`, the only place a measure is coalesced; carry `is_active`, the dominant attribute by value, `is_complete_period`.
- States by window functions (`lag`, running `sum(is_active)`), never a self-join; one state per entity-period, asserted.

## Calendars

Metabase buckets day through year itself; build no date table for those. One generic date spine per instance where a model must generate periods. A fiscal calendar comes from the ledger's own calendar table where one exists; otherwise a `calendar` table only for a fiscal year, a non-default week start, or holidays (`date`, `fiscal_year`, `fiscal_quarter`, `fiscal_period`, `week_start_date`, `is_holiday`), joined by time column; its fiscal columns are the breakouts.
