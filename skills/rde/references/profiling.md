# Profiling

Read before any modeling decision: a grain, a cast, a join key, a definition.

## Rules

- No table names, grains, or metric set until every table on a named question's path is profiled; a table on no path gets a row count only.
- Profile even when handed documentation; where it disagrees with the data, the data wins and the correction is a decision.
- Warehouse unreachable: say so; never fabricate a distribution.
- Aggregate in the probe, never page rows; sort findings by materiality.
- A join key is a hypothesis: state it, show the match rate. Never ask what a probe can turn into a confirmation.
- Personal fields are counted, never listed. On a scan-billed engine (`mb db get <db-id>`), every probe carries a date predicate unless the decision needs the whole table.

## The helper

Written once per working directory with the values filled in literally, and sourced at the start of every Bash call that uses them:

```bash
mkdir -p ./.scratch
cat > ./.scratch/probe.sh <<'SH'
PROFILE=<profile>
DB=<db-id>
q() { jq -n --arg q "$1" --argjson db "$DB" '{"lib/type":"mbql/query",database:$db,stages:[{"lib/type":"mbql.stage/native",native:$q}]}' | mb query --file - --profile "$PROFILE" --json | jq -c '{status, error, cols: [.data.cols[]?.name], rows: .data.rows}'; }
src() { jq -n --rawfile s "$1" --argjson db "$DB" '{type:"query",query:{"lib/type":"mbql/query",database:$db,stages:[{"lib/type":"mbql.stage/native",native:$s}]}}'; }
SH
source ./.scratch/probe.sh && q "SELECT count(*) AS n FROM <schema>.<table>"
```

Pass is `status == "completed"`; otherwise read `error`, or stderr when output is empty. `src <file.sql>` wraps SQL as a transform `source`.

## Tools and limits

- Row ceilings: 2,000 rows bare, 10,000 aggregated (admin settings; `--max-bytes 0` does not lift them). A full extract: a native card, `mb card query <id> --export-format csv > ./.scratch/<name>.csv`, then archive the card.
- Columns: `mb table get <id> --include fields`. One column's cardinality: `mb field summary <field-id>`; its cached values: `mb field values <field-id>`.
- Count every table in one query (explore §4).
- More than two tables on a path: profile in parallel with the `Agent` tool, one subagent per table, each given the helper, the table, its questions, and the domain note's Traps, returning only a summary (grain, verified keys, enum map, match rates, freshness, findings with counts). Read the summaries, never raw output.

## Loader shape

| Columns on most tables | Implies |
| --- | --- |
| Row id, load id, parent id, list index | nested fields flattened into prefixed columns; arrays split into child tables by parent id; load ids order loads |
| Sync timestamp, soft-delete flag, deleted-at, change operation, test-mode marker | rows re-delivered each sync; deletes are flags or change rows; test rows share the table |
| None | hand-loaded or a replica; freshness and duplicates unknown until measured |

Duplicates are measured, never assumed. When history matters, ask the loader's sync mode: a history mode or change capture keeps it; none means capture starts in the first build session (`references/time-and-entities.md`). Staging rules per artifact: `references/modeling.md`.

## The probes

The first three on every table on a path; the rest where a decision is not yet settled.

| Probe | Decides |
| --- | --- |
| Row count | which tables exist and which are empty (empty on a path is a stop) |
| Key uniqueness (rows, distinct, null keys per candidate) | whether the key is the grain or dedup is needed |
| Null rates | which columns carry meaning |
| Enum coverage (value, count, first and last seen) | the mapping checklist; every value with rows maps |
| Foreign-key match rate per path | which relationships are real; the rate is the baseline the relationship check warns from |
| Date agreement per status | which date ends a lifecycle; disagreement is a date-basis decision |
| Identifier domains and outliers | test, staff, demo rows |
| Trailing period (rows and entities per recent period; max event and load time) | freshness, cadence, whether the newest period is partial |
| History horizon (earliest row per history table) | how far back any point-in-time number reaches |
| Baseline candidates (tables named like the measure) | whether a reference exists (`references/reconciliation.md`) |
| The probe each of the domain note's Questions for the owner names | that question's default |

```sql
-- key uniqueness; worst offenders
SELECT count(*) AS rows_total, count(DISTINCT o.order_id) AS keys_distinct, sum(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END) AS key_nulls FROM <raw_schema>.orders o;
SELECT o.order_id, count(*) AS n FROM <raw_schema>.orders o GROUP BY 1 HAVING count(*) > 1 ORDER BY 2 DESC LIMIT 10;
-- enum coverage
SELECT o.status, count(*) AS n, min(o.created_at) AS first_seen, max(o.created_at) AS last_seen FROM <raw_schema>.orders o GROUP BY 1 ORDER BY 2 DESC;
-- foreign-key match rate, one per path
SELECT count(*) AS left_rows, count(c.customer_id) AS matched FROM <raw_schema>.orders o LEFT JOIN <raw_schema>.customers c ON c.customer_id = o.customer_id;
-- date agreement
SELECT s.status, count(*) AS n, count(s.cancelled_at) AS has_cancelled, count(s.ended_at) AS has_ended, sum(CASE WHEN s.cancelled_at <> s.ended_at THEN 1 ELSE 0 END) AS disagree FROM <raw_schema>.subscriptions s GROUP BY 1;
-- identifier domains
SELECT lower(substring(c.email FROM position('@' IN c.email) + 1)) AS domain, count(*) AS n FROM <raw_schema>.customers c GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
-- trailing period
SELECT date_trunc('month', o.created_at) AS period, count(*) AS n, count(DISTINCT o.customer_id) AS entities FROM <raw_schema>.orders o GROUP BY 1 ORDER BY 1 DESC LIMIT 13;
```

Standard SQL; adapt to the engine's dialect.

## Samples and horizons

- Round row counts repeated across tables mean a sampled replica, usually skewed recent: list each table, its cap, the number it degrades.
- Record the earliest row of every history table; the later of two horizons bounds any reconstruction reading both.
- Hunt for history before concluding there is none: the loader's history mode or change capture, and `information_schema.tables` for `%_history`, `%_version`, `snap_%`.

## Close

Each finding that caps a number (truncation, horizon, unit or currency, coverage gap, dedup need, text-typed timestamp, stale derived column) becomes its own decision line, so checks, caveats, and hand-backs read one list.
