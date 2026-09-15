# Staging rules

Read when starting the cleaning layer, whatever the company calls it, and for whichever model first reads a raw table ([layering-and-naming.md](layering-and-naming.md)).

## Invariants

- The block that reads a raw table never joins; enrichment, decoding against a lookup, and classification belong to an intermediate model or a later CTE in a wide model.
- No business logic: no recognition rule, no status collapse, no derived category. Casts, renames, unit conversion, decoding of encodings, key selection, and loader bookkeeping removal only.
- No filter that changes the population the table describes. A hygiene filter removing structurally broken rows is allowed and declared in the header.
- No aggregation: staged rows equal source rows minus the tombstones and duplicates removed deliberately and reported.

## Defaults to match or confirm

- One staging model per source table, named by the company's convention (default in [layering-and-naming.md](layering-and-naming.md)); never merge two source tables into one staging model, never split one into two, never rename two source tables into one shape to look consistent (conform in the intermediate layer).
- Money in one unit and timestamps in one timezone, each converted exactly once, at this step, with the unit in the column name and the timezone in the header.
- Deduplication sits here only when measured as needed (below).

## How a loader shapes a table

Discover the loader's shape from the landed tables, never from assumption. Read the column list per table (`mb table get <id> --include fields --json`): a flattened column exists only where at least one parent row populated it, so two tables of the same source type can carry different columns.

| Columns present on most tables | Implies |
|---|---|
| Row id, load id, parent id, list index | Nested fields flattened into prefixed columns; arrays split into child tables linked by parent id; load ids order the loads |
| Sync timestamp, soft-delete flag, deleted-at, or change-capture operation | Rows re-delivered each sync; deletes are a flag or a change row; dedup by key on the sync column |
| None | Hand-loaded or a database replica; freshness and dedup behaviour unknown until measured |

Record the freshness column and its maximum value; a stale loader caps every trailing period in every model ([modeling-decisions.md](modeling-decisions.md)).

| Loader artifact | Rule |
|---|---|
| Row id column (one per landed row) | Drop, except kept deliberately as the key of a child table that has no natural key |
| Load id column (one per run) | Drop, except kept deliberately as the deduplication tiebreaker |
| Sync or extracted-at timestamp | Drop, except kept as the tiebreaker or as the freshness input |
| Soft-delete flag or deleted-at column | Resolve here: filter deleted rows out, or keep an explicit boolean when downstream counts them. Pick one, say which in the header, apply consistently. Never leave tombstones unfiltered and unflagged |
| Type-discriminator column whose every value names the table it sits in | Drop |
| Nested field flattened into a prefixed column (`address__city`, `address_city`) | Rename to `<parent>_<field>` in `snake_case`; drop the prefix only when the field name is unambiguous without it |
| Array split into a child table (`order__items`) | Stage the child table as its own model with one row per element |
| Child table linking column | Join back on the business key when the element carries one (`order_id`); fall back to the loader's parent id column, and say so in the header |
| Child table with no natural key | Key on the loader row id, or on parent id plus array position |
| Types widened to the source API's JSON types (epoch integers, minor-unit integers, strings for dates and enums) | Convert once here with the unit in the column name |
| One row per key per load (appended syncs) versus merged rows | Measure (below); never assume either |

## Casts and renames

| Source shape | Target | Rule |
|---|---|---|
| Amount in minor units (integer cents) | Major units | `amount / 100.0`, named for the unit: `amount_usd` |
| Epoch integer | Timestamp | Epoch-to-timestamp conversion, column suffixed `_at` |
| Timestamp in mixed or local timezones | One timezone | Convert here; state the timezone in the header |
| Date or enum as a string | Date or typed value | Cast here |
| Boolean as `0`/`1`, `Y`/`N`, `"true"`/`"false"` | Real boolean | Normalize here |
| Junk placeholder (`"NULL"`, `"N/A"`, `"-"`, `""`) | Real null | Normalize here; a null that means absent stays null, never coalesced into a placeholder |
| Text | Trimmed, case-consistent text at sane numeric precision | Normalize here |
| Coded column (`c_4471`, `status_3`) | Cleanly typed code | Deliver the code; the label join happens in an intermediate model |
| Anything | `snake_case` | `*_id` keys, `*_at` timestamps, `*_date` dates |

Count the distinct currencies or units present before suffixing a column with a unit.

## Preserve the source column beside a lossy cast

When a cast can lose information (text to number, text to date, wide numeric to narrow), cast into a new column and keep the original beside it, so cast parity compares non-null originals against non-null casts.

Never gain nulls silently. More nulls in a staged column than in the source is a failure to investigate.

## Key selection

- Globally unique, stable source ids are the primary and foreign keys. Do not mint replacements.
- Mint a key only for a child or array table with no natural key (rule in the loader table above).
- One candidate: proceed. Several candidates: checkpoint (block in [collaboration-contract.md](collaboration-contract.md)).
- Assert uniqueness on the chosen key with the key-uniqueness probe in [profiling-catalog.md](profiling-catalog.md). Duplicates on it mean the wrong key or a table that needs deduplication.

## Decode and normalize encodings

Normalized sources hide meaning in lookup tables (`*_field`, `*_choice`, `*_question`, `*_type`). Build the code-to-label map from the lookup and pull the label from the lookup in the query, never as a typed-in literal. The join makes that model intermediate; staging delivers the code column typed and named.

Never flatten a multi-valued field into an opaque blob (`"email | phone | text"`). Separate columns or a child table with one row per value; the choice is the user's, filterability is not.

## Measure whether deduplication is needed

Run the key-uniqueness probe ([profiling-catalog.md](profiling-catalog.md)) on every staging model and compare source rows to staged rows. Some loaders land exactly one row per key; a loader that appends every sync leaves one row per key per load and inflates a table by a multiple. Zero duplicates proves a plain one-row-per-source-row model correct.

When loads append and the rule is "latest load wins", the standard-SQL shape is:

```sql
WITH ranked AS (
  SELECT s.*, row_number() OVER (PARTITION BY <key> ORDER BY <load id or sync timestamp> DESC) AS load_rank
  FROM <source table> s
)
SELECT * FROM ranked WHERE load_rank = 1;
```

Which collisions are mechanical and which are checkpoints: [modeling-decisions.md](modeling-decisions.md).

## Check before moving on

Run the suite in [data-quality-checks.md](data-quality-checks.md) per model or batched per layer; a failure blocks the next model. For a joined wide model, row parity is per source block, or on the driving table.
