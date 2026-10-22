# Data apps

A data app is a React app built into one bundle, which Metabase serves at `/apps/<slug>`. The `mb` CLI's data-app skills build it on the instance: start with `mb skills get data-app`. This reference settles what rde decides around them: what the app may read, where its project lives, and how it reaches production. Where this reference and those skills differ, this reference wins.

## 1. The instance

`rde status --json`: `url` is the instance, and `mb auth list --json` names the profile whose `url` matches; use it as `$PROFILE`. Only an admin creates an app and writes its collection: when `$PROFILE` is not an admin, ask the user for one. Data apps need a license that carries them: `rde doctor --json`, row `license`; without one, the user activates it in their own terminal with `rde init --only license` (or `! rde init --only license` in this session), and the token never enters the chat. When `mb --profile $PROFILE data-app list` errors, this Metabase doesn't support data apps: stop and say so.

## 2. What the app reads

An app's questions read only the Library: tables published to its Data collection, the segments and measures on those tables, and metrics in its Metrics collection. Metabase refuses any other question in an app's collection, and refuses a question based on another question, even one in the app's collection: every question starts from a published table. Its writes are query actions in its own collection (`mb skills get data-app-actions`).

- **Without the Library** (`mb library get --json` fails), the app has nothing it may read: stop and say so.
- **Before the first question**, every table the app reads is in the Library: its source tables, its joins, the tables it reaches through a foreign key, the tables behind its segments and measures, and the tables of the columns Metabase shows in place of a foreign key. Every metric it aggregates is in the Library too. A missing one goes back through rde's pipeline (`../SKILL.md`, Route): `../playbooks/build-semantic-layer.md`, with clean tables first when the source is raw. Never create a definition ad hoc to unblock the UI.
- **A number the app shows** comes from a metric or measure, so the app queries the definition and never re-derives it.
- **Exception: a table the app writes to** is published as it is, raw, never through a transform, since a transformed copy lags the rows the app writes.
- **The agent never runs DDL.** For a new column or table in an operational database, the agent proposes it and the user's database admin adds it. The development and production Metabase each sync it (a column: `mb table sync-schema <table-id>`; a table: `mb db sync-schema <db-id>`), confirmed with `mb table fields <table-id> --json`, before the app ships: until a Metabase knows it, the app's queries fail there.

## 3. The project

Scaffold the app's project into `data_apps/<slug>/` of the remote-sync repository's working tree (`contentRepository` in `rde status --json`), the folder where an export writes the app's `data_app.yaml` and bundle. The app runs only from the bundle, but the folder keeps its source with it: an export leaves the source alone and an import ignores it. The template's `.gitignore` keeps `node_modules/`, `dist/`, and `.env.local` out of git. Without a remote-sync repository, use `./apps/<slug>` under the working directory.

The dev preview needs an admin API key in the project's `.env.local`. The `data-app` skill writes one with `mb api-key create`: note its id, never print the key, and delete it at handoff with `mb api-key delete <id> --yes`. It is an admin key, so the preview sees every table: say so when the app is meant for a narrower audience.

When `./.scratch/STATE.md` exists, record the app's slug and the table ids it reads and writes (`apps`).

## 4. The build

Follow the CLI's skills, each read when the work reaches it:

| The step | Skill |
| --- | --- |
| Create the app, scaffold, preview, build, upload the bundle (`set-bundle`), turn it on or off | `data-app` |
| Questions, `src/metabase.ts`, the read hooks, charts | `data-app-data` |
| Filter controls and date ranges | `data-app-filters` |
| A write: a form, an update, a delete | `data-app-actions` |
| Layout, theme, pages, what the sandbox blocks | `data-app-ui` |

A data action runs only where its database's **Data actions** toggle is on (Admin > Databases > <database>), set per instance and never synced. Turning it on lets anyone with access to the database's actions write to it, so ask first, then run `mb db set-data-actions <db-id> true` on the instance you build on; in staging, tell the user to turn it on in production too. When the instance you build on uses production's database, with no staging copy, every action run there writes real rows: say so before running one, and recommend a staging copy.

## 5. Reaching production

STATE.md `environment` decides.

- **Production**, one instance: `mb data-app set-bundle` makes the new bundle live at once. Turning the app on (`mb data-app set-enabled <slug> true`) shows it to its viewers, so ask first. Assigning groups is the user's (Admin → Settings → Data apps → the app → Groups). When `remote_sync` is set, the app's collection and bundle reach git with the next export, a sync step like any other; commit its source after that export, as in staging.
- **Staging**: build and check the app on the development instance, then move it with remote sync; never rebuild it on production. Remote sync carries the app with its bundle (`data_apps/<slug>/`) and its collection with the questions and actions in it.
  - With STATE.md `remote_sync: none`, the app can't reach production. Ask whether to set remote sync up (`rde init --only git-sync`, a sync step) or leave the app on the development instance; this is the one case where rde raises remote sync unprompted, because the user asked for an app. An export needs `remote-sync-type` read-write.
  - The app and the Library content it reads go on the same job branch (`remote-sync.md`, "Staging"), so the reviewer merges them together. Production's import does not check that a question's tables are published there, so without that content the app reads around production's Library.
  - Once the app is done, commit its source on that branch, after the export: `git pull --ff-only` (stash first when the tree is dirty), then commit only `data_apps/<slug>/` and push. Never edit or commit the files the export wrote. A pull that can't fast-forward is a stop: report both histories, never merge or force.
  - Every export is a sync step, asked first (`remote-sync.md`, "Ask before every sync step"). "Not now" leaves the app on the development instance only: say so in the hand-back.
  - After the merge, production imports the branch. Turning the app on there and assigning its groups is the user's.

The hand-back names the app's URL and, when something was synced, what, to which branch, and at which commit.
