# Explore raw data

Applies when raw data is synced into Metabase, or must be landed first, and nothing is modeled yet; produces a closed source inventory, a profile per table, a model inventory with a grain and a key per model, and the pre-registered checkpoints. Builds nothing.

Read first: [`collaboration-contract.md`](../references/collaboration-contract.md), [`profiling-catalog.md`](../references/profiling-catalog.md), [`layering-and-naming.md`](../references/layering-and-naming.md), the loader-shape section of [`staging-rules.md`](../references/staging-rules.md), [`ledgers-and-artifacts.md`](../references/ledgers-and-artifacts.md), the domain file the router named, and `mb skills get core`.

## 1. Land data not yet in the warehouse

Data not in a database Metabase can query: the user lands it with their loader into one, untouched, then `mb db sync-schema <db-id> --wait`. Check: `mb db get <db-id> --include tables --json` lists the landed tables. Stop until it does.

## 2. Discover what exists, then ask

Run `mb db list --json`, `mb db get <db-id> --include tables --json`, `mb collection tree --json`, `mb transform list --fields id,name,collection_id,target --max-bytes 0 --json`, `mb search --models dataset,metric --limit 50 --json`. Record the layer vocabulary, name patterns, collection layout, output schema, and existing models and metrics; match them. The `layering-and-naming.md` default applies only where nothing exists, labeled as a default to confirm.

Ask in one message: the database and schema of the raw data; an ERD or data dictionary; whether transformations run outside Metabase (then the outside-Metabase note in `layering-and-naming.md`); whether a number you will build already exists elsewhere, and ask for that export at the finest grain now.

Check: a database id, a schema name, and a written list of conventions to match.

## 3. Inventory every table

`mb table list --db-id <db-id> --fields id,name,schema --max-bytes 0 --json`, then one `SELECT count(*)` per table through `mb query` with a native stage. Present name, row count, status. Never name a table the catalog did not return; exclude scratch and system schemas no model reads.

Check: every table has a count. A zero-row table is a checkpoint under the zero-row rule in `collaboration-contract.md`; loader scaffolding tables are its exemption.

## 4. Meaning versus plumbing

Read the columns of a few tables (`mb table get <id> --include fields --json`) and classify each as meaning or loader plumbing per the loader-shape section of `staging-rules.md`. Check: per table, what one row is and which columns carry meaning.

## 5. Profile with the catalog

Run the catalog queries whose decision you face; at minimum per table: key uniqueness, null rates, value sets of coded columns, join match rates, date horizon, duplicate count at the intended grain. Aggregate in SQL (row ceiling: `profiling-catalog.md`).

Check: no grain without a measured duplicate count, no join without a match rate. Questions the catalog marks as never answered by default go to step 8.

## 6. Propose the model inventory

Fill the grain-and-key inventory table in `layering-and-naming.md`, per model, in the company's layer vocabulary: layer, name, purpose, grain as "one row per ___", key, source tables, the step 8 decisions it depends on. Match the company's layer count; where none exists, the flat-table rule in `layering-and-naming.md` decides. Check: every source table feeds a model or is named out of scope with a reason.

## 7. Present and rank

In the user's terms: what you found, what you would build, what you would leave out (measured extent of real data versus droppable columns). Ask them to rank the deliverables or set a "stop after N" rule. Check: must-haves named.

## 8. Pre-register the checkpoints

List every decision the build will stop on: what the profile left open plus the always-stop categories in `collaboration-contract.md`. Record each in the contract's pre-registration record, with who can answer it and which models depend on it, in the assumption ledger per `ledgers-and-artifacts.md`. A default in the plan is not a confirmation.

## 9. Wait

Stop for an explicit reply; nothing is created before it.

## Done when

Every check in steps 2 to 8 passes, the checkpoints are in the ledger, and the user has approved and ranked the plan.

## Reply

What the data is about, in the user's terms; what you would build; what is left out and how much real data it holds; the ranked build order; the open decisions numbered, one line each, grouped by who can answer. Nothing is built; approval starts the build.
