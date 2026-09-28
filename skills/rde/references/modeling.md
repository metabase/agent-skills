# Modeling

Read before the first transform, or before writing SQL for the company's own tool.

## Match what exists

Layer prefixes, naming, number of layers, output schema, collection layout, where SQL lives, and whether transforms run in Metabase or elsewhere are the company's conventions: match what orient found; propose a default only where nothing exists, as a decided line. A convention that breaks an invariant is named once with a fix; the answer is a decision. Tables built outside Metabase (`data_source: transform`, dbt-shaped schemas) are the curated layer: build on them, never rebuild their staging.

## Layers, the default

- **Staging**: one block per source table, `stg_<source>__<entity>`: rename, cast, convert units, filter other universes, deduplicate; no joins, no business logic, no aggregation. A CTE inside its only consumer until two models read it or it deduplicates a large appended sync. An inlined block still follows staging rules and passes row parity.
- **Intermediate**: only where two outputs share logic (joins, classification, attribution, recognition), computed once: `int_<domain>__<what>`.
- **Final**: named for the business entity or event (`customers`, `invoice_lines`, `customer_months`), never the source. It exists only if it conforms an entity, rolls up, or adds measures at its grain; never a `SELECT *` over the model below.
- **Reading and re-running**: a model reads the most refined upstream in its chain, never one a later model refines; every model re-runs without duplicating rows.
- **Flat under a deadline** (small source, one decision maker, close deadline): one wide table per real-world thing with linking ids on every table, said plainly; promote shared logic the moment it would be written twice.

Final tables as three lists: entities, events, rollups. Per measure set: one atomic grain, one primary rollup, segment rollups only where asked; pre-aggregate each child to the target grain before joining. Keep detail rows with totals beside them, and ids beside labels.

Placement: one output schema separate from raw schemas (a transform never writes into a raw schema); one transforms collection per domain; `data_layer` set as build §7 says (without `data_layer` on the server, `visibility_type: technical` on everything not final).

## Names

`*_id` keys, `*_at` UTC timestamps, `*_date` dates, money suffixed with its unit (`amount_usd`) after counting currencies; `snake_case`; one id named the same everywhere. `date`, `amount`, `status`, `type`, `value`, `count` always qualified. A composite grain is one concatenated key column, `<entity>_<period>_key`. Name every aggregation output; an unnamed `count` becomes the column name.

## The description

Written before the transform is created; the one copy of the model's header (no SQL-comment mirror):

```
grain: one row per <what>; key <column>
sources: <tables it reads>
definition: <one line in business words>
scope: <population; how exclusions are flagged>
required filters: <e.g. is_complete_period for rates and trends>
caveats: <currency, horizon, incomplete period, provisional rules in plain words>
owner: <email>
```

The transform carries all of it; the output table gets `description` = the grain, scope, and required-filters lines (≤400 characters), `caveats`, and `owner_email`. A reader who never saw this session must be able to use the table from those fields alone.

## Staging

- Money converted once to one unit, named for it (`amount / 100.0 AS amount_usd`; zero- and three-decimal currencies divide differently). Timestamps stay UTC; business-timezone dates and FX (needs a rate table and date) are derived downstream.
- Rows from another universe (test mode, soft-deleted, a discriminator naming another table) are filtered here and declared in `scope:`, or kept as an explicit boolean when downstream counts them; never unfiltered and unflagged.
- A lossy cast goes into a new column; cast parity proves every non-null survived, then the raw column is dropped. More nulls after a cast is a failure to investigate.
- Junk placeholders (`"NULL"`, `"N/A"`, `"-"`, `""`) become nulls; `0`/`1`, `Y`/`N`, `"true"` become booleans; text trimmed and case-consistent; epochs converted (read one converted row to tell seconds from milliseconds).
- Codes stay codes; labels join downstream from the lookup (`*_field`, `*_choice`, `*_type`), read in the query, never typed as literals. A multi-valued field never becomes a blob: separate columns or a child table, the user's choice.
- Keys: stable source ids; never mint replacements. Mint only for a child table with no natural key (loader row id, or parent id plus position). Several candidates: a decided line with evidence.

| Loader artifact | Rule |
| --- | --- |
| Row id | drop; keep only as a keyless child table's key |
| Load id, sync timestamp | drop; keep only as dedup tiebreaker or freshness input |
| Soft-delete flag or deleted-at | filter, or an explicit boolean when downstream counts deletes; say which in `scope:` |
| Prefixed nested column (`address__city`) | rename `<parent>_<field>`; drop the prefix only when unambiguous |
| Array child table (`order__items`) | its own block, one row per element, joined on the business key if present, else the loader's parent id (say so) |
| JSON-widened types (epoch ints, minor units, string dates and enums) | convert once here, unit in the name |

## Duplicates: which row wins

Measure first; zero duplicates proves a plain block correct. A table that keeps history (versions, a change log, SCD rows) is never reduced to one row per key: remove only exact re-deliveries of one version, then join it by validity window (`references/time-and-entities.md`). Deduplicate in staging with a deterministic `row_number()` over the key and declared tiebreakers, keeping rank 1: consumed tables hold winners only; losers are counted in a check, or kept in an audit table when someone must see them, never flagged inside a table people read. Never `SELECT DISTINCT` or a bare `GROUP BY` to resolve a collision.

```sql
WITH ranked AS (SELECT s.*, row_number() OVER (PARTITION BY s.<key> ORDER BY <tiebreakers>) AS rn FROM <raw_schema>.<table> s)
SELECT <columns> FROM ranked r WHERE r.rn = 1
```

| Tiebreaker family | Right when | Wrong when |
| --- | --- | --- |
| Latest by time (`loaded_at DESC`) | later rows supersede: a re-sync, a status that only advances | a later row is a fragment (a trailing correction): recency picks the less complete row |
| Preferred by attribute (`is_partial ASC`, then a measure or ranked category) | one row is structurally authoritative: complete over fragment, settled over pending | the replacement is legitimately smaller (a downgrade): "largest wins" keeps the stale figure |

- "Latest load wins" on an appending loader is mechanical once measured. Every other collision is a decision: report groups over one row, rows, share; show two or three groups with differing columns; name the rule and what the alternative changes in the headline.
- Where the data holds the family's breaking case, write an explicit rule and record the case and its count; a late-settling record (refund, correction) always gets one. These cases become the test fixture.
- Rank only qualifying rows (complete, positive, settled) when a group has them. A group of only fragments is its own case: combine additive parts of one event, keep the best of versions, and say which.
- One column of the winner: `first_value(...) OVER (...)`, never a self-join or engine-specific max-by.
- Check every enrichment join's right side for uniqueness first; resolve a many-sided right side before the join.

## Which column is authoritative

| Prefer | Over | Because |
| --- | --- | --- |
| The line item | the document header | headers mutate in place; lines state what was true when issued |
| The immutable reference the line points at (price, plan) | a copy on a mutable parent | every copy is suspect until tested |
| The dominant child by value (`first_value(...) OVER (PARTITION BY <doc> ORDER BY <amount> DESC)`, add-ons excluded first) | first, last, or most common child | value decides what the document is |
| A validity-window join | the entity's current attribute | current state is wrong before the last change (`references/time-and-entities.md`) |

Test a suspected copy; a non-zero count is a decision: `SELECT count(*) FROM <lines> l JOIN <prices> p ON p.price_id = l.price_id JOIN <agreements> a ON a.agreement_id = l.agreement_id WHERE p.recurring_interval <> a.copied_interval`.

Where no single column answers every row, a ladder `coalesce(signal_1, signal_2, default)`, rungs ordered by how directly they speak for the row (own immutable reference, own observable property such as period length, the parent's current value, a stated default), each null when it cannot answer.

- A heuristic sits behind anything that states the answer directly, encoded as bounded ranges with gaps read off the distribution (`BETWEEN low AND high` per class, else null), never nearest match.
- The rung order is a decision, proposed with rows resolved per rung and rows falling to the default; never copied from another build. Emit `<attribute>_source`; traffic on the literal default is a finding.
- Changing a rung: count each misclassification direction before and after; a lower total that grows the opposite error is no improvement.
- Clamp a physically bounded measure (`greatest(x, 0)`) and report rows changed; many means the derivation is wrong. Negative filters null-safe: `(email IS NULL OR email NOT LIKE '%@<staff domain>')`.

Every classification with business meaning is a decision, never settled silently in a `WHERE`.

## Exclusions

A flag plus `exclusion_reason` on the conformed entity or event, computed once from an explicit rule list (staff domains, test accounts, documented incidents, each identifier verified in the data first); metrics and segments read the flag. Excluded rows stay, so reported and adjusted figures can sit side by side.

## Constants

`cfg_<domain>`, one row with one column per constant, `data_layer: internal`, only for a business parameter two or more models read or one that backs an open decision (a grace window, a threshold). Models cross-join it (`CROSS JOIN <out_schema>.cfg_<domain> c`); their tests declare it as an input so the alternative value is rehearsed on fixtures. Changing one: transform update, the tests of every model reading it, one job run. Any other constant lives in its one model's SQL, stated in caveats. The last complete period is derived, never a constant.

## Materialization

Default full rebuild (`target.type: "table"`), so a logic change backfills every period. After the first run read duration and rows (`mb transform runs --transform-id <id>`); propose incremental only when the rebuild exceeds the job window or the engine bills by scan, as a decided line with both numbers.

| Rows | Strategy |
| --- | --- |
| Immutable events with a monotone load timestamp | `table-incremental`, `append`, checkpoint on the load timestamp |
| Entities mutating in place | `table-incremental`, `merge` on the key, checkpoint on the update timestamp |
| Anything a whole-partition window reads (latest-load dedup, spine, movements) | full rebuild |

An incremental model carries a lookback window for late rows, dedup on append, a hard-delete strategy, and a periodic full refresh. The checkpoint must be monotone (a load timestamp, never an event time) or late rows are skipped forever. A run with no stored watermark is a full refresh (the first run, and after the checkpoint field changes); `delete-table` keeps the watermark. A changed definition, merge key, or checkpoint column needs a full refresh: force it by updating the checkpoint field (to another column and back), since `delete-table` alone does not. The gate reads the whole table, never the increment. Body keys: `mb transform create --help --json | jq '.inputSchema.properties | {target, source}'` (`target.target-incremental-strategy`, `source.source-incremental-strategy.checkpoint-filter-field-id`).

## Transformations outside Metabase

When the company transforms in its own tool, build's method still runs: the build list, SQL in their layout with the description as header, slice validation through `q()`, the same test cases in their test facility, the gate on each landed table. Skipped: smoke test, collections, tags, jobs, `mb transform`, `mb transform-test`. Hand over the files; once landed, `mb db sync-schema <db-id> --wait`, the gate in dependency order, `data_source: transform` on each, then the semantic layer.
