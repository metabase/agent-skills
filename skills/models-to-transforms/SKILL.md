---
name: models-to-transforms
description: Plan and run the migration of Metabase models (cards with type "model") to Library-published tables. Each model is mapped 1:1 onto an existing warehouse table, or replaced by a transform whose output table takes its place. Every downstream question, dashboard, metric, filter, alert and action is re-pointed, a git PR is opened for remote-synced content, migration docs are written for everything else, and finally the models are archived and later deleted. Use whenever someone wants to deprecate, retire, migrate, replace or remove Metabase models; convert models to transforms or published Library tables (one or in bulk); replace a model as a data source; or asks what happens to bookmarks, actions, caching, model persistence, filters or dashboards when a model goes away. That includes a single model, and requests phrased in terms of the `mb` CLI or remote sync. Not for publishing tables or swapping table sources when no model is involved.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Migrate Metabase models to transforms and Library tables

Metabase is phasing models out in favor of **transforms** (a query materialized as a real table) and the **Library**
(a curated set of published tables, metrics and dashboards). This skill takes an instance from content built on
models to content built on published tables, without breaking what people use, and leaves a paper trail.

What you hand back, in order:

1. An **inventory** of every model and how it maps to a table, and a **plan** the user approves.
2. **Git PRs** for everything that is remote-synced: transforms, tags, published-table and field metadata, synced dependents.
3. **Instance-side changes**, made only with approval: dependents re-pointed, leftovers fixed, results verified.
4. **Migration docs** for everything git doesn't carry: what changed, for whom, how to roll back, and who to tell.
5. The models **archived** (Trash), then **hard-deleted** after a grace period the user confirms.

If models, published tables, transforms, the Library or "replace data source" are fuzzy for you, read
`references/concepts.md` first. Claims in the references were checked against Metabase's source and a production
instance. Anything marked **[unverified]** needs a test on a rehearsal instance before you rely on it.

`<skill>` below means this skill's folder. Run every command from the user's work directory, usually the repo, never from `<skill>`.

## Ground rules

These exist because the operations are bulk, production-wide and mostly irreversible.

- **Stay read-only until the plan is approved.** Inventory, classification and planning need no writes. Before each
  write batch on a shared instance, show the exact command or request body and get a yes. Ask once, up front, how
  coarse approvals may be (per model, per wave, per kind of change), and never widen that yourself.
- **Never merge, approve or auto-merge a PR yourself.** On an instance that auto-imports from git, merging *is* the
  production deploy. The user merges. You then watch the import (`mb git-sync status`) before any instance-side step.
- **Archive; never hard-delete before the grace period ends.** A hard delete cascades to dashcards, chart series,
  bookmarks, alerts, actions and action buttons, model indexes, filter-value links and **sandboxes**. When a sandbox
  card is deleted, its group silently gets *unrestricted* access to the table. Archived cards keep serving their
  dependents and can be restored.
- **Don't convert models to questions (`type: question`), and don't use `POST /api/ee/replacement/replace-model-with-transform`.**
  The type change hard-deletes the model's dashboard action buttons and implicit actions. The all-in-one endpoint skips
  the compatibility check and the "target already exists" guard, publishes nothing, schedules nothing, and on a
  remote-synced instance creates a transform git doesn't know about, which blocks every import. Build the table first,
  swap with `replace-source`, then archive. `references/replacement-api.md` explains why.
- **On a read-only remote-sync instance, synced things change only through the repo.** That covers transforms, tags and
  tests (when transform sync is on), Library collections, published-table and field metadata, model-less actions, and
  cards and dashboards in synced collections. Writing them through the API either fails or silently diverges from git.
  Unsynced content, permissions and transform jobs (jobs never sync) are changed on the instance.
- **Transform targets must be brand-new tables.** Only `POST /api/transform` refuses an existing target. An imported YAML
  or the replacement endpoint silently replaces whatever table is there, dbt tables included. Check the name against
  Metabase metadata **and** the warehouse, case-insensitively, again right before merge and again before the first run.
- **Transforms read tables, never cards.** No `source-card`, no `{{#123}}`. A transform that reads the model can't
  replace it (`cycle-detected`). A card reference also breaks git self-containment, and it lets a later swap of that
  card rewrite your synced transform.
- **One replacement run at a time.** Runs aren't transactional, cancel doesn't revert, and no reverse swap exists.
  Snapshot what a run will touch before starting it (`references/verification-and-rollback.md`).
- **Publishing is an access grant.** Every group that can read the target Library collection gets query-builder access
  to the whole table, plus any FK-remapped upstream tables the publish cascades to. Show who gains what before you publish.

## Phase 0: Set up and detect the mode

1. **Profiles and environment.**
   - Run `mb auth list --json --fields profile,url,status,user`. Ask which profile is the **target** and whether there
     is a **rehearsal** profile (a read-write instance for trying things). Admin is required for the replacement and
     permissions APIs; publishing needs admin or data-analyst.
   - Run `env | grep -E '^(MB|METABASE)_(URL|API_KEY|PROFILE)='`. If anything is set, stop and ask the user to unset it:
     those variables silently override `--profile` for both `mb` and the helper.
   - Load `mb skills get core` if you haven't used `mb` this session.
   - Before you create or run anything on a rehearsal instance, confirm its connections don't point at a production
     warehouse. If they do, every transform run there is a production warehouse write.
2. **Capabilities.** Run `mb auth status --profile <p> --json --fields version,features,tokenFeatures`.
   - `library`: needed for published tables.
   - `transforms`, plus the per-database `transforms/table` feature (`mb db get <id> --fields features,router_user_attribute,router_database_id`).
   - `dependencyGraph` and `sourceReplacement` (the `dependencies` token feature). **If either is false, use the manual
     path** in `references/replacement-api.md` § "Without the dependencies feature", and run the inventory with `--no-deps`.
   - `remoteSync`, if content is in git. Then check `mb library get`. Create the Library only with approval.
3. **Remote sync settings.** Run `node <skill>/scripts/mb_rest.mjs --profile <p> GET /api/session/properties` and read
   `remote-sync-enabled`, `remote-sync-type`, `remote-sync-branch`, `remote-sync-auto-import` and `remote-sync-transforms`.
   `mb setting get` returns null for defaults and for values set by env var, so don't rely on it. Then run
   `mb git-sync status --json` and check whether the Library root is in `synced_collections`. That gives the **mode**:
   - **A: read-only consumer of git.** Synced changes go in PRs. If `remote-sync-transforms` is false, transforms are
     created on the instance (`mb transform create`) even in mode A. Never add transform YAML without an explicit decision:
     the next import turns transform sync on for *all* transforms. If the Library isn't synced, publishing and metadata
     happen on the instance.
   - **B: read-write, exports to git.** Build on the instance, then `mb git-sync create-branch <b>` (or
     `mb git-sync stash --new-branch <b> -m …`), `mb git-sync export-preflight`, `mb git-sync export -m "…"`, and open
     the PR from `<b>`. Load `mb skills get git-sync`.
   - **C: no remote sync.** Everything happens on the instance with `mb` and the helper. There is no PR; the docs are the record.

   Ask which **other instances import the same branch**. They receive the transforms too, and the jobs on built-in tags run there.
4. **Repo (modes A/B).** Ask for its path. `git fetch`, then branch from `origin/<remote-sync-branch>`: a stale checkout
   gives a wrong picture of what is synced. Learn the house style (branch names, PR title and body, how schedules and
   owners are described) from recent merged PRs. Stage explicit paths only.
5. **App DB shortcut.** Some instances have their own application database connected as a data source. If so, inventory
   is a few SQL queries instead of thousands of API calls, and it sees more. Look for a database with `report_card`,
   `dependency` and `metabase_table` tables. `inventory.py --app-db` checks that it really is *this* instance's live
   primary by matching card ids, names and entity ids against the API. It is production: SELECT only, through
   `inventory.py --sql` (which refuses anything else).
6. **Work dir.** Keep all state in `./.scratch/model-migration/`: inventory, decisions, plan, snapshots, REST log, and
   `state.json` with per-model status, so work can resume across sessions. Add `.scratch/` to `.git/info/exclude`
   before writing anything, and never commit it.

`<skill>/scripts/mb_rest.mjs` calls REST endpoints that have no `mb` verb, with the profile's own credentials, so the
user pastes nothing.
- It allows GET, plus the read-only `check-replace-source` POST.
- Any other method needs `--allow-write "<METHOD> <path>"` naming the exact approved call.
- Every call is logged.

Prefer `mb` verbs wherever one exists.

### Where each change is made

| Change | Mode A (read-only) | Mode B (read-write) | Mode C (no sync) |
|---|---|---|---|
| Transforms, tags, tests | PR (if transform sync is on) | instance, then export | instance |
| Transform jobs (schedules) | instance | instance | instance |
| Publish, table and field metadata (Library synced) | PR | instance, then export | instance |
| Synced dependents (cards, dashboards, metrics) | PR | swap on instance, ship in export | n/a |
| Unsynced dependents, leftovers | instance | instance | instance |
| Permissions, sandboxes, alerts, bookmarks | instance (never synced) | instance | instance |
| Archive and purge of a synced model | PR deleting its file = hard delete; wait for the purge date | archive on instance, export at the purge date | n/a |

## Phase 1: Inventory

Run `python3 <skill>/scripts/inventory.py --profile <p> --out ./.scratch/model-migration/inventory`.

- Add `--app-db <id>` when step 5 found the app DB.
- Add `--include-archived` to also cover models already in the Trash: some still feed live cards.
- On the API path, add `--extras` to collect actions, model indexes, cache configs, alerts and sandboxes.

The script writes `models.csv` (one row per model), `models.jsonl` (raw), `model_edges.csv` (the model→model DAG,
including models reached through saved questions), `failures.csv` and `summary.md`.

**It exits 3 when anything couldn't be read.** Read `summary.md` and `failures.csv`, resolve the failures, and re-run.
Don't classify on a partial inventory. Tell the user plainly what the run couldn't see: on the API path, other users'
bookmarks, subscriptions and archived dependents. `references/inventory-and-classification.md` covers what each path
sees and gives the gate SQL.

## Phase 2: Classify and propose

The script assigns each model a **class** and a proposed **action**:

| Class | Shape | Usual action |
|---|---|---|
| T1 | MBQL on one table, only `fields` / `order-by` / `limit` | swap to that table |
| T2 | native `SELECT * / plain column list FROM one_table` | swap to that table (check the parse confidence) |
| T3 | built on an uploaded CSV table | swap if it's a wrapper, else transform |
| T4 | derived MBQL: joins, filters, expressions, aggregations, stages | new transform |
| T5 | derived native SQL | new SQL transform |
| T6 | reads another card (`source-card`, joins, `{{#id}}`) | waits for its upstream models (re-classify after their wave); with only saved-question upstreams, inline them, or swap through a wrapper question |
| T7 | wrapper of a table that already is a transform's output | swap to that table |

The action can instead be one of these:

- `archive: unused` (no use for N days, no dependents, no direct use);
- `exclude` (Metabase-managed usage analytics);
- `broken`;
- `blocked` (the database can't host transforms at all, a sandbox card, an upstream that won't migrate);
- `review` (LIMIT wrappers, unparsed queries, unreadable upstreams, archived models still used by buttons or filters);
- `swap-archived-feeder` / `purge-candidate`, for models already in the Trash.

Flags predict `check-replace-source` failures (missing columns, missing FK metadata) and user-visible metadata changes.
They also mark things to raise in the interview:
- a model that builds on another transform's output: extending that transform may beat adding a new one;
- coerced source columns the transform must cast;
- wrappers whose `ORDER BY` or `LIMIT` a swap drops;
- a target database that is the instance's own app DB, or one no transform has written to yet.

**There is no "convert to a saved question" end state.** A model with logic becomes a transform-backed table, a 1:1
wrapper is swapped onto its table, and an unused model is archived. This holds for awkward cases too. The instance's
own app DB gets a transform into a dedicated schema the user confirms once. A database no transform has written to gets
a transform after you prove a writable schema. Only databases that can't host transforms at all (no `transforms/table`,
audit, sample, DB routing) fall back to archiving, or to keeping the model, listed with the reason.

Order the work in **waves** along the model→model DAG. Wave 0 holds models whose sources are tables or saved questions.
Wave *k* runs after wave *k−1* is swapped.

## Phase 3: Ask what the model can't tell you

Run the interview in `references/interview.md`. Propose a default for every question from the inventory, and ask only
what is genuinely the user's call:

- scope, archived models and archive candidates;
- the target schema per database, naming, transforms folder and owner (scheduled runs execute as the owner);
- schedule and freshness;
- Library folder and table metadata (display name, description, owner, visibility layer);
- metadata conflicts;
- access;
- what to do about actions, model indexes, uploads, verification, bookmarks, alerts, public links and dashcards that show the model;
- databases not to write to;
- column renames;
- other instances on the branch;
- where the docs go;
- the grace period.

Use AskUserQuestion for policies, a few at a time, with your recommendation first. For per-model exceptions, write
`decisions.csv` with your proposal on every row, and ask the user to review only the flagged rows.

**Freshness is where people get surprised.** A model without persistence or a cache policy is a live query; a transform
table is a snapshot. Derive the proposed schedule from evidence: model persistence and its cron, `cache_config` on the
model, the consumers' policies (`consumer_cache` in models.csv), the database policy, upstream transform schedules, and
usage. State what you inferred and why (`references/transforms-and-scheduling.md`).

## Phase 4: Write the plan and get it approved

Write `./.scratch/model-migration/plan.md`. It holds:

- scope and counts by class and action;
- wave 0 in full, later waves as estimates;
- the PRs and what each carries;
- the instance-side runs, with dependent counts;
- what users will notice: freshness, access, bookmarks, links, action buttons, Metabot;
- rollback;
- open risks;
- the decisions.

Every number must say what it counts: active vs. archived, direct vs. transitive. Don't start Phase 5 without an
explicit go-ahead.

## Phase 5: Make the tables exist and look right (per wave)

Before anything is re-pointed, every target table must:

- exist;
- carry the right metadata;
- be published in the agreed Library folder;
- be queryable by the people who used the model.

Publishing first matters for two reasons. Library read access is how people without "create queries" keep exploring.
And the swap's compatibility check needs the table's **FK semantics** (semantic type and target) in place. Entity keys
don't gate a card→table swap, but add them for implicit joins and detail views.

1. **Access gate before publishing.** List the tables the publish touches, including FK-remap upstream tables, and the
   groups that can read the target Library collection. Note which groups lack create-queries today, which columns
   become explorable that the model hid, and which groups are blocked or sandboxed on the database. Show this, and get
   approval. Never publish with a null collection. A new transform table gets database-level permissions only:
   table-level grants on the model's source table must be re-granted. The permission and sandbox recipes are in
   `references/edge-cases.md` § Permissions.
2. **Existing tables** (T1/T2/T3/T7):
   - publish if not yet published;
   - set table metadata;
   - promote the model's column overrides where the user agreed. Edit existing metadata files in place and never
     overwrite them with minimal ones; never change `visibility_type` on a shared table;
   - add the FK semantics the model had.
3. **New transforms** (T3-derived/T4/T5, and T6 once re-classified):
   - author them from the model's own query, rewritten to read only tables;
   - give each a fresh target name, the agreed folder, a tag whose job is **active**, and an owner who can run it;
   - run it once, then compare it with the model;
   - then do the same metadata and publish steps as above. Pin it with a transform test where the engine supports one.

Per mode (`references/git-sync-and-yaml.md` has YAML shapes and PR structure):

- **Mode A**:
  1. PR 1 adds the transforms, tags and tests. The user merges it; you watch the import succeed.
  2. Run each transform on the instance (`mb transform run <id> --sync`, with approval) and verify it.
  3. PR 2 adds the publish metadata (TableUserSettings / FieldUserSettings YAML), FK fixes, synced dependents and metric
     dimensions. Wrapper-only waves need only PR 2.
  4. Create jobs for new schedules on the instance.
- **Mode B**: `mb transform create/run`, `table update`, `field update`, then publish into the agreed folder:
  `POST /api/ee/data-studio/table/publish-tables {"table_ids":[…],"collection_id":<folder>}` through the helper. Or run
  `mb library publish` and then `mb table update <T> --body '{"collection_id":<folder>}'`; the first step briefly
  exposes the table to everyone who can read Library > Data. Export to the feature branch and open the PR. Revert
  serializer churn the change didn't cause.
- **Mode C**: the same commands, with no PR.

**Watch the transform output column names.** The swap matches columns by exact, case-sensitive name. Redshift
lower-cases, BigQuery escapes, and long aliases are truncated. After the first run, compare the output fields with the
model's column keys. Read `references/transforms-and-scheduling.md` before authoring any transform.

## Phase 6: Cut over, one model at a time, in wave order

For each model (details in `references/replacement-api.md` and `references/edge-cases.md`):

1. **Gate.** All of these must hold:
   - the target exists, is published, and has its permissions and sandboxes set;
   - no other replacement run is active;
   - **mode A:** no remote-synced entity is in the model's closure (any `remote_sync_object` status but `removed`).
     Synced dependents go in a PR first. **Mode B:** synced dependents may be swapped; review `mb git-sync dirty` afterwards;
   - the closure fits the 30-minute run limit;
   - text references with no dependency edge are listed for manual fixing;
   - the user approved this run, or its batch.
2. **Snapshot** the closure: every card, dashboard (with `tabs`) and filter source a run can touch, plus the model
   itself, its actions in any state, its dashcards, series and alerts, and the affected metrics' dimensions. Capture
   "before" results for a sample of dependents.
3. **Check.** `check-replace-source` (read-only) must return `success: true`, with every column mapped and no per-column
   errors. Fix the table (FK semantics) or the plan; never force it.
4. **Swap.** Run `replace-source` from card to table, then poll `GET /runs/:id` until the run is terminal. `failed`,
   `timeout` and `canceled` all mean *partially applied*: read the message, fix the cause, and re-run.
5. **Leftovers** the swap doesn't touch:
   - dashcards that show the model, and chart **series** that include it;
   - filters whose dropdown values come from it;
   - click behaviors and link cards;
   - `/model/<id>` URLs;
   - snippets;
   - alerts on it;
   - its actions and action buttons;
   - curated metric dimensions;
   - sandboxes.

   `references/edge-cases.md` has a recipe for each, including the dashboard `tabs` trap and how to keep a re-created
   alert's permissions.
6. **Verify.**
   - Compare "after" results with the snapshot.
   - Confirm nothing references the model anymore. Stale editors can re-save an old version.
   - Run `mb dependency broken table <T>` and compare `mb dependency breaking` with the pre-wave baseline.
   - Mark the model `swapped` in `state.json`.

**Loop.** When every model in wave *k* is `swapped`, re-run the inventory (`--ids` for wave *k+1*), re-classify,
append wave *k+1*'s transforms and PRs to `plan.md`, and get approval before starting Phase 5 for it.

## Phase 7: Write the migration docs

Fill in `references/migration-docs-template.md`:

- a summary;
- a per-model record: decision, table, PR links, run ids, entities rewritten, leftovers fixed, what was lost;
- user-visible changes;
- jobs created;
- rollback;
- notification lists: bookmark holders, alert recipients, owners of affected dashboards, heavy viewers.

In modes A and B, the docs go in a docs-only PR under a folder outside the serialized top-level directories (e.g.
`docs/model-migration/`), opened after Phase 6 and updated after Phase 8 and after the purge. In mode C, put them where
the user chose. Keep personal data such as emails out of git unless the user explicitly wants it there.

## Phase 8: Remove the models

1. **Pre-archive gate**, per model. Every item must read zero, or be explicitly accepted by the user, by name:
   - dependency edges from live entities;
   - cards whose query text still references the model, archived ones included;
   - dashcards and chart series showing it;
   - filter sources;
   - sandboxes using it;
   - alerts;
   - subscriptions containing it;
   - actions in **any** state, and the dashboard **action buttons** that run them;
   - model indexes;
   - a public link or embedding.

   The SQL is in `references/inventory-and-classification.md`.
2. **Synced models.** Archiving a synced model removes its file at the next export (mode B), and a PR that deletes the
   file (mode A) hard-deletes it on every instance that imports the branch. There is no Trash on that path. So keep
   synced models in place, unarchived, until the purge date, then handle them in step 5.
3. **Archive** unsynced models with `mb card archive <id>`, in batches the user approved. Archiving deletes the card's
   alerts (and emails recipients), resets filters that took values from it, hides its dashcards and bookmarks, and
   archives its actions. Their buttons keep working until the purge, which is why the gate comes first.
4. Record the archive time per model, update the docs, and tell the user the purge date.
5. **Purge** after the grace period, and only when the user re-invokes and confirms.
   - Re-verify the app DB (if used), then re-run the gate for each model.
   - Skip anything restored, newly referenced, made public, or now remote-synced. **Never** delete a card that a
     sandbox uses, or one whose actions still back buttons.
   - Right before each delete, snapshot it to `snapshots/purge/<id>/`: `mb card get --full`, actions in any state,
     dashcards including buttons and series, sandboxes, filter sources, subscriptions, bookmarks, and its sync status.
   - Then run `DELETE /api/card/:id` through the helper (for synced models in mode A, the file-deleting PR), and record it in the docs.

Already-archived models from `--include-archived`:

- `purge-candidate`: purge it under the same rules.
- `swap-archived-feeder`: goes through Phases 5–6 first. Swapping from an archived source works.
- `review`: decide case by case.

## Resuming and scale

Expect hundreds of models. Batch PRs by wave and by Library or transforms folder, not one per model. Keep `state.json`
current per model: class, action, wave, target table, PR, run ids, status, archive time and purge time. When
re-invoked, read it first, and recompute only what may have changed: new models, new dependents, merged PRs.

## Don't

- Don't infer that something is synced from a collection name. Use `synced_collections` from `mb git-sync status`, or `remote_sync_object` on the app DB.
- Don't run `git-sync import --force`, or export to the tracked main branch, without explicit approval.
- Don't trust `mb search` past 1,000 results, and remember it hides the usage-analytics namespace. The inventory script handles both.
- Don't treat `mb card query` JSON as a correctness check. It caps rows and may serve cached results; use `--export-format csv`.
- Don't paste compiled SQL (`mb query --compile`) into a transform you want to test. It is table-qualified, which transform tests refuse.
- Don't revert a transforms or publish PR after cut-over. Swapped content depends on it. Fix forward instead.
