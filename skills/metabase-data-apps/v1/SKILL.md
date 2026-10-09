---
name: metabase-data-apps
description: Build and change Metabase data apps, the React apps Metabase serves at `/apps/<slug>` from `data_apps/<slug>/` in the Git repository connected through remote sync. Use when the user asks to create, scaffold, set up, or remove a data app; to show Metabase tables, metrics, or saved questions in one, or work with its generated `metabase.data.ts` schema; to add pages or routing; to add a form or button that writes data through an action; or to migrate an app Metabase marks Outdated, or whose `npm run typecheck` or `npm run build` fails after an SDK upgrade.
metadata:
  version: v1
  internal: true
---

# Metabase data apps

This skill is split into parts, one per task. Each part is a guide in its own folder, together with the files only that task uses. Paths in this skill are relative to `<skill-dir>`, the directory holding this `SKILL.md`.

## Read only the parts the task needs

Every guide is long, and its rules apply only to its own task. Pick the parts from the user's request, read those guides, and leave the others unread.

| The task | Read |
| --- | --- |
| Create, scaffold, or remove an app; the dev preview and its diagnostics feed; syncing an app to Metabase; an app-wide error | `setup/setup.md` |
| Change an existing app's UI without new data or writes: layout, theme, SDK components, how a chart renders | `setup/setup.md`, from _Source conventions_ on |
| Show Metabase data: tables, metrics, segments, measures, saved questions, filters, charts, the generated `metabase.data.ts` | `semantic-layer/semantic-layer.md` |
| More than one page: routes, links between pages, the current path | `routing/routing.md` |
| A write: a form, a button that creates, updates, or deletes, running an action | `actions/actions.md` |
| Metabase marks the app _Outdated_, the user asks to migrate it, or `npm run typecheck` or `npm run build` fails after an SDK upgrade | `migrate/migrate.md` |

- Don't read `routing/routing.md` unless the app needs more than one page.
- Don't read `actions/actions.md` unless the app writes data.
- Don't read `migrate/migrate.md` unless the app needs migrating as the table says. An app Metabase doesn't mark Outdated, and that builds, needs no migration.
- A task can span parts: a new app that shows a metric needs `setup/setup.md`, then `semantic-layer/semantic-layer.md`. Read each part when the work reaches it, not all of them up front.
- When a guide points to another part or to a file under its own `references/`, read it only when you reach that step.
