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

1. An **inventory** of every model and how it maps to a table, and a **plan** the user approves **once**. It shows,
   for every model and everything built on it, what it is now and what it will be.
2. **Git PRs** for everything that is remote-synced: transforms, tags, published-table and field metadata, synced dependents.
3. **Instance-side changes**, carried out as the plan says: dependents re-pointed, leftovers fixed, results verified.
   The user runs nothing.
4. **Migration docs** for everything git doesn't carry: what changed, for whom, how to roll back, and who to tell.
5. The models **archived** (Trash), then **hard-deleted** after a grace period the user confirms.

If models, published tables, transforms, the Library or "replace data source" are fuzzy for you, read
`references/concepts.md` first. Claims in the references were checked against Metabase's source and a production
instance. Anything marked **[unverified]** needs a test on a rehearsal instance before you rely on it.

`<skill>` below means this skill's folder. Run every command from the user's work directory, usually the repo, never from `<skill>`.

## Ground rules

These exist because the operations are bulk, production-wide and mostly irreversible.

- **Stay read-only until the plan is approved, then run the plan to the end.** Inventory, classification and
  planning need no writes. The plan is the one approval: it lists everything that will be created, changed, re-pointed
  and archived, the before and after of each, and the user's own steps (see "Plan"). After the yes, carry it out
  without asking again, waves included. Come back only for what the plan's stop rules name, and for the purge. Never
  widen the plan yourself: anything it doesn't cover is a stop, not a judgment call.
- **The user runs no commands.** Every `mb`, helper and git command is yours, with the profile's own credentials: the
  import, the transform runs, the swaps, the archive. What stays with the user is the plan's yes, merging the pull
  requests when the plan gives them that, and the purge confirmation after the grace period. Never hand the user a
  command to run.
- **Merging is whoever the plan says.** On an instance that auto-imports from git, merging *is* the production
  deploy, so by default the user merges, from the pull request's page, when you say it's ready. When the user chose in
  the plan that you merge, or when there is no pull-request page and merging is a push, you do it, for the pull
  requests the plan lists and nothing else. Never auto-merge or force-push. After each merge, watch the import
  (`mb git-sync status`), or run it yourself (`mb git-sync import --profile <p>`, the tracked branch) on an instance
  that doesn't auto-import, before any instance-side step.
- **Archive; never hard-delete before the grace period ends.** A hard delete cascades to dashcards, chart series,
  bookmarks, alerts, actions and action buttons, model indexes, filter-value links and **sandboxes**. When a sandbox
  card is deleted, its group silently gets *unrestricted* access to the table. Archived cards keep serving their
  dependents and can be restored.
- **Convert a model to a question only on the verified-question path, and never use `POST /api/ee/replacement/replace-model-with-transform`.**
  A simple model (one table, no joins or aggregation) stays where it is, as the same card, converted to a question and
  verified (see "Simple models"). Everything else is replaced by a table. The type change hard-deletes the model's
  dashboard action buttons and implicit actions, so re-home those first. The all-in-one endpoint skips
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

## What the user reads

The user never reads this skill. They read your messages, the approval prompts, `plan.md`, `decisions.csv`, the pull
requests, the branch and commit names, and the migration docs. All of it names things by what they are and what they
do. The skill's shorthand (class slugs, "wave k", the section names here, any batch or decision numbering of your own)
is for you and the CSV files; the user gets words.

| Never write | Write |
|---|---|
| `W2`, `W0-2`, `PR 1`, `PR 2` | the pull request's title: "Add transforms for Charges, Scored Issues and 8 more models", "Publish 7 tables in the Library and carry the models' column metadata" |
| `T5`, `derived-sql` | what the model is: "a 1:1 wrapper of `dbt_models.account`", "a SQL model that joins deals and accounts" |
| `mode A` | what it means here: "your instance imports from git and is read-only, so transforms go in through a pull request" |
| `Phase 5`, `step 3` | what happens: "build the tables", "re-point everything built on Contact", "archive the models" |
| `D5`, `batch B` | the decision by its subject ("the column-metadata decision: the table wins conflicts"); the batch by its content ("the 8 models whose tables were published this morning") |
| `w0`, `inventory_w1`, `library/w1-publish` | `wave-0`, `inventory-wave-1`, `model-migration/publish-tables` (within the house style) |
| "approve wave 2", "batch B needs your go-ahead", "run `mb git-sync import …`" | nothing. The plan was approved once and you run the commands. If something is off, say what, and ask about that |

"Wave" is fine, spelled out and introduced by what it holds: "wave 0: the 39 models that read tables directly",
"wave 1: the 11 models built on wave-0 models". It names your order of work, never an approval.

The plan is the one request for a yes; its shape is under "Plan". When a stop rule brings you back, the message says,
in this order:

1. **What happened**, and what the plan assumed instead ("the swap check for Contact fails: the table has no
   `owner_id` column; the plan assumed the model's 14 columns all exist on `dbt_models.contact`").
2. **What you propose**, concretely: the command or request body, and what it touches by name and count.
3. **What changes for people**, if anything: freshness, access, column names, links, buttons.
4. **What the user has to do**: usually pick an option, or say yes. "Nothing" is an answer.
5. **What comes after**, and how to undo it.

Every hand-off (a pull request for the user to merge) says what it contains, what to check, what merging does (on an
instance that auto-imports, merging is the production deploy), and what you'll do once it's in, without any step for
the user beyond the merge. From the message alone, the user can answer "what am I agreeing to, and what do I have to
do?".

## Set up

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
   - `remoteSync`, if content is in git. Then check `mb library get`. Creating the Library is a plan item, never a
     side effect.
3. **Remote sync settings.** Run `node <skill>/scripts/mb_rest.mjs --profile <p> GET /api/session/properties` and read
   `remote-sync-enabled`, `remote-sync-type`, `remote-sync-branch`, `remote-sync-auto-import` and `remote-sync-transforms`.
   `mb setting get` returns null for defaults and for values set by env var, so don't rely on it. Then run
   `mb git-sync status --json` and check whether the Library root is in `synced_collections`. That tells you how the
   instance relates to git, which decides where each change is made:
   - **Read-only sync**: the instance imports from git and can't export. Synced changes go in pull requests. If
     `remote-sync-transforms` is false, transforms are created on the instance (`mb transform create`) even here. Never
     add transform YAML without an explicit decision: the next import turns transform sync on for *all* transforms. If
     the Library isn't synced, publishing and metadata happen on the instance.
   - **Read-write sync**: the instance exports to git. Build on the instance, then `mb git-sync create-branch <b>` (or
     `mb git-sync stash --new-branch <b> -m …`), `mb git-sync export-preflight`, `mb git-sync export -m "…"`, and open
     the pull request from `<b>`. Load `mb skills get git-sync`.
   - **No remote sync**: everything happens on the instance with `mb` and the helper. There is no pull request; the
     docs are the record.

   Ask which **other instances import the same branch**. They receive the transforms too, and the jobs on built-in tags run there.
4. **Repo (with remote sync).** Ask for its path. `git fetch`, then branch from `origin/<remote-sync-branch>`: a stale checkout
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

| Change | Read-only sync | Read-write sync | No sync |
|---|---|---|---|
| Transforms, tags, tests | PR (if transform sync is on) | instance, then export | instance |
| Transform jobs (schedules) | instance | instance | instance |
| Publish, table and field metadata (Library synced) | PR | instance, then export | instance |
| Synced dependents (cards, dashboards, metrics) | PR | swap on instance, ship in export | n/a |
| Unsynced dependents, leftovers | instance | instance | instance |
| Permissions, sandboxes, alerts, bookmarks | instance (never synced) | instance | instance |
| Archive and purge of a synced model | PR deleting its file = hard delete; wait for the purge date | archive on instance, export at the purge date | n/a |

## Inventory

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

## Classify and propose

The script assigns each model a **class** and a proposed **action**:

| Class | Shape | Usual action |
|---|---|---|
| `table-wrapper` | MBQL on one table, only `fields` / `order-by` / `limit` | swap to that table |
| `sql-table-wrapper` | native `SELECT * / plain column list FROM one_table` | swap to that table (check the parse confidence) |
| `upload-based` | built on an uploaded CSV table | swap if it's a wrapper, else transform |
| `derived-mbql` | joins, filters, expressions, aggregations, stages | a verified question in place when it reads one table with no joins or aggregation; otherwise a new transform |
| `derived-sql` | any other native SQL | a verified question in place when it's one SELECT over one table with no joins or aggregation; otherwise a new SQL transform |
| `card-based` | reads another card (`source-card`, joins, `{{#id}}`) | classified through the tables that replace its upstream models: a wrapper of one upstream swaps onto that model's table (`swap-to-upstream-table`); anything else becomes a transform reading those tables. With only saved-question upstreams, inline them, or swap through a wrapper question |
| `transform-output-wrapper` | wrapper of a table that already is a transform's output | swap to that table |

The class is a CSV value. When you tell the user about a model, describe it instead: "a 1:1 wrapper of
`dbt_models.account`", "a SQL model that joins deals and accounts".

The action can instead be one of these:

- `convert-to-verified-question` (a simple model: one table, no joins or aggregation; it stays as the same card);
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

**End states.** Every model ends in one of four ways:

- **A 1:1 wrapper** is swapped onto its table.
- **A simple model** becomes a **verified question** in place. Simple means one table, no joins and no aggregation:
  added columns, filters, column picks and a sort are fine. Example: `select *, cast(is_trialing as bool) … from one_table`.
  It keeps its id, so everything built on it, its bookmarks, alerts and dashcards keep working with nothing re-pointed,
  and it stays a live query.
- **A model with real logic** (joins, aggregation, several stages) becomes a transform-backed table.
- **An unused model** is archived.

Nothing ends as a plain, unverified saved question. This holds for awkward cases too:
- The instance's own app DB gets a transform into a dedicated schema the user confirms once.
- A database no transform has written to gets a transform after you prove a writable schema.
- Only databases that can't host transforms at all (no `transforms/table`, audit, sample, DB routing) fall back to a
  verified question when the model is simple, else to archiving or keeping the model, listed with the reason.

Order the work in **waves** along the model→model DAG. Wave 0 holds models whose sources are tables or saved
questions. Wave *k*'s transforms run after wave *k−1*'s tables exist, and its swaps after wave *k−1*'s. Every wave is
classified, planned and approved up front, in the one plan: the script reads each card-based model's own shape over
its upstream (`upstream_shape`), and you substitute the table the plan gives that upstream. Waves order your work;
they are not approval points.

## Interview: ask what the model can't tell you

Run the interview in `references/interview.md`. Propose a default for every question from the inventory, and ask only
what is genuinely the user's call:

- scope, archived models and archive candidates;
- the target schema per database, naming, transforms folder and owner (scheduled runs execute as the owner);
- schedule and freshness;
- Library folder and table metadata (display name, description, owner, visibility layer);
- metadata conflicts;
- access;
- simple models: a verified question in place (the default), or a transform when the user wants the table materialized;
- what to do about actions, model indexes, uploads, verification, bookmarks, alerts, public links and dashcards that show the model;
- databases not to write to;
- column renames;
- other instances on the branch;
- where the docs go;
- the grace period.

Use AskUserQuestion for policies, a few at a time, with your recommendation first. For per-model exceptions, write
`decisions.csv` with your proposal on every row, and ask the user to review only the flagged rows. The interview is
where every choice gets made; the plan then carries them all, so that the user's yes to the plan is the last thing
you need until the purge.

**Freshness is where people get surprised.** A model without persistence or a cache policy is a live query; a transform
table is a snapshot. Derive the proposed schedule from evidence: model persistence and its cron, `cache_config` on the
model, the consumers' policies (`consumer_cache` in models.csv), the database policy, upstream transform schedules, and
usage. State what you inferred and why (`references/transforms-and-scheduling.md`).

## Plan: the one approval

Write `./.scratch/model-migration/plan.md`. It is the only thing the user approves, so it says, for everything the
migration touches, what it is now and what it will be, all waves included. After the yes you carry it out to the end;
you come back only for its stop rules and for the purge. It holds, in this order:

1. **Where things stand now.** The instance and its sync setup in words, the repo, and the counts: models by what they
   are, and everything built on them by kind (questions, dashboards, metrics, filters, alerts, actions and buttons,
   bookmarks, public links, sandboxes). Every number says what it counts: active vs. archived, direct vs. transitive.
2. **The end state, model by model.** For each model: what it is now ("a SQL model that joins deals and accounts, in
   Sales, a live query; 14 questions and 2 dashboards are built on it") and what replaces it
   ("`mb_transforms.deals_with_accounts`, a transform refreshed daily at 07:00 UTC, published in Library › Sales,
   owner …"; or, for a simple model, "stays as the question 'Cloud Customers Monthly Usage' in Product › Cloud, now
   verified, still live"). Then **every dependent by name**: what it reads now, what it will read, and what changes for it
   (nothing / these column names / freshness / its sort / the dashboard filter's values / its action button). Group
   by dashboard where that reads better. Above about 20 dependents on one model, keep one line per kind in the plan
   and put the full list in `changes.csv` next to it (one row per object: kind, id, name, where it lives, reads now,
   will read, what changes), and say so. Later waves get the same treatment: their upstream's table is the one the
   plan gives it.
3. **What people will notice**, in one place: freshness, access (who gains query access to which tables, and the
   columns a wider table exposes), column names, bookmarks, links, action buttons, Metabot.
4. **What you will do**, in order and in words: the pull requests, each by title and content, and who merges each;
   the transform runs; the swaps in wave order; the leftovers; the archive; the docs. Each wave introduced by what it
   holds.
5. **What the user does**, as a short list with a "when": accept this plan; merge each pull request when you say
   it's ready (or nothing, if they chose that you merge); confirm the purge after the grace period. Nothing else, and
   no commands.
6. **Stop rules**: what brings you back before you continue. At least: a swap check that fails for a reason the plan
   didn't predict; a transform whose first run doesn't match its model (rows, keys, column names); a target table
   name that turns out to be taken; a dependent the plan has no rule for (its rule for new dependents of a known kind
   is that they are re-pointed with the rest and listed in the docs); a remote-synced dependent on a read-only
   instance that no pull request in the plan carries; an access change beyond the plan's access section; an import
   that fails or conflicts; a replacement run that ends failed, timed out or canceled; anything the plan marks
   "confirm by name". Everything else, you handle and record.
7. **Rollback**, per stage.
8. **The decisions**, each by its subject, with who decided.

Ask for the yes in plain words: what you'll create and change, where, what the user does and when, and what brings
you back. Build nothing before it.

## Build the tables

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
   become explorable that the model hid, and which groups are blocked or sandboxed on the database. That list is the
   plan's access section: publish and grant only what it says, and stop if the instance now differs from it. Never
   publish with a null collection. A new transform table gets database-level permissions only: table-level grants on
   the model's source table must be re-granted. The permission and sandbox recipes are in
   `references/edge-cases.md` § Permissions.
2. **Existing tables** (every kind of wrapper: MBQL, SQL, upload-based, transform-output):
   - publish if not yet published;
   - set table metadata;
   - promote the model's column overrides where the user agreed. Edit existing metadata files in place and never
     overwrite them with minimal ones; never change `visibility_type` on a shared table;
   - add the FK semantics the model had.
3. **New transforms** (derived MBQL and SQL models, upload-based models with logic, and card-based models with logic):
   - author them from the model's own query, rewritten to read only tables. A reference to an upstream model becomes
     the table the plan gives that model, even if that table doesn't exist yet; write such a transform as SQL (the
     reference is text), since an MBQL reference to a table that doesn't exist at import time is [unverified];
   - give each a fresh target name, the agreed folder, a tag whose job is **active**, and an owner who can run it;
   - run it once, in wave order (a later wave's transform reads tables earlier runs create), then compare it with
     the model;
   - then do the same metadata and publish steps as above. Pin it with a transform test where the engine supports one.

Per sync setup (`references/git-sync-and-yaml.md` has YAML shapes and the pull requests):

- **Read-only sync**, as few pull requests as the dependencies allow, all listed in the plan:
  1. A **transforms pull request** adds every transform of every wave, with tags and tests. Title it by what it carries
     ("Add transforms for Charges, Scored Issues and 8 more models"). After the merge, watch the import succeed, or
     run it yourself where the instance doesn't auto-import.
  2. Run each transform on the instance (`mb transform run <id> --sync`), in wave order, and verify it.
  3. A **publish pull request** adds the publish metadata (TableUserSettings / FieldUserSettings YAML) for every target
     table, existing and new, plus FK fixes, synced dependents and metric dimensions ("Publish 17 tables in the Library
     and carry the models' column metadata"). It opens once the new tables exist. A migration of wrappers only needs
     this one. If the user wants the wrappers swapped before the transforms are done, it splits in two, and the plan
     says so.
  4. Create jobs for new schedules on the instance.
- **Read-write sync**: `mb transform create/run`, `table update`, `field update`, then publish into the agreed folder:
  `POST /api/ee/data-studio/table/publish-tables {"table_ids":[…],"collection_id":<folder>}` through the helper. Or run
  `mb library publish` and then `mb table update <T> --body '{"collection_id":<folder>}'`; the first step briefly
  exposes the table to everyone who can read Library > Data. Export to the feature branch and open the pull request.
  Revert serializer churn the change didn't cause.
- **No remote sync**: the same commands, with no pull request.

**Watch the transform output column names.** The swap matches columns by exact, case-sensitive name. Redshift
lower-cases, BigQuery escapes, and long aliases are truncated. After the first run, compare the output fields with the
model's column keys. Read `references/transforms-and-scheduling.md` before authoring any transform.

## Simple models: convert in place and verify

A simple model keeps its card. Everything that points at it keeps working, so there is no swap. It becomes a question
and gets the verified badge ("Verify this question"). Its source table is published in the Library like any other
target, so people can also explore the table directly. For each one, in wave order:

1. **Gate.**
   - Its actions in any state, and their dashboard buttons, are re-homed (`references/edge-cases.md` § 5). The type
     change deletes implicit actions and their buttons and archives query actions.
   - The model column overrides that questions built on it would lose are handled as the plan says. The inventory
     flags these: "questions built on it lose N model column overrides". For MBQL columns, promote the overrides onto the
     table's field metadata (in the publish pull request when the Library is synced). For SQL columns, list them in the
     docs: the converted question keeps them for itself, but its dependents no longer see them.
   - A card-based model is converted only after its upstream model's swap has re-pointed it onto that model's table.
     Check that its query now reads the table.
   - Its model index (record search) and a list display are model-only. They're dropped, and the docs say so.
2. **Snapshot** it: `mb card get <id> --full`, its dashcards and links, and a "before" export of it and a few dependents.
3. **Convert.** Run `mb card update <id> --body '{"type":"question"}'`. For a synced card on a read-only instance, set
   `type: question` in its YAML, in a pull request instead. Set `display` to `table` if it was `list`.
4. **Fix links.** Rewrite `/model/<id>` URLs in link cards, click behaviors, text cards, descriptions and documents to
   `/question/<id>`. A `/model/` URL shows "not found" on a question.
5. **Verify it, last.** Run `mb card verify <id> --text "Replaces the <name> model; reads <schema.table>, live"`. Any
   later edit to its query withdraws the badge, so verify after every change. If the plan moves it to an official
   collection, move it before verifying.
6. **Check.** Compare the "after" exports with the snapshot, run `mb dependency broken card <id>`, and mark it
   `verified-question` in `state.json`. It is not archived.

## Cut over, one model at a time, in wave order

For each model that gets a table (simple models were handled above; details in `references/replacement-api.md` and
`references/edge-cases.md`):

1. **Gate.** All of these must hold:
   - the target exists, is published, and has its permissions and sandboxes set;
   - no other replacement run is active;
   - **read-only sync:** no remote-synced entity is in the model's closure (any `remote_sync_object` status but `removed`).
     Synced dependents go in a pull request first. **Read-write sync:** synced dependents may be swapped; review
     `mb git-sync dirty` afterwards;
   - the closure fits the 30-minute run limit;
   - text references with no dependency edge are listed for manual fixing;
   - the run is in the plan: the model, its target and its dependents match what the plan listed, or differ only in
     ways the plan's rules absorb (new dependents of a known kind). Anything else is a stop rule.
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

**Loop.** When every model in wave *k* is `swapped`, re-run the inventory for wave *k+1* (`--ids`, into
`inventory-wave-<k+1>`). The swaps rewrote those models onto tables, so the script now classifies them mechanically:
it must agree with the plan (same table, same shape, columns present). If it does, go on with wave *k+1*'s swaps. If
a model's class, target or dependents differ from the plan beyond what its rules absorb, that is a stop rule. No new
approval is asked for a wave that matches the plan.

## Write the migration docs

Fill in `references/migration-docs-template.md`:

- a summary;
- a per-model record: decision, table, PR links, run ids, entities rewritten, leftovers fixed, what was lost;
- user-visible changes;
- jobs created;
- rollback;
- notification lists: bookmark holders, alert recipients, owners of affected dashboards, heavy viewers.

With remote sync, the docs go in a docs-only pull request under a folder outside the serialized top-level directories
(e.g. `docs/model-migration/`), opened after the cut-over and updated after the archive and after the purge. Without
remote sync, put them where the user chose. Keep personal data such as emails out of git unless the user explicitly
wants it there.

## Archive, then purge

Models that became verified questions are not archived: the card stays.

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
2. **Synced models.** Archiving a synced model removes its file at the next export (read-write sync), and a pull
   request that deletes the file (read-only sync) hard-deletes it on every instance that imports the branch. There is
   no Trash on that path. So keep synced models in place, unarchived, until the purge date, then handle them in step 5.
3. **Archive** unsynced models with `mb card archive <id>`, as the plan says (each model once its gate passes, or all
   together at the end). Archiving deletes the card's alerts (and emails recipients), resets filters that took values
   from it, hides its dashcards and bookmarks, and archives its actions. Their buttons keep working until the purge,
   which is why the gate comes first.
4. Record the archive time per model, update the docs, and tell the user the purge date.
5. **Purge** after the grace period, and only when the user re-invokes and confirms.
   - Re-verify the app DB (if used), then re-run the gate for each model.
   - Skip anything restored, newly referenced, made public, or now remote-synced. **Never** delete a card that a
     sandbox uses, or one whose actions still back buttons.
   - Right before each delete, snapshot it to `snapshots/purge/<id>/`: `mb card get --full`, actions in any state,
     dashcards including buttons and series, sandboxes, filter sources, subscriptions, bookmarks, and its sync status.
   - Then run `DELETE /api/card/:id` through the helper (for synced models on a read-only sync instance, the file-deleting
     pull request), and record it in the docs.

Already-archived models from `--include-archived`:

- `purge-candidate`: purge it under the same rules.
- `swap-archived-feeder`: goes through Phases 5–6 first. Swapping from an archived source works.
- `review`: decide case by case.

## Resuming and scale

Expect hundreds of models. Keep the pull requests few: one for the transforms, one for the publish metadata, one for
the docs. Split one by Library or transforms folder only when a house rule or the review load demands it, never per
wave or per model, and title each by what it carries. Keep `state.json` current per model: class, action, wave,
target table, pull request, run ids, status, archive time and purge time. When re-invoked, read it first, and
recompute only what may have changed: new models, new dependents, merged pull requests.

## Don't

- Don't infer that something is synced from a collection name. Use `synced_collections` from `mb git-sync status`, or `remote_sync_object` on the app DB.
- Don't run `git-sync import --force` or `--branch`, switch the tracked branch, or push or export to the tracked
  branch, unless the plan says so. `--branch` switches the instance's tracked branch; it is for rehearsal instances.
- Don't ask the user to run anything, and don't ask for a second approval of what the plan already covers.
- Don't trust `mb search` past 1,000 results, and remember it hides the usage-analytics namespace. The inventory script handles both.
- Don't treat `mb card query` JSON as a correctness check. It caps rows and may serve cached results; use `--export-format csv`.
- Don't paste compiled SQL (`mb query --compile`) into a transform you want to test. It is table-qualified, which transform tests refuse.
- Don't revert a transforms or publish PR after cut-over. Swapped content depends on it. Fix forward instead.
