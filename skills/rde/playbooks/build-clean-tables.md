# Build clean tables

Applies once a model inventory is approved; produces the models as Metabase transforms, gated on data quality, plus a build ledger. An open model, grain, or key returns to [`explore-raw-data.md`](explore-raw-data.md).

Read first: [`layering-and-naming.md`](../references/layering-and-naming.md), [`staging-rules.md`](../references/staging-rules.md) (loader shape too), [`modeling-decisions.md`](../references/modeling-decisions.md), [`data-quality-checks.md`](../references/data-quality-checks.md), [`ledgers-and-artifacts.md`](../references/ledgers-and-artifacts.md), [`collaboration-contract.md`](../references/collaboration-contract.md), dialect and row ceiling in the Tools and limits section of [`profiling-catalog.md`](../references/profiling-catalog.md), the domain file the router named, `mb skills get transform`, `mb skills get native-sql` or `mbql`, `mb skills get metadata` (step 7).

## 1. Pre-flight

Fix profile, database id, output schema. Match the schema and names existing transforms use (`mb transform list --fields id,name,collection_id,target --max-bytes 0 --json`); with none, propose the `layering-and-naming.md` default to confirm. Outside-Metabase transformations: the note in `layering-and-naming.md` says which steps below apply.

Count every source table in the inventory (enrichment included): name, rows, status. Confirm every target name is free in that list and in `mb table list --db-id <db-id> --fields id,name,schema --max-bytes 0 --json`.

Check: no zero-row source, no name collision. Either is a checkpoint, never a silent skip or overwrite.

## 2. Collections

Reuse existing transform collections; otherwise one per layer, named per `layering-and-naming.md`, via `mb collection create --namespace transforms` (body from the bundled skill). Check: `mb transform list --fields id,name,collection_id --json` shows every transform filed.

## 3. Ledger and order

Start `./.scratch/BUILD_LEDGER.md` per `ledgers-and-artifacts.md`, SQL beside it, one file per model. One layer at a time, in dependency order within it.

## 4. Build loop, one model at a time

1. SQL, formatted, in `./.scratch/<model>.sql`, headed per `layering-and-naming.md`; the block that reads a raw table obeys `staging-rules.md`.
2. Run it through `mb query` as a native stage with a small `--max-bytes`. A pass is `status: completed` on stdout, or an over-cap exit 2; `{status: failed}` on stdout with exit 0 is a failure. An MBQL transform is validated with `mb query --dry-run` on its body instead of a `.sql` file.
3. `mb transform update <id>` when the name exists in `mb transform list --max-bytes 0 --json`, else `mb transform create` (body from the bundled skill).
4. `mb transform run <id> --sync --json`. `--sync` waits for this transform's target table to register; it is not a database-wide sync.
5. On a failed run, fix the SQL file and return to 3, never to a second transform.

## 5. Quality gate after every model

Run the `data-quality-checks.md` suite on the fresh table; report in its format. A `FAIL` stops the build: no next model, no weakened check; a join match rate under threshold, an unconfirmed empty output, and a non-unique grain all fail.

When the fix is a judgment, stop with counts in hand, using the checkpoint block in [`collaboration-contract.md`](../references/collaboration-contract.md): the collision winner, the authoritative column, the partial-period cut (`modeling-decisions.md`), the fate of rows an enrichment join missed (default: null columns plus a flag column, confirmed). Record every answer in both ledgers.

## 6. Declare each model deployed

Write `status: DEPLOYED` only when the four criteria in `ledgers-and-artifacts.md` hold.

## 7. Metadata on the final-layer tables

On deployed final-layer tables only, perform the field-metadata pass in the order `semantic-layer-design.md` gives (`mb skills get metadata`). Check: every inventory foreign key resolves to a real table; no decoded column is untyped.

## 8. Re-running a chain

`mb transform dependencies <id>` lists upstream transforms, not dependents; re-run a chain per the "Building a DAG" section of `mb skills get transform` (tags plus a transform-job).

## Done when

Every model carries `status: DEPLOYED`; no check fails; final-layer tables have step 7 metadata; every checkpoint is answered; every model's SQL sits in `./.scratch`.

## Reply

The tables, what one row of each is, how they connect; the checks that ran; limitations named as such; one final-layer table to open, by name and link; decisions still held; offer the semantic layer next.
