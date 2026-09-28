# Build clean tables

Applies with an inventory whose proposal point returned (explore §8 or extract §7), one model added later (start at §1 with a one-model proposal: its inventory row and decisions printed, then one `AskUserQuestion`), or a request to test a transform (§4 on that model). Produces transforms with their rules tested, gated on landed data, approved before going live, plumbing internal, history captured where needed, scheduled, with a standing check.

Read first: `references/modeling.md`, `references/transform-tests.md`, `references/quality-checks.md`; `references/time-and-entities.md` when a model has periods; the domain note's Invariants and Test cases.

Order: 1 pre-flight, 2 collection/tag/job; then per layer (staging, intermediate, final, each later chain): 3 describe and slice, 4 test, 5 run, 6 gate for each model in dependency order, then 7 go-live approval (stop; the next layer starts only after yes); then 8 schedule and standing check, hand-back.

## 1. Pre-flight

- A proposal point has returned (or, headless, is recorded unanswered); otherwise run it now. Build only the models on the current slice's path; more needs a yes to widen.
- Re-read those tables and existing transforms with their last runs and tests: built, passing, and decided is done.
- Record `environment`: production (what you write is what people see) or staging (changes reach production as a reviewed branch; `mb git-sync status`).
- Prove the write path unless your transforms already run into that schema: a throwaway `_rde_smoke` transform writing one literal row into the output schema, `run --sync`, then `mb transform delete-table <id> --yes` and `mb transform delete <id> --yes`. A permission or missing-schema error is a stop for the admin, never a reason to write elsewhere.

## 2. Collection, tag, job

Reuse what exists; else one transforms collection per domain, one tag per chain, one job over the tag at the loader's cadence (default daily after the load, a decided line):

```bash
mb collection create --body '{"name":"<domain>"}' --namespace transforms
mb transform-tag create --body '{"name":"<domain>"}'
mb transform-job create --body '{"name":"<domain> daily","schedule":"<quartz cron after the load>","tag_ids":[<tag-id>]}'
```

Transforms are created untagged and join the tag only when approved in §7, so no scheduled run builds an untested or unapproved model. Ids go into the state file; one build-list row per model in dependency order, `cfg_<domain>` first when warranted, snapshot and history models (`references/time-and-entities.md`) in the layer that needs them when the source keeps no history.

## 3. Describe, then build on a slice

Write the description (`./.scratch/<model>.desc`, `references/modeling.md`, The description), then the SQL (`./.scratch/<model>.sql`), aliasing every table and qualifying every column by alias. Validate on a bounded predicate (a recent window or one entity) through `q()` until the shape is right and the gate's checks pass on the slice; drop the predicate and create:

```bash
source ./.scratch/probe.sh
jq -n --argjson src "$(src ./.scratch/<model>.sql)" --rawfile d ./.scratch/<model>.desc --argjson db "$DB" \
  '{name:"<model>", description:$d, collection_id:<transforms-collection-id>, owner_email:"<owner>", source:$src,
    target:{type:"table", database:$db, schema:"<out_schema>", name:"<model>"}}' > ./.scratch/<model>.transform.json
mb transform create --file ./.scratch/<model>.transform.json --profile "$PROFILE" --json | jq '{id, target}'
```

An MBQL source is validated by the create itself (`SKILL.md`, mb conventions). A rule discovered mid-layer that moves a headline past materiality is a stop where it was found.

## 4. Test

Per `references/transform-tests.md`, before the first run. Red is fixed in the SQL with a source-only patch, never in the test:

```bash
source ./.scratch/probe.sh
jq -n --argjson src "$(src ./.scratch/<model>.sql)" '{source:$src}' > ./.scratch/<model>.patch.json
mb transform update <transform-id> --file ./.scratch/<model>.patch.json --profile "$PROFILE" --json
```

For "test this transform" or "it gets case X wrong" on a live model: its tests as they stand, the case added and failing, then the fix through `playbooks/change.md`.

## 5. Run

`mb transform run <id> --sync` (read `.final.status`, `.target_table_id`, `.final.message`), then `mb table update <table-id> --body '{"data_layer":"internal"}'` on a new table until §7. A null `target_table_id` means still registering (`mb transform get <id> --fields target_table_id`). A failure: read `final.message`, fix, patch, rerun (unreadable: `transform` skill, "Iterating on a failing transform"); a changed column shape needs `mb transform delete-table <id> --yes` first.

## 6. Gate

`references/quality-checks.md`, one query per model, plus its beyond-structure block. A blocking failure stops the chain: a build bug is fixed and rerun; one whose fix needs a business rule is a stop. A decision taken here adds its case to the test. Results go in the build list.

## 7. Go-live approval

At the end of each layer: print per model its one row per what, rows, tests and the rules they pin, gate results, and the diff against anything it replaces on the grain, plus every raw table you would hide and what reads it (`references/reconciliation.md`, Compare at the finest shared grain); then one `AskUserQuestion`: make these live (Recommended) / hold one back / change a rule. Nothing more runs in that response.

On yes: tag each approved transform into the job (`mb transform update <id> --body '{"tag_ids":[<tag-id>]}'`); per final table set `data_layer: final`, `description` (grain, scope, required filters), `caveats`, `owner_email`, a readable display name; staging, intermediate, and constants stay `internal`; a raw table a final one replaces becomes `hidden` once nothing people read depends on it. Rules the owner has not decided stay open decisions with a plain sentence in the table's caveats. On staging, this approval also gates the export (`playbooks/sync.md`).

## 8. Schedule, run once, leave a check

`mb transform-job transforms <job-id>` lists every model; `mb transform-job run <job-id>` returns immediately, so poll `mb transform runs --transform-id <id>` until each succeeded. Keep full rebuilds unless the first run's duration argues otherwise (`references/modeling.md`, Materialization). Then the domain's standing check and alert (`references/quality-checks.md`, The standing check).

## Done when

Every build-list row has transform, table, rows, `tests`, and a gate without blocking failures; the owner approved every layer that went live; the job ran once, every member succeeded; plumbing internal; descriptions carry grain, scope, caveats; history capture runs where needed; the check card and alert exist. Hand-back: what one row of each table is, the rules tested, checks and counts, which period is last complete and why, a link per transform (`/data-studio/transforms/<id>/inspect`).
