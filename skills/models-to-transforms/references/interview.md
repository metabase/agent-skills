# The interview: what to ask, with what default

Ask only what the inventory can't answer, and always propose an answer. Use AskUserQuestion for policies, at most four
per call, with your recommendation as the first option and "(Recommended)" in its label. For anything per-model, write
`decisions.csv` with your proposal on every row, flag the rows that need a human, and ask the user to review just those.
Record every answer in `plan.md`, under "Decisions", each named by its subject (never `D3`). Ask everything here,
before the plan: the user's yes to the plan is the last approval until the purge, so nothing may be left for "when
we get there".

Ask in roughly this order, because later answers depend on earlier ones.

## 1. Scope and approvals

| Question | Default / how to infer |
|---|---|
| Which models are in scope: all, some collections, some databases? | all active models, minus excluded and broken |
| Include models in **personal collections**? | yes if they have active dependents, otherwise archive-candidate |
| Include **archived models that still feed active content**? (run the inventory with `--include-archived`) | yes, swap them (`swap-archived-feeder`). Their dependents rely on them silently. Already-archived models with nothing depending on them are `purge-candidate`s: purge them with the rest |
| **Archive candidates** (unused ≥ N days, no active dependents, no direct use): archive without migrating? Which N? | yes, N = 180. Show the count and the top ones by past views |
| Who **merges the pull requests** (with remote sync)? | the user, from each pull request's page, when you say it's ready: on an auto-importing instance the merge is the production deploy, and the repo's reviewers see it. Or you, once the checks pass, if the user would rather not be asked again. Where there is no pull-request page (a bare remote), merging is a push, and it's yours. Either way, the user runs no command, and the plan is the only approval |
| Which profile is the target, and is there a rehearsal (read-write) instance? Does it share the production warehouse? | from `mb auth list`. Ask: never assume |
| Which **other instances import the same branch**, and do they share the warehouse? | ask. For each one, list the jobs on the tags you plan to use. Either disable them there, or use a new tag with a job only on the target |

## 2. Where and how tables get built

| Question | Default / how to infer |
|---|---|
| Target **schema** per database | the schema existing transforms already write to; otherwise ask. Never a schema owned by dbt or another tool |
| **Naming** convention for transform tables | snake_case of the model name minus noise ("- Wide Format", "(new)"); check uniqueness |
| **Transforms folder** | by domain, mirroring the Library folder |
| **Owner** of the transforms (scheduled runs execute as the owner) | the user, if they are an admin; never an API-key user. Confirm the email exists on the instance |
| **Schedule** per model or group | from the evidence in `transforms-and-scheduling.md`. Always show the evidence; ask when the model was live, or when the upstream load time is unknown |
| **Incremental?** | no, unless the table is large and append-only with a clear checkpoint |
| Databases **not to write to** (Metabase app DBs, production OLTP, test databases) | the default is still a transform (never "convert to a saved question"). For the instance's own app DB, propose a dedicated schema (e.g. `mb_transforms`) and confirm it once. For a database no transform has written to, prove a writable schema with a tiny test transform (on rehearsal, or on the target as a plan item) before authoring the rest. Test databases: archive their models if unused |
| A model that **builds on another transform's output** | new transform on the same tag as the upstream (default) / extend the upstream transform (needs its owner's OK) / swap onto the upstream table if all columns exist |
| Models on databases **without transform support** | keep as a model for now, or archive if unused. Never silently drop them |
| **Column names**: keep the model's exact names, or clean them up? | keep exact. Cleaning means hand-rewriting every dependent's refs |
| **Dedupe**: several models wrap the same table | swap all of them onto that table; merge their column-metadata wishes, and ask on conflicts |

## 3. Publishing and metadata

The published-tables docs list what a published table carries. Ask only for what you can't fill from the model.

| Question | Default / how to infer |
|---|---|
| **Library Data folder** per table | the folder where tables of the same schema or source are already published. Ask when it's mixed or there are none |
| **Table display name** | the model's name, which is what users know, unless a published table already has a name people use |
| **Table description** | the model's description, rewritten to state grain, key and caveats; append "Replaces the <model> model." Ask for models with no description |
| **Table owner** (person or email; shown in Data Studio) | the model's creator if still active, otherwise ask |
| **Visibility layer** (`data_layer`) | `final`, which Metabot's curated mode counts. `internal` for intermediate tables |
| **Entity type** | let sync detect it; ask only when the model's purpose is obvious and the detected type is generic |
| **Field metadata conflicts**: the model overrides display names, semantic types, descriptions, formatting or FK targets that differ from the table's | promote the overrides onto the table where the table's own value was never set by a person; flag conflicts, including those between several models on one table. Tell the user that table metadata is **global**, unlike model metadata |
| **FK / entity-key semantics** the model had but the table lacks | add them: required for the swap check and for implicit joins. Point FK targets at published tables |
| **Segments / measures** worth defining on the table (e.g. a model that was just a filter of a table) | offer it, when a derived MBQL model is a single filter over a published table: a segment may serve better than a new transform |

## 4. Access

| Question | Default / how to infer |
|---|---|
| Who must keep **ad-hoc exploration** (people who used the model without "create queries")? | grant read on the table's Library collection to the groups that could read the model's collection |
| Groups with **blocked or sandboxed** tables in the database | set view-data and sandboxes on each new table before the swap. List the groups that would lose access |
| Swapping to a **wider existing table** that exposes columns the model hid | list those columns. To keep them hidden, use permissions (a sandbox with a column subset), or keep a narrow transform instead of swapping. Never change `visibility_type` on a shared table. Before promoting any model override onto an existing table, show how many other things use that table (`mb dependency dependents table <T> --include-personal-collections`) |
| Groups with **impersonation** on the database | a transform table doesn't carry warehouse row/column security from its sources. Keep the model, or build per-role transforms, unless the sources have no RLS for those roles |

## 5. Model-only features (one answer per feature, with per-model exceptions)

| Feature | Options (default first) |
|---|---|
| **Dashcards showing the model** | replace with a new question on the table, in the model's collection / in the dashboard; or remove the card |
| **Filter value sources** from the model | use the mapped field's own values / a question on the table / a static list |
| **Query actions** | re-home them as model-less data actions (data-actions collections only; Library content, so synced when the Library is) / recreate them / keep the model until later |
| **Implicit actions and their buttons** | recreate them as query actions on the source table / table data editing / keep the model (it then isn't removed) |
| **Model indexes** | accept the loss and notify / keep the model |
| **Upload-backed models** | swap and document `mb upload append|replace` / keep the model if people append via the UI often |
| **Replacement questions** (for dashcards, filter values, links, alerts) | verified, as standing in for the model (the default, whether or not the model was verified) / left unverified |
| **Alerts on the model** | recreate them on a replacement question with the **original creator** (`PUT /api/notification/:id {"creator_id": …}`), after showing recipients the two emails they'll get / let them go, with notice |
| **Public links / embeds of the model** | create them on the replacement question and tell the owners / drop them |
| **Bookmarks** | notify holders, with the new location / no notice |
| **Metric dimensions** on metrics built on models | re-target them to the table / re-seed and re-curate |

## 6. Records and removal

| Question | Default |
|---|---|
| Where do the **migration docs** go: a folder in the PR, a separate doc, both? | with remote sync: `docs/model-migration/` (outside the serialized top-level dirs) in a docs-only pull request, opened after the cut-over and updated after the archive and the purge; without it: where the user picks. Notification lists stay outside git |
| **Notify** users? How: list only, draft messages? | produce lists and draft messages. Sending is the user's job |
| **Grace period** between archive and hard delete | 30 days. The user confirms the purge when it comes |
| Keep any model on purpose (actions, indexes, blocked DBs)? | yes, list them as "kept" with the reason. "Remove all models" still means "all that can go" |

## Inference shortcuts worth stating out loud

- The model's `description`, `name`, `collection` and `creator` seed the table's description, display name, Library
  folder and owner.
- `result_metadata` overrides seed the field metadata. Diff them against the table's current field metadata and show
  only the differences.
- A model persisted at instance cron X means its consumers already accept staleness of X.
- A model on a table that is already a transform output (a transform-output wrapper) inherits that transform's schedule. There's nothing to choose.
- Several models over one table with no differences in metadata need one decision, not several.
