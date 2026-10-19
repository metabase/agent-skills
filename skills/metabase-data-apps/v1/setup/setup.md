# Create a Metabase data app

The scaffold ships in this skill at `setup/template/`: a Vite + React + TypeScript project whose whole build and dev setup is the SDK preset behind `dataAppConfig()`. Copy it into the app directory. If you find yourself writing `package.json`, `vite.config.ts`, `tsconfig.json`, or `src/index.tsx` by hand, stop and copy the template instead.

- `npm run dev` previews the app against a real Metabase, through the same sandbox and distortion rules Metabase uses, so third-party libraries the app bundles behave as they will in production. It listens on `http://localhost:5174`, or the next free port when that one is taken, so take the URL from the `Local:` line Vite prints. An edit under `src/` rebuilds the bundle and soft-reloads it: the app remounts and its component state resets, while auth and the SDK stay loaded. There's no browser refresh and no Fast Refresh. Edits under `queries/` and `actions/` don't trigger a rebuild: after one, save a file under `src/` or restart `npm run dev`.
- `npm run build` writes the single bundle, `dist/index.js`. It's committed, and a pull imports it into Metabase.

Apps can also be created and updated through `/api/apps`. This guide covers the Git path. To remove an app, only _Removing an app_ applies.

## Step 1 — Locate the remote-sync repository

If the user already named the repository's path, use it. Otherwise ask: **"Do you already have a Git repository connected to this Metabase via remote sync?"** If yes, ask for its local path. If no, ask the user to create one, a plain Git repository they connect under Admin > Settings > Remote sync, and to share its path. This skill neither creates nor connects it. Check that the path is a Git working tree (it has a `.git`). Every step below runs in it.

## Step 2 — Name the app and create its directory

1. Settle the **slug**, the `/apps/<slug>` URL. It must be dash-cased (`[a-z0-9]+(?:-[a-z0-9]+)*`, such as `sales-overview`), at most 100 characters, and not `generate`, `repo-status`, or `sandbox-host`, or sync rejects it. If the app's purpose isn't clear yet, ask "what's this app for?" in one line, then propose a slug and confirm it.
2. Create `<repo>/data_apps/<slug>/`, and `data_apps/` first if it's missing. If the directory already exists, it holds an existing app: check it as below, and never overwrite a file without confirmation.

### An existing app

The app is template-shaped when both of these hold:

1. `vite.config.ts` is `export default dataAppConfig()`, imported from `@metabase/embedding-sdk-react/data-app-dev/config`, and there is no local `config/` directory.
2. `src/index.tsx` default-exports a `DataAppFactory` (from `@metabase/embedding-sdk-react/data-app`) that takes no arguments and returns `{ component, providerProps? }`.

If both hold, ask: "Extend this app, or scaffold a new one under a different slug?" To extend, skip the copy and edit `src/`. For a new one, pick another slug and restart at Step 2.

If either fails, **stop**. Tell the user the app differs from the current template, so extending it risks breaking the bundle contract. Ask whether to (1) migrate it (`migrate/migrate.md`), (2) scaffold a fresh app under a new slug and port the code over, or (3) proceed at their own risk. Wait for the answer.

## Step 3 — Copy the template

```bash
APP_DIR="<repo>/data_apps/<slug>"
cp -R "<skill-dir>/setup/template/." "$APP_DIR/"
```

The app is a subdirectory of the repository, so this is a plain copy. Everything below runs in `$APP_DIR`. Keep the root-level `queries/` and `actions/` directories even while each holds only its README.

## Step 4 — Customize

1. Set the `name` in `package.json` to the slug.
2. Pin the SDK to the `65-beta` tag (the template ships `*`). Not `63-data-apps`, an older tag that lacks `data-app-dev/config`:

   ```bash
   npm install @metabase/embedding-sdk-react@65-beta
   ```

   The contract this skill describes (`write-resources`, `/api/apps/generate/*`) starts with Metabase 65, and `latest` predates it, so never use `latest`. The tag provides `@metabase/embedding-sdk-react/data-app`, the app's APIs, and `@metabase/embedding-sdk-react/data-app-dev/config`, the dev and build preset that `vite.config.ts` uses.

   If the user develops against a local SDK build, install that instead and skip the pin. They might say so, or the app's `package.json` might already point at one with a `file:` or `link:` version.
3. Make the repo-root `.gitignore` ignore `.env.local`, before any credentials file exists:

   ```bash
   ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
   if [ -z "$ROOT" ]; then
     echo "MISSING (run this from inside the connected git repo)"
   else
     GITIGNORE="$ROOT/.gitignore"
     [ -f "$GITIGNORE" ] || : > "$GITIGNORE"
     grep -qxF ".env.local" "$GITIGNORE" || echo ".env.local" >> "$GITIGNORE"
   fi
   ```
4. Create `.env.local` at the repository root (one file serves every app in the repository), then check its two variables without printing them:

   ```bash
   # An unguarded $(git ...) would expand to "/.env.local" outside a repo.
   ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
   if [ -z "$ROOT" ]; then
     echo "MISSING (run this from inside the connected git repo)"
   else
     ENV_FILE="$ROOT/.env.local"
     [ -f "$ENV_FILE" ] || cp .env.local.example "$ENV_FILE"
     ( source "$ENV_FILE" 2>/dev/null
       [ -n "$DATA_APP_MB_URL" ] && [ "$DATA_APP_MB_URL" != "mb_replace_me" ] &&
       [ -n "$DATA_APP_MB_API_KEY" ] && [ "$DATA_APP_MB_API_KEY" != "mb_replace_me" ]
     ) && echo "creds present" || echo "MISSING"
   fi
   ```

   If it prints `MISSING`, ask the user to fill in `DATA_APP_MB_URL` (the running Metabase instance) and `DATA_APP_MB_API_KEY` (from Admin > Authentication > API keys, a key in the Administrators group) in `<repo>/.env.local` themselves. Ask now, before anything needs the key. `creds present` means only that both variables are filled in. A bad URL or key shows up later, when a request fails.
5. **Generate `data_app.yaml` and the app's collection.** First check whether `data_apps/<slug>/data_app.yaml` exists. The template ships none, so a file there means the app already exists.

   Call `POST /api/apps/generate/app` with the API key in the `x-api-key` header, sourced from `.env.local` as above. The body holds the app's display name, its slug, and an optional description: `{"name": "Sales App", "slug": "sales-app", "description": "Pipeline health and quota attainment by region"}`.

   - A new app gets new entity IDs.
   - An existing app must send the IDs it has. Otherwise the call writes a new app with a new collection, and the app's saved questions and copies stay behind in the old one. Send its `entity_id` as `entity_id`, its `collection:` value as `collection_id`, and its `slug` unchanged. Regenerate an existing app only to change its name or description. If its `version` is lower than the one in the answer, the app is outdated: stop and migrate it first (`migrate/migrate.md`). Otherwise, copy its `allowed_hosts` into the new file.

   The answer is `{"files": [{"path": "...", "yaml": "..."}]}`: the app's `data_apps/<slug>/data_app.yaml` and its collection's file under `collections/data_apps/`. Write each `yaml` unchanged to its `path`, which is relative to the repo root. Any other answer is an error: show it to the user and stop.

   - **`description`** is one short sentence about what this app does, shown under its name in the admin list so admins can tell apps apart. Sync folds whitespace into single spaces and rejects more than 255 characters. Leave it out if it adds nothing beyond the name.
   - **`version`** is the contract version the app's code targets. Metabase writes it, so never change it by hand. Metabase raises the version it serves only on a breaking change. An app on an older version is marked _Outdated_, hidden from every other user, and won't open until it's migrated with `migrate/migrate.md`, one version at a time, never ad hoc.
   - **`allowed_hosts`** is needed only when the app calls an **external** API with `fetch`. XHR is blocked even for listed origins. Each origin listed, exact or a `*.` subdomain wildcard, opens to `fetch` in both `npm run dev` and Metabase. Never list the Metabase instance, and leave the key out entirely when the app talks only to Metabase. In Metabase, a native `<form action>` submit (`form-action`) and an `<iframe src>` or navigation (`frame-src`) obey the same list, and the target must also allow framing (`X-Frame-Options`, `frame-ancestors`), which many public sites don't. The dev preview blocks both, whatever the list. Prefer `<form onSubmit>` with `preventDefault`: a native submit navigates the sandboxed iframe away from the app.
6. Run `npm install`, or use the user's package manager. The template ships no lockfile, so keep whichever one the install creates.
7. Commit both the lockfile and the built bundle: a pull imports the committed file at `data_app.yaml`'s `path`, and the lockfile keeps installs reproducible. After installing and building, check `git status` to confirm both are committable.
8. If the preview hits CORS, add `http://localhost:5174` under Admin > Embedding > Embedded analytics SDK > CORS.

`npm run write-resources` writes into the collection that `data_app.yaml` names, so it refuses to run until that collection's file exists. The app's saved questions and copies come later, when you build its data layer (`semantic-layer/semantic-layer.md`).

## Step 5 — Verify the starter app

1. `npm run typecheck`.
2. `npm run check-resources`. It fails when `data_app.yaml` names no collection, or one without a file, and it validates the repository's YAML. It changes nothing in Metabase.
3. `npm run build`.
4. `git status` shows the app source, the lockfile, `data_app.yaml`, the collection's file under `collections/data_apps/`, and `dist/index.js` as committable files.
5. Run `npm run dev` and confirm the preview shows "Hello, data app". Read the diagnostics feed once (below). Expect `clients: 1` and no entry with `"alert": true`.
6. Confirm that `@metabase/embedding-sdk-react` is on `65-beta`.

Stop here if the user only asked to create or set up an app.

## Reading the diagnostics feed

`npm run dev` serves everything its corner **⚠ Diagnostics** toolbar shows as JSON. That's how you see runtime failures, since you have a shell, not a browser. Note `nextEventId` before an edit, make the change (an edit under `src/` rebuilds on its own), then read again from that ID. `startEventId` is inclusive and survives page reloads. Use the preview's own URL: the examples assume port 5174.

```bash
curl -s "http://localhost:5174/__data-app/diagnostics?startEventId=0"
```

```jsonc
{
  "entries": [{
    "eventId": 31, "kind": "blocked-network", "alert": true,
    "summary": "Blocked fetch to api.example.com (not in allowed_hosts)",
    "detail": null,   // stack frames, when any
    "hint": "Add https://api.example.com to allowed_hosts in data_app.yaml …",
    "buildId": 7      // the bundle generation that reported it
  }],
  "clients": 1,       // connected preview tabs; 0 means nothing ran
  "buildId": 7,       // the generation running now
  "staleEntries": 164, // withheld, reported by an older build
  "nextEventId": 32   // pass back as ?startEventId=
}
```

- **`clients: 0` doesn't mean healthy.** It means no preview tab is open, so empty `entries` prove nothing. Open `http://localhost:5174` first.
- The feed answers for the bundle that is running now. A multi-step edit passes through builds that don't compile or don't render. Their errors describe code the preview has already replaced, so they're withheld and counted in `staleEntries`. Anything still broken reports itself again under the new `buildId`. `?includeStale=true` returns the withheld entries when comparing builds is the point. A *failed* build doesn't advance `buildId`: the preview keeps running the last good bundle, so its entries stay current. The compile error goes to the `npm run dev` terminal, not the feed, so when `buildId` didn't advance after an edit, read the terminal.
- Read `hint` when there is one (`error`, `blocked-api`, and `sdk-call` entries have none), and quote `summary` as it is when you report it. Never add the Metabase URL to `allowed_hosts`, even when a hint says to: in the preview, a raw `fetch` to Metabase reports itself as not in `allowed_hosts`, and the fix is a data-app hook.

| `kind` | Fix |
|---|---|
| `blocked-network` / `csp-violation` | For an external API's `fetch`, add its origin to `allowed_hosts` in `data_app.yaml`, then **restart** `npm run dev`, which reads the allowlist and CSP at boot. For a `script-src` or `style-src` violation, bundle the asset instead. For Metabase, use the data-app hooks. |
| `blocked-api` | It's blocked in production too. Use an SDK API or drop the call. Don't work around it. |
| `sdk-call` + `alert: true` | A Metabase request failed. Fix the query. `summary` has the endpoint and status. |
| `error` | A real bug. `detail` has the stack. |

Text is truncated, and the buffer keeps the last 200 events, at most 50 of them `sdk-call`. `curl -X DELETE .../__data-app/diagnostics` clears it for every reader.

## Source conventions

Write plain ESM and TSX with normal package imports:

```tsx
import { StaticQuestion } from "@metabase/embedding-sdk-react";
import {
  DataAppLink,
  useMetabaseQuery,
} from "@metabase/embedding-sdk-react/data-app";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
```

- The build externalizes React, React DOM, the JSX runtimes, `@metabase/embedding-sdk-react`, and `@metabase/embedding-sdk-react/data-app` to sandbox globals, in `npm run dev` as in production. Import from the entrypoints as usual. Never read SDK values off `globalThis`: the sandbox globals there are private plumbing.
- Data-app APIs (routing, the data hooks, `useAction`, `copy`, the date pickers) come from `/data-app`. Components such as `StaticQuestion` come from the main entry.
- JSX uses the automatic runtime, so don't write `import React from "react"`. Import hooks by name, and React types as named type imports, not through the `React.` namespace.
- `dataAppConfig()` takes one override, `port`. The bundle contract (the factory shape, externals, the dev sandbox entry, CSS inlining, SVG handling) can't be overridden, and there's no way to add Vite plugins, aliases, or `define`s. There's no `index.html` either: the SDK's dev server serves the HTML shell. If you think you need one, solve the problem in `src/` instead.
- The build is one self-contained `.js` file. CSS is inlined, and every imported asset becomes a data URI: `import logo from "./logo.png"` gives a ready-to-use string, and `import Icon from "./icon.svg?react"` a React component. If the editor doesn't recognize `?react`, add `declare module "*.svg?react";` to a `.d.ts` file in `src/`. Keep large binaries out, since inlining inflates the bundle.

Layout once the starter grows:

```
queries/               defineQuery exports, one <topic>.query.ts per topic
actions/               defineAction exports, one <topic>.action.ts per topic
src/
├── index.tsx          the factory (from the template)
├── App.tsx            routing and composition only
├── theme.ts
├── metabase.data.ts   the generated schema
├── pages/             one file per screen
├── components/        shared UI
├── hooks/             hooks that call a query export, never define one
├── lib/               pure helpers
└── types/             shared types
```

Vite bundles everything reachable from `src/index.tsx`, so the layout under `src/` is only for readability.

## Theme rules

The `theme` in `src/theme.ts`, passed through `providerProps`, is the only way to change how SDK components look. It never styles your own UI: give page backgrounds, headers, and card wrappers inline `style` or CSS modules.

| Field | Purpose | Notes |
|---|---|---|
| `colors.brand` | Accent for SDK widgets | The app's primary color. |
| `colors.brand-hover`, `colors.brand-hover-light` | Hover backgrounds | A subtle tint that contrasts with hover text, never the saturated `brand`. For a blue brand, use something like `#EAF4FF`. |
| `colors.charts` | Chart palette | Fill all 8 slots, starting with the brand color. Metabase assigns series to slots, and an empty slot keeps Metabase's default color, so a short list leaves series in colors from outside the theme. Use vivid colors that are easy to tell apart, **never pale tints**: entries from index 1 on may color labels, and pale on white is invisible. |
| `colors.positive` / `colors.negative` | Semantic indicators | |
| `colors.background`, `colors.background-secondary` | SDK component surface | **Must match the SDK component's immediate parent container**: `"white"` inside a white card, the tint on a tinted page. |
| `colors.text-primary`, `text-secondary`, `text-tertiary` | Text on SDK surfaces | **Must contrast with `background`**, such as `#1f2937` on white. Set it whenever you set `background`. |
| `fontFamily` | SDK typography | |

If you set `colors.text-hover`, check that it contrasts with `brand-hover` and `brand-hover-light` in open menus, chart-type selectors, and visualization-settings dropdowns.

Several `<MetabaseProvider>`s fight over one set of CSS variables, so per-subtree theming doesn't work. When the look depends on state, recompute `sdkTheme` at the app level and let the whole tree re-theme.

## Custom error UI (optional)

When an embedded question or dashboard can't load (its `questionId` was removed, the user lacks access, or a request fails), Metabase renders a neutral built-in error state in its place. The dev preview shows the SDK's default error alert instead. Leave that alone unless the app has a strong reason to restyle it. To match the app's look, add an `errorComponent` to the factory's `providerProps`:

```tsx
// src/components/AppError.tsx
import type { SdkErrorComponentProps } from "@metabase/embedding-sdk-react";

export default function AppError({ message }: SdkErrorComponentProps) {
  return (
    <div style={{ padding: 16, textAlign: "center", color: "#6b7280" }}>
      {message}
    </div>
  );
}

// src/index.tsx
const factory: DataAppFactory = () => ({
  component: App,
  providerProps: { theme: sdkTheme, errorComponent: AppError },
});
```

- It replaces the error UI of **every** SDK component in the app, not only not-found errors, so keep the wording generic.
- `message` is a `ReactNode`. Render it as it is: don't call `.toString()` on it or index into it.
- Keep the component small and presentational, with no data hooks.

## Available SDK surface

| Import | Purpose |
|---|---|
| `StaticQuestion` | A question without drill-through. Props include `card`, `questionId`, `withChartTypeSelector`, `withDownloads`, `title`, `height`, `width`. |
| `InteractiveQuestion` | A drillable question, with the same props plus drill behavior. Pass `isSaveEnabled={false}` unless the app is an editing surface, and `title={false}` inside a card that has a heading. Choosing between the two and rendering a query are in `semantic-layer/semantic-layer.md`. |
| `MetabaseCard` | Type of the `card` prop. |
| `CreateQuestion`, `MetabotQuestion` | More question variants. |
| `StaticDashboard`, `InteractiveDashboard`, `EditableDashboard` | Dashboard variants. |
| `CreateDashboardModal` | The new-dashboard flow. |
| `CollectionBrowser` | A collection picker. |
| `@metabase/embedding-sdk-react/data-app` | Routing (`routing/routing.md`), the data hooks and query helpers (`semantic-layer/semantic-layer.md`), `useAction` (`actions/actions.md`), `copy`, and `DateRangePopover`, `DateRangeCalendar`, and `useDateFormatter` for date ranges. |

### Blocked APIs

The sandbox throws at runtime on these globals. Use the replacement:

| Blocked | Use instead |
|---|---|
| **Network**: `fetch`, `XMLHttpRequest`, `WebSocket` | The SDK and data-app APIs for Metabase reads and writes. Raw `fetch` reaches **only** the external origins in `data_app.yaml`'s `allowed_hosts` (Step 4). Any other `fetch`, the Metabase origin included, rejects. XHR is always blocked: an instance can be constructed, but its methods throw. `WebSocket` is always blocked. |
| **Dialogs**: `alert`, `confirm`, `prompt` | A React modal in your own tree. |
| **Storage**: `localStorage`, `sessionStorage`, `indexedDB`, `document.cookie` | Nothing persists across reloads. Persist through a Metabase action. |
| **Window and history navigation**: `window.open`, `history.pushState`, `history.replaceState` | `useDataAppLocation().navigate` inside the app, and `<a target="_blank" rel="noopener">` for external links. |
| **Clipboard**: `document.execCommand("copy")`, `navigator.clipboard` | `import { copy } from "@metabase/embedding-sdk-react/data-app"`, then `await copy(text)` from a user event. It's write-only: there is no paste API, since one would let a bundle read whatever the user copied. |
| **Other `navigator.*` device APIs**, such as `geolocation` | Not available. |
| **Global `document`/`window` listeners** for typing and clipboard events: `keydown`, `keyup`, `keypress`, `beforeinput`, `input`, `paste`, `copy`, `cut`, `before*paste/copy/cut`, `compositionstart/update/end`, `storage` | Attach the listener to your own element, or use the React handler (`onKeyDown`, `onPaste`, …) on the input or container. |

If you're about to touch `window.X`, `document.X`, `navigator.X`, `history.X`, or a storage global, stop and pick the replacement above. React, React DOM, the SDK components, the data hooks, `useAction`, the routing primitives, `DateRangePopover`, and `copy` cover every routine need. Anything outside them is unreachable on purpose.

## App layout: fill the frame height

Metabase and `npm run dev` both give the bundle a full-height frame, but nothing in between sets a height, so a short app ends where its content ends and leaves bare white below. Give the app's outermost element `minHeight: "100vh"` (plus `boxSizing: "border-box"` when it has padding), and paint the page background on it. Use `minHeight`, never `height`, so taller content still scrolls. Regions that should reach the bottom, such as a sidebar or a sticky footer, go in a flex-column root with `flex: 1`. Check the emptiest screens (loading, empty states, a lone KPI), since they render shortest.

## SDK component sizing

SDK components don't fit their parent on their own: without `height` and `width` they render at their intrinsic size and overflow. A height on the outer container or card isn't enough either. Give the height to the component that owns the visualization:

- A chart alone: `InteractiveQuestion.QuestionVisualization`.
- The default question layout with its query bar: `InteractiveQuestion`.
- A static question: `StaticQuestion`.

Pass the height actually available to the chart: in a 560px card with a 60px header, `height="500px"`. Or pass `height="100%"` inside a container with a fixed height. Here `card` is a memoized card, as in `semantic-layer/semantic-layer.md`, _Render a query_:

```tsx
<div style={{ height: 360 }}>
  <StaticQuestion card={card} height="100%" width="100%" />
</div>
```

Don't wrap an SDK question in a container that clips or moves on hover: no `overflow: hidden`, hover transforms, or hover-driven layout shifts. Popovers, menus, and tooltips need stable geometry and visible overflow.

## Sync to Metabase

1. After any change to `queries/` or `actions/`, run `npm run write-resources`, regenerating `src/metabase.data.ts` first if it doesn't cover what the definitions use. Then run `npm run check-resources`.
2. Run `npm run build`. It fails when the app's collection files don't match the definitions: run `npm run write-resources` and build again.
3. From the **repo root**, commit the app directory together with the app's collection files, and push:

   ```bash
   git add data_apps/<slug> collections/data_apps
   git commit -m "Add <slug> data app"
   git push
   ```
4. The app appears at `/apps/<slug>` on Metabase's next remote-sync import: a manual pull (**Pull changes** in the Git sync menu, or under Admin > Settings > Remote sync), the auto-import poll, or a restart.

Don't offer to "deploy" the app, and don't ask how the bundle reaches a staging environment. Metabase imports the committed bundle straight from the connected repository. Once the change is on the branch Metabase syncs from, however the user gets it there (a merged PR or a direct push), tell them to pull it in and open `/apps/<slug>`. An update is the same loop: `write-resources` if the definitions changed, a new build, a commit, and another pull.

## Removing an app

Delete the app's directory **and** its collection's files in one commit, from the repo root, and push:

```bash
git rm -r data_apps/<slug> collections/data_apps/<collection>.yaml collections/data_apps/<collection>
git commit -m "Remove <slug> data app"
git push
```

`<collection>` is the collection that `data_app.yaml` names as `collection`: the file under `collections/data_apps/` whose `entity_id` is that value, and the directory of the same name beside it. The collection is named after the slug, so the app `order-desk` has `Data App: order-desk`, slugged `data_app__order_desk`. The next pull removes the app, along with its collection, saved questions, and copies of metrics and actions.

Delete both. If the directory goes without the collection's files, the next pull still removes the app and its collection, and Metabase's next push deletes the files. Until that push, though, a pull that reloads every file brings the collection back with no app owning it, and the push then keeps it. The other way round is refused: a pull fails when an app's directory stays but its collection file is gone.

## Common pitfalls

| Symptom | Fix |
|---|---|
| "Failed to fetch the user, the session might be invalid." | A bad API key, or CORS. Check the key by sourcing the repo-root `.env.local` in a subshell, as in Step 4, and running `curl -H "x-api-key: $DATA_APP_MB_API_KEY" "$DATA_APP_MB_URL/api/user/current"`. Add `http://localhost:5174` to the SDK CORS origins. |
| Invisible chart labels. | Set `text-primary` in the theme (_Theme rules_). |
| A chart looks unlike the rest of the instance, ignores the theme, or has no tooltips, formatting, or drill-through. | It was built in React. Render it with `StaticQuestion` or `InteractiveQuestion` and a `visualization` (`semantic-layer/semantic-layer.md`, _Rendering_ under _Rules_). |
| A chart overflows its container. | Pass `height` and `width` to the SDK component (_SDK component sizing_). |
| The app's background stops partway down the frame. | Give the root `minHeight: "100vh"` (_App layout_). |
| "Invalid hook call" at runtime. | Two copies of React. `dataAppConfig()` externalizes `react`: make sure `react` and `react-dom` are installed and nothing adds a second or mismatched React. |
| The bundle is several MB. | React and the SDK aren't externalized. Confirm `vite.config.ts` still uses `dataAppConfig()` and the data-apps SDK tag is installed. A large but not multi-MB bundle can be inlined assets. |
| `dist/index.js` doesn't assign `__dataAppFactory__`, or the preview is blank with `Bundle did not assign a function to __dataAppFactory__`. | `src/index.tsx` must `export default` the `DataAppFactory` and export nothing else. Otherwise app code throws while the sandbox evaluates the bundle: read the real error in the diagnostics feed. |
| `Cannot find module '@metabase/embedding-sdk-react'`. | Run `npm install`, or the equivalent for the package manager. |
| Drill popups don't open, or SDK components render empty, in dev. | The app renders its own `<MetabaseProvider>`. Remove it. |
| A network call works in `npm run dev` but is blocked after syncing. | `allowed_hosts` was edited without restarting the dev server, so the running sandbox still used the old list. Restart `npm run dev`. The feed's `manifest` section flags this as `restartRequired`. |
| The SDK was rebuilt or reinstalled, but the preview behaves like the old version. | Vite caches its pre-bundled SDK in `node_modules/.vite`, keyed on the lockfile and the Vite config, so rebuilding the package in place doesn't invalidate it. Stop the dev server, delete `node_modules/.vite`, and start it again, or run `npx vite --force`. |
| The preview doesn't pick up a change to `queries/` or `actions/`. | Only edits under `src/` rebuild the preview. Save a file under `src/`, or restart `npm run dev`. |
| Component state resets on every edit. | Expected: each edit rebuilds the bundle and remounts the app in the sandbox. |
