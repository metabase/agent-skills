---
name: metabase-data-apps
description: Build and change Metabase data apps, the React apps Metabase serves at `/apps/<slug>` from `data_apps/<slug>/` in the Git repository connected through remote sync. Use when the user asks to create, scaffold, set up, or remove a data app; to show Metabase tables, metrics, or saved questions in one, or work with its generated `metabase.data.ts` schema; to add pages or routing; to add a form or button that writes data through an action; or to migrate an app Metabase marks Outdated, or whose `npm run typecheck` or `npm run build` fails after an SDK upgrade.
metadata:
  version: v1
  internal: true
---

# Metabase data apps

A data app is a React bundle that Metabase serves at `/apps/<slug>`. It lives in `data_apps/<slug>/` of the Git repository connected to Metabase through remote sync, and Metabase pulls it from there. This skill has one guide per task, each in its own folder with the files only that task uses. Paths are relative to `<skill-dir>`, the directory holding this `SKILL.md`.

## Read only the guides the task needs

| The task | Read |
| --- | --- |
| Create, scaffold, or remove an app; the dev preview and its diagnostics feed; syncing an app to Metabase; an app-wide error | `setup/setup.md` |
| Change an existing app's UI without new data or writes: layout, theme, sizing, SDK components, what the sandbox blocks | `setup/setup.md`, from _Source conventions_ on; for how a chart renders, also `semantic-layer/semantic-layer.md`, _Rendering_ under _Rules_ |
| Show Metabase data: tables, metrics, segments, measures, saved questions, filters, charts and how they render, the generated `metabase.data.ts` | `semantic-layer/semantic-layer.md` |
| More than one page: routes, links between pages, the current path | `routing/routing.md` |
| A write: a form, a button that creates, updates, or deletes, running an action | `actions/actions.md` |
| Metabase marks the app _Outdated_, the user asks to migrate it, or `npm run typecheck` or `npm run build` fails after an SDK upgrade | `migrate/migrate.md` |

A task can span guides: a new app that shows a metric needs `setup/setup.md`, then `semantic-layer/semantic-layer.md`. Read each guide when the work reaches it, and a file under its `references/` only at the step that names it. An app that Metabase doesn't mark Outdated, and that builds, needs no migration.

## Rules for every task

The guides build on these rules and don't repeat them.

### The app's files

- All work happens in the connected repository: the app is `data_apps/<slug>/`, and its collection is YAML under `collections/data_apps/`. Never a standalone project, a nested `git clone`, or `git init`.
- Every query the app runs is a `defineQuery(...)` named export in the root-level `queries/` directory, and every action a `defineAction(...)` named export in root-level `actions/`, both beside `package.json` and never under `src/`. Filter-option, KPI, and helper queries are queries too.
- Pass the export itself to `useMetabaseQuery`, `useMetabaseQueryObject`, or `useAction`: never an inline object, a spread copy, an entity ID, a raw id, a schema entry, or a hand-built `{ source: { type: "card", id } }`. `Property 'definedWithDefineQuery' is missing` (or `'definedWithDefineAction'`) means the hook got one of those. Move it into `queries/` or `actions/` and import it. Never cast it, and never wrap it in `defineQuery(...)` at the call site: that compiles, but nothing backs it in production.
- Every definition carries an entity ID that names its file in the app's collection: `savedQuestionEntityId` on a query, `copiedActionEntityId` on an action. Generate new ones with `npx @metabase/representations generate-entity-id` (`--count <n>` for several). Use the scoped name: an unscoped `npx representations` outside the app's installed dependencies fetches an unrelated package. Keep it through renames and refactors. Never invent one, copy one to another definition, keep a source's ID on its copy, or remove one while its file exists.
- Metabase generates these files. Never write or edit them by hand, and never copy them from another app, the repository's other YAML, git history, or your own API calls:

  | File | Written by |
  | --- | --- |
  | `data_app.yaml` and the collection's own file | `POST /api/apps/generate/app` (`setup/setup.md`, Step 4). The hand edits are `allowed_hosts`, and `version` during a migration (`migrate/migrate.md`). |
  | `src/metabase.data.ts` | the schema export (`semantic-layer/semantic-layer.md`, _Generate Schema_) |
  | the app's saved questions and its copies of metrics and actions, in `collections/data_apps/<collection>/` | `npm run write-resources` |
  | the bundle, `dist/index.js` | `npm run build` |

- Keep `vite.config.ts` the template's one-liner; `dataAppConfig()` takes only a `port` override. Change `tsconfig.json` or `src/index.tsx` only when it's genuinely required. The usual change is a new `providerProps` key, and changing the factory's shape breaks drill popups and routing. Never render `<MetabaseProvider>` in the app: the dev preview and the Metabase host each wrap the app in their own, and a second one inside the bundle breaks drill popups, plugin init, and similar.

### Credentials

- The Metabase URL and API key are `DATA_APP_MB_URL` and `DATA_APP_MB_API_KEY` in `.env.local` at the repository root, not in the app directory. The key must be in the Administrators group. The schema export, `npm run write-resources`, and the app API answer only an admin, so another key gets `403` or a partial answer: stop and ask for an admin's key.
- Never ask the user to paste the key into the chat, and never `cat`, `echo`, or otherwise print `.env.local` or its variables, since the file may hold other secrets. `source` it in a subshell so the shell uses the values and you see only a pass/fail signal. A value still at the `mb_replace_me` placeholder counts as missing: ask the user to fill it in themselves.

### The sandbox

- The bundle runs inside a Near Membrane sandbox, the same in `npm run dev` as in Metabase. Raw `fetch` reaches only the external origins in `allowed_hosts`, never Metabase, and XHR and `WebSocket` are always blocked. The sandbox also blocks storage, `alert`/`confirm`/`prompt`, `window.open` and `history`, the clipboard, and global key and clipboard listeners. Read and write Metabase only through the data-app hooks, and use the replacements in `setup/setup.md`, _Blocked APIs_.
- Runtime failures, such as sandbox blocks, CSP refusals, failed queries, and uncaught errors, reach neither the terminal nor `tsc`. After any change you can't verify by reading the code, read them from the dev preview's diagnostics feed (`setup/setup.md`, _Reading the diagnostics feed_).

### What the app shows

- When Metabase can display a chart or table, render it with `StaticQuestion` or `InteractiveQuestion`. Build your own only when Metabase can't display it, or when the user asks for a custom one (`semantic-layer/semantic-layer.md`, _Rendering_ under _Rules_).
- Show only values Metabase returned, or deterministic transforms of them. No mock data, sample arrays, or invented KPIs, trends, labels, or statuses.
- Render a spinner or skeleton until a query's data arrives, and a clear empty state only for a result with no rows. `isLoading` alone can't tell them apart (`semantic-layer/semantic-layer.md`, _Queries_ under _Rules_). Never an empty slot, a stale value, or "No data" while loading.
- An app with tabs or another top-level screen switcher opens on its first, leftmost tab, shown as selected, never on a blank page or a "nothing selected" state. Load the app fresh to check.
- A date-range filter uses `DateRangePopover` from `@metabase/embedding-sdk-react/data-app`, or `DateRangeCalendar` inline. No date-picker dependency, no `<input type="date">`, and no `new Date("YYYY-MM-DD")` for its label (`semantic-layer/semantic-layer.md`, _Filters_ under _Rules_).

### Before handoff

- Run `npm run typecheck` after every round of edits. `npm run dev` only transpiles, so type errors don't show up there. Fix the errors before any final summary, and report the command and its result. Group errors by root cause, with a few representative diagnostics, not the whole output.
- After any change to `queries/` or `actions/`, run `npm run write-resources`, then `npm run check-resources`, then `npm run build`. Don't test or hand off the app until the build succeeds.
- A migration changes files only as its upgrade guides say, and runs these checks only at the target version (`migrate/migrate.md`).
- The app reaches Metabase only through Git. Commit the app directory (source, lockfile, `data_app.yaml`, and the built bundle) together with the app's collection files. Metabase pulls them on its next remote-sync import, so there is no deploy step to offer (`setup/setup.md`, _Sync to Metabase_).
