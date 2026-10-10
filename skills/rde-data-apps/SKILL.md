---
name: rde-data-apps
description: >
  Build or change a Metabase data app on an rde machine: settles what the `metabase-data-apps` skill needs from the local setup (the remote-sync repository, the Metabase URL, the API key rde stores, how the app reaches Metabase), makes sure everything the app reads is Library content already synced into that repository, confirms every sync step with the user, and hands the build to it. Use only when an app is asked for explicitly: "build me an app for X", "create a data app", "make an internal tool / portal in Metabase", "add a page / a form / a filter to my data app". A dashboard, a question, or a metric is not an app; those stay with the `rde` skill.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# rde-data-apps

A data app is a React bundle Metabase serves at `/apps/<slug>` from `data_apps/<slug>/` in the repository connected through remote sync. The `metabase-data-apps` skill builds it. This skill answers its questions from what rde already knows, so the user is asked only what rde cannot know, makes sure the content the app reads is in that repository before the app is built, then hands over. Sections 4 to 6 override the data-apps skill wherever they differ: the schema scope, the order of commits and pushes, and the confirmation before any sync.

## 1. The instance

`rde status --json`: `url` is the instance. It serves data apps only when `curl -s -o /dev/null -w '%{http_code}\n' -H "x-api-key: $(rde credentials --api-key)" <url>/api/apps` prints `200`; never judge by `version` (a head build reports `vUNKNOWN`). `mb auth list --json` names the profile whose `url` matches; use it as `$PROFILE`. Metabase serves apps only under a license with remote sync and data apps: `rde doctor --json`, row `license`. Without one, the user activates it in their own terminal with `rde init --only license` (or `! rde init --only license` in this session); the token never enters the chat. Syncing content needs `remote-sync-type` set to `read-write` (`mb setting get remote-sync-type --json`); switching it is a sync change, confirmed like one (section 6).

## 2. The repository

`contentRepository` in `rde status --json` is the working directory of the remote-sync repository, and the answer to Step 1 of the `metabase-data-apps` setup guide: name it and use it, do not ask. When it is null and the license has remote sync, ask where the repository should live, then run `rde init --only git-sync --git-dir <path> --git-remote local` (a bare remote inside `~/.rde`, no account). A hosted remote needs a git token, so the user runs `rde init --only git-sync` themselves. A repository rde creates ignores `.env.local`, `node_modules/`, `.scratch/`, and the rest a data app must not push; in a hosted repository rde cloned, add whichever of `.env.local`, `node_modules/`, `.scratch/` its `.gitignore` lacks, committed with the app, before the first `git add`.

## 3. The credentials

The data-apps skill reads `DATA_APP_MB_URL` and `DATA_APP_MB_API_KEY` from `.env.local` at the repository root and forbids the key in the conversation. rde stores the API key `mb` uses, and `rde credentials --api-key` prints it alone. When its setup guide reaches the credentials step, or its check prints `MISSING`, fill the file with this command instead of asking the user, `<url>` from step 1 and `<repo>` from step 2. It prints only `creds written`, keeps the file's other lines, and makes sure `.env.local` is ignored:

```bash
ROOT="$(git -C "<repo>" rev-parse --show-toplevel)" && KEY="$(rde credentials --api-key)" &&
{ grep -qxF .env.local "$ROOT/.gitignore" 2>/dev/null || echo .env.local >> "$ROOT/.gitignore"; } &&
{ if [ -f "$ROOT/.env.local" ]; then grep -v -e '^DATA_APP_MB_URL=' -e '^DATA_APP_MB_API_KEY=' "$ROOT/.env.local"; fi
  printf 'DATA_APP_MB_URL=%s\nDATA_APP_MB_API_KEY=%s\n' "<url>" "$KEY"; } > "$ROOT/.env.local.tmp" &&
mv "$ROOT/.env.local.tmp" "$ROOT/.env.local" && chmod 600 "$ROOT/.env.local" && echo "creds written"
```

Never run `rde credentials --api-key` where its output comes back to you, and never print `.env.local`. The key belongs to rde's admin, so the dev preview sees every table; say so when the app is meant for a narrower audience.

## 4. The repository is the source of truth

A data app exists only through remote sync, so here it is a requirement, not a suggestion: section 2 sets it up when it is missing, and that is the only place rde proposes remote sync unprompted, because the user asked for an app. Record it in STATE.md as `remote_sync`. Outside an app, the `rde` skill raises syncing only when remote sync is already configured.


The bundle refers to Metabase objects by id and through the typed schema. An app built on content that lives only in the instance works there and nowhere else: importing the repository into another instance brings the app without the definitions it reads, and its queries fail. So everything the app reads is in the repository before the app is built, and everything the build creates goes there with the app.

- **What the app may read.** Library-published tables with their field metadata, measures, and segments; metrics filed in the Library's Metrics collection; query actions without a model (Data Studio → Data actions). Nothing else.
- **What "in the repository" means.** The Library collections carry `is_remote_synced: true` (`synced_collections` in `mb git-sync status --json`), the content has been exported, and `git pull` has brought it into the working tree: the files are there under `databases/…/tables/<table>/` and `collections/…`, checked, not assumed.
- **Measures and segments need a published table** (the `rde` skill's `references/remote-sync.md`, "What belongs in git"). Without the Library (`mb library get --json` fails), stop: the app has nothing it may read; say so.
- **The app's own files.** `npm run write-resources` writes the app's questions and copies of its actions as files under `collections/data_apps/` in the working tree; nothing changes in Metabase until the repository is imported. They are committed with the app (`data_apps/<slug>/`), in the same commit. They are copies: when a metric, measure, or action the app uses changes, run `npm run write-resources` again so the app's copy follows, and ship it with the change.
- **Schema scope.** The schema always covers the Library's published tables and metrics and every query action without a model (`metabase-data-apps`, "Generate Schema"); nothing else reaches the app, so a table it needs is published first.
- **A missing entity found mid-build** (a measure, a segment, a metric, a published table) goes back to the `rde` skill; a missing action follows `actions/actions.md`, "What's in the schema". Then sync it (sections 5 and 6), `git pull`, regenerate the schema, and continue. Never create it ad hoc to unblock the UI.
- **Before the first line of app code**, every entity the app needs is in the generated schema and its file is in the working tree. When one is missing, stop and go back to `rde`.

## 5. Syncing safely

Remote sync merges nothing and resolves no conflicts. The instance side (what to check before every import or export, which goes first, never `--force` without the user's yes) and the staging hand-back: the `rde` skill's `references/remote-sync.md`, "Before each step" and "Staging". Here a `git push` behind a Metabase export is rejected too, and two writers push to the same remote, Metabase's export and the app's commits, so keep them in step:

- **Working-tree side.** The app's commits touch only `data_apps/<slug>/` and the files `npm run write-resources` writes under `collections/data_apps/`; exported Metabase YAML is never edited by hand. Before pulling a Metabase export: `git stash --include-untracked`, `git pull --ff-only`, `git stash pop`. Before every `git push`: `git pull --ff-only` again. A pull that cannot fast-forward is a stop: report both histories, do not merge or force.
- **Delivery order**, each step starting from a clean state: export the instance's dirty set to the job branch (**Branch**, below) → `git fetch` and switch the working tree to that branch (stash, pull, pop) → `npm run write-resources`, `npm run check-resources`, `npm run build` → commit `data_apps/<slug>/` with its `collections/data_apps/` files → pull, push → hand back the branch for review. After the merge, production imports it; the development instance follows with `mb git-sync import --branch <main>` (`references/remote-sync.md`, "Staging").
- **Branch.** One job branch per change, created and exported per `references/remote-sync.md`, "Staging" (the `rde` skill); push the app to the same branch, so content and app travel together. Export or push to `main` or `master` only with an explicit yes.

## 6. Ask before anything touches sync

Every sync step, every `git push` to the synced remote included, is approved first, one checkpoint per sync point: the `rde` skill's `references/remote-sync.md`, "Ask before every sync step". "Yes for the rest of this job" is recorded and not asked again; anything less is asked again at the next sync point.

"Not now" before the build leaves one path: a dev preview only, labelled as working on this instance alone and breaking wherever the repository is imported. Nothing is pushed to the synced branch until the content it reads is synced.

## 7. Hand off

The `metabase-data-apps` skill has one guide per step; follow it for the app's code, with sections 4 to 6 taking precedence:

| The step | Guide in `metabase-data-apps` |
| --- | --- |
| No app yet: create, scaffold, set up | `setup/setup.md` |
| The app reads Metabase tables, metrics, measures, or segments (the generated `metabase.data.ts`) | `semantic-layer/semantic-layer.md` |
| More than one page | `routing/routing.md` |
| A write: a form, an update, a delete, a saved action | `actions/actions.md` |

## 8. The data behind it

The app reads what the semantic layer publishes to the Library. A number it shows with no metric or measure behind it yet goes back to the `rde` skill first (its semantic-layer playbook, clean tables before that when the source is raw), then through sections 4 to 6 into the repository, so the app queries the definition by id and never re-derives it in `queries/`. The agent never runs DDL. A new column or table in an operational database: the agent proposes it, the user's database admin adds it in every warehouse (staging and production), then it is synced into each Metabase (a column: `mb table sync-schema <table-id>`; a table: `mb db sync-schema <db-id>`; production: Admin → Databases → <database> → Sync database schema) and confirmed with `mb table fields <table-id> --json`, all before the app's PR merges: until a Metabase knows it, the app's queries fail there. A table the app writes to is published as it is, never through a transform (a transformed copy lags the app's writes). When the `rde` skill keeps `./.scratch/STATE.md`, record there the app's slug and the table ids it reads and writes (`apps`), and each sync decision.

## 9. Delivery

The setup guide ends with a commit and a push; make them in section 5's order, after section 6's question. To try the app in the development Metabase before the merge, `mb --profile $PROFILE git-sync import --branch agent/<slug>-<change> --json` brings it in, and it opens at `<url>/apps/<slug>`. A data action runs only where its database's **Data actions** toggle is on (Admin → Databases → <database>), set per instance and never synced: turn it on in the development Metabase (`mb db set-data-actions <db-id> true`) and tell the user to turn it on in production. If the development Metabase uses production's database (no staging copy), every action run there writes real rows: say so before running one, and recommend a staging copy. The hand-back names what was synced, to which branch, and at which commit.
