# Data apps

A data app is a React app built into one bundle, which Metabase serves at `/apps/<slug>`. The `mb` CLI's data-app skills build it in the synced repository, and an import loads it into Metabase: start with `mb skills get data-app`. This reference settles what rde decides around them: what the app may read, where its project lives, and how it reaches production. Where this reference and those skills differ, this reference wins.

## 1. The instance

`rde status --json`: `url` is the instance, and `mb auth list --json` names the profile whose `url` matches; use it as `$PROFILE`. The data-app commands need an admin: when `$PROFILE` is not an admin, ask the user for one. Data apps need a license that carries them: `rde doctor --json`, row `license`; without one, the user activates it in their own terminal with `rde init --only license` (or `! rde init --only license` in this session), and the token never enters the chat. When `mb --profile $PROFILE data-app list` errors, this Metabase doesn't support data apps: stop and say so. An app reaches Metabase only through git, so it needs STATE.md `remote_sync: <branch>, read-write` and `contentRepository` in `rde status --json`, a clone of that repository: without either, stop and say so before scaffolding anything. Setting remote sync up (`rde init --only git-sync`) is the user's call; this is the one case where rde raises it unprompted, because the user asked for an app.

## 2. What the app reads

An app's questions read only the Library: tables published to its Data collection, the segments and measures on those tables, and metrics in its Metrics collection. Metabase refuses any other question in an app's collection, and refuses a question based on another question, even one in the app's collection: every question starts from a published table, in one stage, with no explicit joins and no custom expressions. Its writes are table actions on its published tables, in its own collection, never SQL actions (`mb skills get data-app-actions`).

- **Without the Library** (`mb library get --json` fails), the app has nothing it may read: stop and say so.
- **Before the first question**, every table the app reads is in the Library: its source tables, the tables it reaches through a foreign key, the tables behind its segments and measures, and the tables of the columns Metabase shows in place of a foreign key. Every metric it aggregates is in the Library too, and built on a published table: a metric on a model can't be used in a question that starts from a table. A missing one goes back through rde's pipeline (`../SKILL.md`, Route): `../playbooks/build-semantic-layer.md`, with clean tables first when the source is raw. Never create a definition ad hoc to unblock the UI.
- **A number the app shows** comes from a metric or measure, so the app queries the definition and never re-derives it. The app never re-aggregates a metric at runtime, since a sum over its rows is wrong for distinct counts, averages, ratios and levels such as MRR: a runtime filter only picks rows of a question on it. A filter on a column needs a question broken out by that column too; a date filter offers whole, complete periods of the question's buckets and no custom range, and a KPI shows one period (`data-app-data`, _Runtime clauses_). A complete period is one up to STATE.md `last_complete_period`, not the calendar: the app's metric questions carry the `Complete periods` segment, and presets and KPIs anchor on the newest row they return (`orderBys` descending, `limit: 1`), never on today's date; take the first 10 characters of its date value for the arithmetic, never `new Date(<value>)`. Without that segment or `last_complete_period` (a Library rde didn't build), settle Freshness (`../SKILL.md`), add `is_complete_period` through `../playbooks/build-clean-tables.md`, then the segment (`../playbooks/build-semantic-layer.md`); when the table isn't a transform rde can change, say the app can't mark complete periods. When a request needs more, say so rather than rebuild the number from rows.
- **Exception: a table the app writes to** is published as it is, raw, never through a transform, since a transformed copy lags the rows the app writes.
- **The agent never runs DDL.** For a new column or table in an operational database, the agent proposes it and the user's database admin adds it. The development and production Metabase each sync it (a column: `mb table sync-schema <table-id>`; a table: `mb db sync-schema <db-id>`), confirmed with `mb table fields <table-id> --json`, before the app ships: until a Metabase knows it, the app's queries fail there.

## 3. The project

From the root of `contentRepository`, `mb data-app scaffold <slug>` writes the project and its `data_app.yaml` into `data_apps/<slug>/` and the app's collection file into `collections/data_apps/`. The folder keeps the source with the bundle: an import ignores the source. An app already in the repository is never scaffolded again. `npm run build` writes `dist/index.js`, the bundle an import loads, so it is committed with the source; the template's `.gitignore` keeps `node_modules/` out, and the repository's `.gitignore` keeps `.env.local` out.

The dev preview needs an admin API key in the project's `.env.local`. The `data-app` skill asks the user before writing one with `mb api-key create --profile $PROFILE`; never print the key, and delete it at handoff: find its id with `mb api-key list --profile $PROFILE`, then `mb api-key delete <id> --yes --profile $PROFILE`. It is an admin key, so the preview sees every table: say so when the app is meant for a narrower audience.

When `./.scratch/STATE.md` exists, record the app's slug and the table ids it reads and writes (`apps`).

## 4. The build

Follow the CLI's skills, each read when the work reaches it:

| The step | Skill |
| --- | --- |
| Scaffold, preview, generate the collection, build, push, import, turn it off | `data-app` |
| `src/metabase.schema.ts`, questions in `src/metabase.queries.ts`, the read hooks, charts | `data-app-data` |
| Filter controls and date ranges | `data-app-filters` |
| A write in `src/metabase.actions.ts`: a form, an update, a delete | `data-app-actions` |
| Layout, theme, pages, what the sandbox blocks | `data-app-ui` |

A data action runs only where its database's **Data actions** toggle is on (Admin > Databases > <database>), set per instance and never synced. Turning it on lets anyone with access to the database's actions write to it, so ask first, then run `mb db set-data-actions <db-id> true` on the instance you build on; in staging, tell the user to turn it on in production too. When the instance you build on uses production's database, with no staging copy, every action run there writes real rows: say so before running one, and recommend a staging copy.

## 5. Reaching production

STATE.md `environment` decides.

Either way, the app ships as in the `data-app` skill, _Release_: export pending Library changes, pull, generate its questions and actions (`mb data-app generate-queries` and `generate-actions`), build, test in the preview, commit the source, `dist/index.js` and `collections/data_apps/` together, push, import. Every export, push and import is a sync step, asked first (`remote-sync.md`, "Ask before every sync step"); "not now" leaves the app unpublished: say so in the hand-back. In `data_app.yaml` change only `name`, `description` and `allowed_hosts`; never edit the generated collection files. A pull that can't fast-forward is a stop: report both histories, never merge or force.

- **Production**, one instance: the import makes the new bundle live at once. A new app is on from the start, open to admins; it reaches viewers once the user assigns their groups (Data Studio → Data apps → the app → Permissions). Turning it off (`mb data-app set-enabled <slug> false`) is the user's call; an app turned off opens only in Data Studio → Data apps → the app → Overview.
- **Staging**: build and check the app on the development instance, then move it with remote sync; never rebuild it on production. Remote sync carries the app with its bundle (`data_apps/<slug>/`) and its collection with the questions and actions in it.
  - The app and the Library content it reads go on the same job branch (`remote-sync.md`, "Staging"), so the reviewer merges them together. Production's import does not check that a question's tables are published there, so without that content the app reads around production's Library.
  - After the merge, production imports the branch. The first import creates the app on, open to admins until the user assigns groups; later imports keep its on/off state.

The hand-back names the app's URL and, when something was synced, what, to which branch, and at which commit.
