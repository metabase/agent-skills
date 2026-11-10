# Playwright: setup, UI steps, screenshots

All browser work happens in `./.scratch/arranger/`, using the scripts copied from `<skill-dir>/scripts/`.

## Setup (once per job)

```bash
mkdir -p ./.scratch/arranger/steps
cp <skill-dir>/scripts/*.mjs ./.scratch/arranger/
cd ./.scratch/arranger
[ -f package.json ] || npm init -y >/dev/null
npm ls playwright >/dev/null 2>&1 || npm i playwright
npx playwright install chromium
```

The scripts import `playwright`, and Node looks for it next to the script. That is why the scripts are copied into `./.scratch/arranger/` instead of being run from `<skill-dir>`.

Every script reads `MB_URL` (the profile's `url` from `mb auth list --json`). Pass it inline on each command.

### Signing in

The Metabase UI authenticates with a session cookie. The `mb` OAuth token and API keys don't work in the browser. The person signs in once, by hand:

```bash
MB_URL=… node session.mjs --login
```

This opens a visible Chromium window on the person's screen and waits up to 5 minutes. Before running it, tell the user: "A browser window will open. Sign in to Metabase there (password or SSO); it closes by itself." Once `/api/user/current` succeeds, the script saves the cookie to `./.scratch/arranger/auth-<host>.json` (one file per instance), and every later run reuses it headless. Never ask for or handle the password.

Any script exits with `NeedsLoginError` when there's no saved session or it has expired. When that happens, run `--login` again, give the same notice, then re-run the failed command.

The cookie is a credential. If the current directory is a git repository and `git check-ignore -q .scratch` fails, add `.scratch/` to its `.gitignore` before the first sign-in, and mention it in the hand-back.

## UI steps

For each change made in the UI, write one script, `./.scratch/arranger/steps/NN-<slug>.mjs`:

```js
import { withPage } from "../session.mjs";

await withPage(async (page) => {
  await page.goto("/admin/permissions/data");
  await page.getByRole("button", { name: "Save changes" }).click();
  // one change per script; wait for the result you can see before returning
  await page.getByText("Saved").waitFor();
});
```

Run it with `MB_URL=… node steps/NN-<slug>.mjs`.

- Prefer locators by role or label, using the exact labels from the docs. Use CSS selectors only when nothing else works.
- Finish each step by waiting for something visible (a toast, a URL change, an element appearing). Never use a fixed sleep.
- If a step fails, save a debug screenshot before retrying: `page.screenshot({ path: "debug-NN.png" })`.
- When a scene depends on UI state that doesn't survive a page load (an open modal, a hover, an unsaved edit), the screenshot has to be taken in that same step script. Do the setup and then call `shoot(page, …)` from `screenshot.mjs` before the script exits.

## Taking the shot

```bash
MB_URL=… node screenshot.mjs \
  --path /dashboard/12 --out shot-03.png \
  [--viewport 1440x900] [--fit] [--full-page] [--theme dark] [--selector '<css>'] [--wait '<css>']
```

- `--path` is joined to `MB_URL`. `--selector` captures one element instead of the whole viewport.
- `--fit` grows the viewport height until the whole page is visible. Use it for a whole dashboard or any long page. Metabase scrolls dashboards inside an inner panel, so `--full-page` only captures the viewport, and a guessed height either cuts off the bottom or leaves blank space (row height grows with dashboard width). `--viewport` still sets the width.
- Dashboards are fixed-width by default, with wide side gutters. `"width": "full"` is ignored by `mb dashboard create`, so set it with `mb dashboard update <id>` afterwards and read it back.
- `--wait` is an extra element that must appear before the shot (for example a chart's `svg`). The script always waits for network idle and for every `[data-testid="loading-indicator"]` to disappear first. That is the id Metabase's shared `Loader`, dashcard loading view and loading wrappers render.
- `--theme dark|light` sets the browser's `prefers-color-scheme`. Metabase follows it only when the browser user's `color-scheme` setting is `auto` (the default). That setting is per user and can be `auto`, `light` or `dark`. The script reads `data-mantine-color-scheme` on `<html>` and warns when the page rendered a different scheme. When it warns, change the setting in the UI for the browser user (a step script), or with `mb setting set color-scheme '"auto"'` if the `mb` profile logs in as that same user. Record the old value under `Changed settings` either way.
- The `#theme=night` URL hash only works in static and public embeds (`/embed/…`, `/public/…`). It does nothing in the normal app.
- Number shots in order and never overwrite one. The hand-back gives the absolute path.

## Troubleshooting

- **`NeedsLoginError`, or redirected to `/auth/login`.** The saved session has expired or belongs to another instance. Run `node session.mjs --login` again (see "Signing in").
- **The sign-in window never appears.** The session has no display, for example over SSH or in a cloud sandbox. Ask the user to run `MB_URL=… node session.mjs --login` from `./.scratch/arranger/` in their own terminal.
- **The shot shows spinners.** Some screens draw their own loader with a different test id. Pass `--wait` with an element that only appears once the content has rendered.
- **Wrong theme.** See `--theme` above: the browser user's `color-scheme` setting isn't `auto`.
- **Chromium is missing.** Run `npx playwright install chromium` from `./.scratch/arranger/`.
