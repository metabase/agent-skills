# Data apps

A data app is a React app built into one bundle, which Metabase serves at `/apps/<slug>`. The `mb` CLI's data-app skills build it on the instance: start with `mb skills get data-app`. This reference settles what rde decides around them: what the app may read, where its project lives, and how it reaches production. Where it differs from those skills, it wins.

## 1. The instance

`rde status --json`: `url` is the instance, and `mb auth list --json` names the profile whose `url` matches; use it as `$PROFILE`. Data apps need a license that carries them: `rde doctor --json`, row `license`; without one, the user activates it in their own terminal with `rde init --only license` (or `! rde init --only license` in this session), and the token never enters the chat. When `mb --profile $PROFILE data-app list` fails, the instance has no data apps: stop and say so. Only an admin profile creates an app and writes its collection.

## 2. What the app reads

An app's questions read only the Library: tables published to its Data collection, the segments and measures on those tables, and metrics in its Metrics collection. Metabase refuses any other question in an app's collection. Its writes are query actions in its own collection (`mb skills get data-app-actions`).

- **Before the first question**, every table and metric the app needs is in the Library. A missing one goes back to this skill's pipeline (`../SKILL.md`, Route): `../playbooks/build-semantic-layer.md`, with clean tables first when the source is raw. Never create a definition ad hoc to unblock the UI, and never read around the Library.
- **Without the Library** (`mb library get --json` fails), the app has nothing it may read: stop and say so.
- **A number the app shows** comes from a metric or measure, so the app queries the definition and never re-derives it.
- **A table the app writes to** is published as it is, raw, never through a transform: a transformed copy lags the rows the app writes.
- **The agent never runs DDL.** For a new column or table in an operational database, the agent proposes it and the user's database admin adds it in every warehouse. Each Metabase then syncs it (a column: `mb table sync-schema <table-id>`; a table: `mb db sync-schema <db-id>`), confirmed with `mb table fields <table-id> --json`, before the app ships: until a Metabase knows it, the app's queries fail there.

When `./.scratch/STATE.md` exists, record the app's slug and the table ids it reads and writes (`apps`).

## 3. The project

`mb data-app scaffold` writes the app's project. Put it in `./apps/<slug>` under the working directory unless the user names another place, and never in the working tree of the remote-sync repository: Metabase receives only the built bundle, and git sync carries that bundle itself (section 5). The source is the user's to keep under git or not.

The dev preview needs an admin API key in the project's `.env.local`. The `data-app` skill writes one with `mb api-key create`; follow it, never print the key, and delete it at handoff. It is an admin key, so the preview sees every table: say so when the app is meant for a narrower audience.

## 4. The build

Follow the CLI's skills, each read when the work reaches it:

| The step | Skill |
| --- | --- |
| Create the app, scaffold, preview, build, publish, turn on or off | `data-app` |
| Questions, `src/metabase.ts`, the read hooks, charts | `data-app-data` |
| Filter controls and date ranges | `data-app-filters` |
| A write: a form, an update, a delete | `data-app-actions` |
| Layout, theme, pages, what the sandbox blocks | `data-app-ui` |

A data action runs only where its database's **Data actions** toggle is on (Admin > Databases > <database>), set per instance and never synced: turn it on in the development Metabase (`mb db set-data-actions <db-id> true`, in an `mb` whose `mb db --help` lists it; otherwise ask the user to flip the toggle), and tell the user to turn it on in production. When the development Metabase uses production's database, with no staging copy, every action run there writes real rows: say so before running one, and recommend a staging copy.

## 5. Reaching production

STATE.md `environment` decides.

- **Production**, one instance: `mb data-app set-bundle` makes the new bundle live at once. Turning the app on (`mb data-app set-enabled <slug> true`) shows it to its viewers, so ask first. Assigning groups is the user's (Admin → Settings → Data apps → the app → Groups).
- **Staging**: build and check the app on the development instance, then move it with remote sync; never rebuild it on production. Remote sync carries the app with its bundle (`data_apps/<slug>/`) and its collection with the questions and actions in it. It needs STATE.md `remote_sync` and the Library synced (`../SKILL.md`, "Remote sync").
  - The app and the Library content it reads go on the same job branch (`remote-sync.md`, "Staging"), so the reviewer merges them together. Production's import does not check that a question's tables are published there, so a branch without that content ships an app whose queries read around production's Library.
  - Every export is a sync step, asked first (`remote-sync.md`, "Ask before every sync step"); "not now" leaves the app on the development instance only, labelled as such.
  - After the merge, production imports the branch. Turning the app on there and assigning its groups is the user's.

The hand-back names the app's URL, what was synced, to which branch, and at which commit.
