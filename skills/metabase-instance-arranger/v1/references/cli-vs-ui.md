# Choosing the route: `mb` first, then docs plus browser

## Order of preference

1. **`mb` command.** Use it whenever the CLI can make the change. It is repeatable, returns ids, and doesn't break when the UI changes. To find out: `mb --help`, then `mb <group> --help --json` for the command index, and `mb skills list` / `mb skills get <name>` for workflows such as dashboards, transforms or data apps. Settings go through `mb setting get|set <key>`, and `mb setting list` shows the keys.
2. **Docs, then browser.** Only when no `mb` command reaches the change. This covers most pure UI state: which tab or modal is open, hover and tooltip states, a half-finished query builder, unsaved edits, admin screens with no setting key behind them, picking a visualization in the editor before saving.

Don't call `/api/...` directly with `curl` to avoid the browser. When the CLI can't do something, the next step is the UI as a user would use it, so the screenshot shows a state a real user can reach.

## Reading the docs

- Docs are versioned: `https://www.metabase.com/docs/v0.<major>/<path>`. `<major>` is the `major` that `mb auth status` reported. Enterprise tags start with `v1.` (`v1.65.3.6` has major 65 and docs at `v0.65`). Use `latest` for a development build (`kind: "development"`, tag `vUNKNOWN`), or when the versioned page returns 404, and say so in the hand-back.
- Find the page with a site search (`site:metabase.com/docs/v0.<major> <topic>`), or start from `https://www.metabase.com/docs/v0.<major>/` and follow the table of contents.
- Pull out the click path as numbered steps: menu names, button labels, field labels. These become locators in the step script (`getByRole`, `getByLabel`, `getByText` with the exact label).
- If the docs and the instance disagree (a label renamed, a menu moved), trust the instance. Record the difference in the step's `result` column.
- If neither the docs nor the instance show a way to get to the state, say so and give the closest state you can reach. Never fake it, for example by editing the DOM before the screenshot.

## Ids and URL paths

The screenshot needs a URL path. Build it from the ids `mb` returns:

| object | path |
|---|---|
| question / model / metric | `/question/<id>` (`/model/<id>`, `/metric/<id>`) |
| dashboard | `/dashboard/<id>` (for dark mode, use `--theme dark` in `screenshots.md`; `#theme=night` only works in static and public embeds) |
| collection | `/collection/<id>` (`root` for Our analytics) |
| admin pages | `/admin/<section>`, e.g. `/admin/permissions/data`, `/admin/settings/general` |

Before using a path, check it against the docs for the instance's version.
