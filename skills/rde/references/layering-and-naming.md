# Layering and naming

Read before creating the first transform or writing SQL for the company's own transformation tool.

## Discover the company's conventions first

Inventory what exists and record it in `./.scratch` before proposing any layer, name, or location:

| Look at | Where | Take from it |
|---|---|---|
| Schemas and table names | Catalog commands in [profiling-catalog.md](profiling-catalog.md) | Layer vocabulary, prefixes, landing and output schemas |
| Transforms and their collections | `mb transform list --fields id,name,collection_id --json`, then `mb collection get <id> --json` per collection | Layer count, collection layout, grammar, header style |
| Models, metrics, measures, segments | The discovery commands in [semantic-layer-design.md](semantic-layer-design.md) | Definitions to reuse, description style |
| Documentation | Files the user shares, or an export of an unreachable document space | Conventions, glossary |

Match an existing convention even where it differs from the defaults below; propose a default only where nothing exists, labeled as such, and confirm it with the checkpoint block in [collaboration-contract.md](collaboration-contract.md).

## Invariants and conventions

The final layer is the tables people read, whatever the company calls it. The loader-shape rules in [staging-rules.md](staging-rules.md) apply to whichever model first reads a raw table, even when that model is a wide table with no staging layer.

| Invariant, holds everywhere | Convention, flexes to the company |
|---|---|
| Every model, in every layer, declares the five header facts below; the layout follows an existing header style when one exists | Layer prefixes and name grammar |
| The block that reads a raw table never joins; it may be a CTE inside a wider model | Number of layers, and whether a cleaning layer exists at all |
| Nothing reads a model that a later model in the same chain refines | Collection layout and output schema (defaults under Physical layout) |
| Checks pass before the next model ([data-quality-checks.md](data-quality-checks.md)) | Where SQL files live |
| One definition per number: shared logic computed once, read by every consumer | Whether transforms run in Metabase or in the company's tool |
| Ids kept beside labels, never replaced by them | |
| Detail rows kept; a total sits beside them, never instead of them | |
| Re-runnable without duplicating rows, incremental where volume demands it, a uniqueness check on the key | |
| Business rules are the user's to decide | |

Where an existing convention breaks an invariant, say so once, propose the fix, and let the user decide.

## Default layers

Default, to confirm, when no convention exists:

| Layer | Does | Owes |
|---|---|---|
| Staging | One model per source table: rename, cast, convert units, choose a key. No joins. | A safe-to-read source table ([staging-rules.md](staging-rules.md)) |
| Intermediate | Joins, enrichment, classification, attribution, recognition | Each piece of shared business logic computed once |
| Mart | The final layer: the output grains people read | The measures for its grain on the row |

A final-layer table exists only if it rolls up (changes what a row is), conforms an entity across sources, or adds measures that only make sense at the output grain; one whose body would be `SELECT * FROM <model below>` is not built, and consumers read the model below.

## Naming

| Object | Default pattern | Example |
|---|---|---|
| Staging model | `stg_<source>_<table>` | `stg_acme_order` |
| Intermediate model | `int_<source>_<concept>` | `int_acme_order_classified` |
| Entity mart | `mart_<source>_dim_<entity>` | `mart_acme_dim_customer` |
| Event mart | `mart_<source>_fct_<event>` | `mart_acme_fct_order` |
| Composite grain key | `<entity>_<period>_key` | `customer_month_key` |

`<source>` is the system the data came from, not the warehouse and not the team. Under any grammar:

- Ambiguous words are banned as column names: the rule in [semantic-layer-design.md](semantic-layer-design.md).
- Which id is the key, and when to mint one: Key selection in [staging-rules.md](staging-rules.md).

## Model header

Five facts at the top of every model's body, mirrored into its description; the layout below is the default where the company has no header style:

```sql
-- One row per: <X>
-- Key:         <column that identifies the row>
-- Sources:     <upstream models or tables>
-- Definition:  <one-line business definition>
-- Caveats:     <exclusions, hardcoded values, deviations, unconfirmed assumptions with their open question>
```

Constants (window length, rank order, exclusion list, rate) live in one named place.

## Declare grain and key before building

Agree the inventory with the user as a table before the first model is created: staging models one per source table, the named intermediates, and final-layer tables as three lists (entities, events, rollups).

| Model | One row per | Key |
|---|---|---|
| `mart_acme_dim_customer` | customer | `customer_id` |
| `mart_acme_fct_order` | order | `order_id` |
| `mart_acme_fct_customer_month` | customer and month | `customer_month_key` |

- Materialize a composite grain as one column, `concat(customer_id, '|', cast(date_trunc('month', event_at) as varchar)) AS customer_month_key`, so the grain check is a duplicate count on it.
- A grain column name means the same thing everywhere; pick the date basis once, record it, and checkpoint it.
- Unrelated domains get their own final-layer tables; a domain with no stated business logic gets the simplest defensible model, every definitional choice logged as an open question.

## Grain ladder for rollups

1. One atomic grain: the finest row the source supports (one row per order line).
2. One primary rollup: the grain most questions are asked at (one row per order).
3. Segment rollups: the same measure set sliced one way each (per customer and month).

Define the measure set once and reuse it across the segment rollups; a list of questions is usually a few measures across a few grains, answered by rolling one event model up by a date column.

## Anti-patterns

| Never | Instead |
|---|---|
| Precomputed totals instead of detail rows | Detail rows, with a convenience count beside them |
| Joining several child tables directly onto one row | Pre-aggregate each child to the target grain in its own block, then join the blocks |
| A placeholder for an absent attribute | `coalesce(x, 0)` only for a measure from a left-joined child; a genuinely absent attribute stays null |

## Physical layout

Every clause here is a default to confirm: one collection per layer named for it (`stg_acme`, `int_acme`, `mart_acme`), each model filed before the next is started; every layer in one output schema separate from the landing schema; layer carried by prefix and collection, not by schema.

## Transformations that run outside Metabase

When the company transforms data in its own tool, [build-clean-tables.md](../playbooks/build-clean-tables.md) still runs:

- Applies: pre-flight, the build ledger, SQL carrying the model header in the company's file layout and naming, `mb query` validation against physical table names, and the quality gate on each landed table.
- Skipped: collections, `mb transform create`, `update`, and `run`, and the DAG re-run.
- SQL references physical tables so it runs through `mb query`; the user swaps in their tool's reference syntax. Hand the files over from `./.scratch`.
- Once the tables land: `mb db sync-schema <id> --wait`; a batch gets the gate per model in dependency order. `DEPLOYED` for a landed table means it passed the gate. Then continue at the semantic layer ([semantic-layer-design.md](semantic-layer-design.md)).

## When a single flat table is enough

Skip the layers when a handful of source tables describe one real-world thing, no measure is shared by two outputs, and there is no rollup: one wide table per thing (`customers`, `orders`, `products`), linking ids kept on it. Return to layers when the same business logic is about to be written into two outputs, or an output table feeds another: promote the shared piece into an intermediate model.
