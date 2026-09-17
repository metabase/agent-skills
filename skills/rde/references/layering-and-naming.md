# Layering and naming

Read before the first transform, or before writing SQL for the company's own tool.

## Discover the company's conventions first

Before proposing a layer, name, or location, inventory what exists and record it in STATE.md ([state.md](state.md)): schemas and table names ([profiling-catalog.md](profiling-catalog.md)); transforms and their collections (`mb transform list --fields id,name,collection_id,description --json`); existing models, metrics, measures, and segments ([semantic-layer-design.md](semantic-layer-design.md)); files the user shares. Match what exists; propose a default only where nothing exists, labelled as such, as a reversible decision ([collaboration-contract.md](collaboration-contract.md)). Where a convention breaks an invariant, say so once, propose the fix, and record the answer as a Decisions row.

## Invariants and conventions

"Final layer" is the role term for the tables people read, whatever the company calls them. The loader-shape rules in [staging-rules.md](staging-rules.md) apply to whichever block first reads a raw table, even inside a wide table with no staging layer.

Invariants: every model in every layer declares the five header facts below; the block that reads a raw table never joins; nothing reads a model that a later model in the same chain refines; every rule a model carries is pinned by a transform test before it materialises ([transform-tests.md](transform-tests.md)); checks pass before the next model ([data-quality-checks.md](data-quality-checks.md)); one definition per number, computed once and read everywhere; ids kept beside labels; detail rows kept, a total beside them, never instead; re-runnable without duplicating rows; a uniqueness check on the key; business rules are the user's to decide.

Conventions, the company's: layer prefixes and name grammar; number of layers, and whether a cleaning layer exists; collection layout and output schema; where SQL files live; transforms in Metabase or in the company's tool; a staging block materialized or a CTE.

## Layers, and the flat default

Default, to confirm, when no convention exists: staging, one block per source table (rename, cast, convert units, choose a key; no joins), owing a safe-to-read source table ([staging-rules.md](staging-rules.md)); intermediate (joins, enrichment, classification, attribution, recognition), owing each piece of shared business logic computed once; final layer (mart), the output grains people read, owing the measures for its grain on the row.

A staging block is a CTE inside its only consumer; it becomes its own materialized transform when two or more models read it or when it deduplicates a large appended sync. A final-layer table exists only if it rolls up, conforms an entity across sources, or adds measures that only make sense at the output grain; a `SELECT * FROM <model below>` is not built.

Flat under deadline: a small source, one decision maker, and a deadline get one wide table per real-world thing (`customers`, `orders`) or two layers (cleaned tables, then the tables people read), linking ids kept on every table; say so plainly. Return to layers when the same logic is about to be written into two outputs, or an output feeds another: promote the shared piece into an intermediate model.

## Naming

Default grammar `<layer>_<source>_<thing>` (`stg_acme_order`, `mart_acme_fct_order`); `<source>` is the system the data came from, not the warehouse or the team; a composite grain key is `<entity>_<period>_key`. Ambiguous words (`date`, `amount`, `status`, `type`, `value`, `count`) are banned as column names; qualify them (`order_date`, `amount_usd`). Key choice and minting: [staging-rules.md](staging-rules.md).

## Model header and constants

The transform description is the canonical header; the SQL comment at the top of the body mirrors it, and when they differ the description wins. Five facts, in the company's header style where one exists:

```sql
-- One row per: <X>
-- Key:         <column that identifies the row>
-- Sources:     <upstream models or tables>
-- Definition:  <one-line business definition>
-- Caveats:     <exclusions, constants and values, deviations, provisional decisions by id>
```

Constants live in one transform, `cfg_<domain>` (`SELECT 1 AS gap_months, 'D7' AS gap_months_note, 0.05 AS materiality, 'D2' AS materiality_note`): one row, one column per constant plus a `<constant>_note` column naming the STATE.md decision id. Every model that reads a constant cross-joins it (`CROSS JOIN analytics.cfg_billing c`, then `c.gap_months`); changing one is a `mb transform update` on `cfg_<domain>`, the domain's transform tests run (each declares `cfg_<domain>` as an input, so the alternative value is rehearsed on fixtures first; [transform-tests.md](transform-tests.md)), then one run of the domain's job.

## Declare grain and key before building

Agree the inventory as a table before the first model is created: staging blocks one per source table, the named intermediates, and final-layer tables as three lists (entities, events, rollups). A grain column name means the same thing everywhere; pick the date basis once, as a decision.

| Model | One row per | Key |
|---|---|---|
| `mart_acme_dim_customer` | customer | `customer_id` |
| `mart_acme_fct_order` | order | `order_id` |
| `mart_acme_fct_customer_month` | customer and month | `customer_month_key` |

A composite grain is one concatenated column, so the grain check is a duplicate count on it.

Grain ladder for rollups: one atomic grain, the finest row the source supports; one primary rollup, the grain most questions are asked at; segment rollups, the same measure set sliced one way each. Define the measure set once; pre-aggregate each child to the target grain in its own block before joining.

## Materialization

Default: full rebuild (`target.type: "table"`), so a logic change backfills every period on the next run. After the first run measure rows and duration (`mb transform runs --transform-id <id> --json`); propose incremental only where the rebuild exceeds the job window or the engine bills by scan, as a reversible decision carrying both numbers.

| Rows | Strategy |
|---|---|
| Immutable events with a monotone timestamp | `table-incremental`, `append`; source checkpoint on that column |
| Entities that mutate in place | `table-incremental`, `merge` on the declared key (deletes matching keys, then inserts); checkpoint on the update timestamp |
| Anything a whole-partition window function reads (latest-load dedup, dense spine, motion tables) | full rebuild |

Body shape: `mb transform create --help --json | jq .inputSchema`; mechanics: `mb skills path transform`, section "Incremental targets". A run reads rows with checkpoint above the stored watermark up to the field's maximum at run start, then stores that maximum; the field must be monotone (a load timestamp, never an event time) or a late row is skipped forever. A run with no watermark is a full refresh: the first run, and the run after `checkpoint-filter-field-id` changes. `delete-table` keeps the watermark and does not force one. A changed definition, merge key, or checkpoint column needs a full refresh, forced by changing the checkpoint field on update or by deleting and recreating the transform. The quality gate reads the whole table after an incremental run, never the increment. History snapshots (`append` transforms): [entities-and-time.md](entities-and-time.md).

## Physical layout

Defaults to confirm: one collection per layer named for it (`mb collection create --body '{"name":"stg_acme"}' --namespace transforms`); every layer in one output schema separate from the landing schema; layer carried by prefix and collection, not by schema.

## Transformations that run outside Metabase

When the company transforms data in its own tool, [build-clean-tables.md](../playbooks/build-clean-tables.md) still runs: the Models table in STATE.md; SQL with the header in the company's layout and naming; slice-first validation through `q()` on physical table names; the gate on each landed table. Skipped: smoke test, collections, tag and job, `mb transform create`, `update`, `run`, `mb transform-test` (the same cases go into the tool's own test facility, [transform-tests.md](transform-tests.md)), and picker hiding of the tool's tables. The user swaps in their tool's reference syntax; hand over the files. Once the tables land: `mb db sync-schema <id> --wait`, the gate per model in dependency order (a passed table is deployed, [state.md](state.md)), then the semantic layer ([semantic-layer-design.md](semantic-layer-design.md)).
