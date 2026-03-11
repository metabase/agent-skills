---
name: metabase-modular-embedding-to-modular-embedding-sdk-upgrade
description: Migrates a React project from Metabase Modular embedding (embed.js web components) to the Modular embedding SDK (@metabase/embedding-sdk-react). Replaces metabase-dashboard, metabase-question, metabase-browser custom elements with React SDK components, removes embed.js script tag, and converts window.metabaseConfig to MetabaseProvider. Use this skill whenever the user wants to migrate/convert/switch from modular embedding to modular embedding SDK, from embed.js to React SDK, from EmbedJS to SDK, from web components to React components, or stop using embed.js and use MetabaseProvider instead. This is NOT a version upgrade — it changes the embedding technology.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Execution contract

Follow the workflow steps in order — do not skip any step. Create the checklist first, then execute each step and explicitly mark it done with evidence. Each step's output feeds into the next, so skipping steps produces wrong migrations.

If you cannot complete a step due to missing info or tool failure, you must:

1. record the step as ❌ blocked,
2. explain exactly what is missing / what failed,
3. stop (do not proceed to later steps).

### Required output structure

Your response should contain these sections in this order:

1. **Step 0: Prerequisites Check**
2. **Migration Plan Checklist** (Step 0.1)
3. **Step 1: Project Scan**
4. **Step 2: Target SDK API**
5. **Step 3: Migration Mapping**
6. **Step 4: Applied Code Changes**
7. **Step 5: Typecheck Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

### Evidence requirements

- Step 0: React detected (dependency + version), Metabase instance version, target SDK version, package manager.
- Step 1: every file with Modular embedding usage (web components, metabaseConfig, embed.js script tag), with matching grep lines.
- Step 2: confirm d.ts loaded in context. List exported components, their props, and the MetabaseProvider config type.
- Step 3: the structured migration mapping — every web component → React component with prop conversions, auth config mapping, and embed.js removal plan.
- Step 4: per file — what was changed and exact diffs applied.
- Step 5: the exact typecheck command run and error summary if any remain.

## Performance

The workflow is designed as a pipeline:

```
Round 1 (grep+glob+pkg) ──► Round 2 (prepare.sh) ──► Round 3 (read-sources.sh) ──► Step 3 (mapping, inline)
                                                                                          │
                                                                                    Step 4 per-file:
                                                                                     ├── Convert FileA
                                                                                     ├── Convert FileB
                                                                                     └── Convert FileC
                                                                                           │
                                                                                     Step 5 (typecheck) ──► Step 6
```

In Claude Code, use parallel tool calls or `run_in_background: true` for sub-agents.

Do not parse repo branches, commits, PRs, or issues — they're noisy and irrelevant.

### Tool-call round budget for Steps 1+2

Steps 1+2 must complete in **3 tool-call rounds**.

**Round 1** — discovery (all concurrent, single message):
- Grep for `metabase-dashboard`, `metabase-question`, `metabase-browser` in `*.{jsx,tsx,js,ts}` files
- Grep for `window.metabaseConfig`
- Grep for `/app/embed.js` (to find the script tag)
- Read `package.json` (to confirm React dependency and detect package manager)
- Glob for lock files (`yarn.lock`, `pnpm-lock.yaml`, `package-lock.json`)
- `npm view @metabase/embedding-sdk-react version` (if target not specified by user)

All tool calls in one message.

**Round 2** — `prepare.sh` alone (single Bash call, nothing else):
```bash
bash <skill-path>/scripts/prepare.sh {TARGET_VERSION}
```
Downloads the target SDK npm package and extracts it. Outputs `SDK_TMPDIR` and d.ts availability.

**No other tool calls in this message.** Bash calls get cancelled if a parallel Read errors.

**Round 3** — `read-sources.sh` (single Bash call):
```bash
bash <skill-path>/scripts/read-sources.sh {SDK_TMPDIR}
```
Dumps the target SDK's d.ts type definitions to stdout.

After Round 3, output Step 1 Results + Step 2 Results + Step 3 Migration Mapping with zero additional tool calls. Produce Step 3 inline right after the data is loaded.

## Scope

This skill converts Modular embedding web components used inside a React app to the Modular embedding SDK (`@metabase/embedding-sdk-react`). The project must already be a React application with Modular embedding web components in JSX/TSX files.

If the project is not React-based, this skill does not apply. If the project uses iframes instead of web components, use the `metabase-full-app-to-modular-embedding-upgrade` skill instead.

### What this skill handles

- Replacing `<metabase-dashboard>`, `<metabase-question>`, `<metabase-browser>` web components in JSX/TSX with their SDK React equivalents
- Installing the `@metabase/embedding-sdk-react` npm package
- Adding `<MetabaseProvider>` at the appropriate level in the React component tree
- Converting `window.metabaseConfig` to `MetabaseProvider` config props
- Removing the `embed.js` `<script>` tag (typically in `index.html` or the HTML entry point)
- Removing the `window.metabaseConfig` assignment
- Converting HTML attribute naming (kebab-case) to React prop naming (camelCase)

### What this skill does NOT handle

- Non-React projects using Modular embedding web components in plain HTML/templates
- Migrating from Full App (iframe-based) embedding — use the `metabase-full-app-to-modular-embedding-upgrade` skill instead
- Upgrading the SDK version after installation — use the `metabase-modular-embedding-version-upgrade` skill for future upgrades

## Detecting versions

Do all version detection in Round 1.

- **Metabase instance version**: grep for Docker image tags (`metabase/metabase:v`), `METABASE_VERSION`, or version references in env files. If undetected, AskUserQuestion.
- **Target SDK version**:
  - If user specifies, use it.
  - Otherwise, use the Metabase instance version to determine the matching SDK version (they use the same version scheme: Metabase v0.58 → SDK 0.58.x). Run `npm view @metabase/embedding-sdk-react version` to find the latest matching version.
- **Package manager**: detect from lock files — `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm, `package-lock.json` → npm.

## Pre-workflow steps

### Migration Plan Checklist

Create a checklist to track progress. In Claude Code, use TaskCreate/TaskUpdate tools:

- Step 0: Prerequisites check
- Step 1: Scan Modular embedding usage
- Step 2: Fetch target SDK API
- Step 3: Build migration mapping
- Step 4: Apply code changes (one sub-task per file)
- Step 5: Typecheck and fix
- Step 6: Final summary

## Workflow

### Step 0: Prerequisites check

Verify before starting:

1. **React dependency**: check `package.json` for `react` in `dependencies` or `devDependencies`. If not present, mark ❌ blocked — this skill only applies to React projects.
2. **Web components in JSX/TSX**: confirm the grep results from Round 1 show `<metabase-*` usage in `.jsx`, `.tsx`, `.js`, or `.ts` files (not only in plain HTML). If web components are only in plain HTML files, mark ❌ blocked — this skill requires web components to already be used inside React.
3. **Metabase instance version**: detect or ask user.
4. **Target SDK version**: determine as described in "Detecting versions".
5. **Package manager**: detect from lock files.

### Step 1: Scan Modular embedding usage

Step 1 happens in Round 1 — grep only, no file reading.

Grep for these patterns (all in parallel):

- `<metabase-dashboard` in `*.{jsx,tsx,js,ts}` files — dashboard web components
- `<metabase-question` in `*.{jsx,tsx,js,ts}` files — question web components
- `<metabase-browser` in `*.{jsx,tsx,js,ts}` files — collection browser web components
- `window.metabaseConfig` — global config assignment (may be in `index.html` or a JS/TS file)
- `/app/embed.js` — the embed.js script tag (typically in `index.html`)

This returns file paths + matching lines. Do not read project files yet — that happens in Step 4.

**Output**: a file list grouped by category:
```
Web components (JSX/TSX):
  - src/pages/Dashboard.tsx:15 — <metabase-dashboard dashboard-id="123">
  - src/pages/Analytics.tsx:22 — <metabase-question question-id="456">
Config:
  - public/index.html:8 — window.metabaseConfig = { ... }
Script tag:
  - public/index.html:12 — <script defer src="...embed.js"></script>
```

### Step 2: Fetch target SDK API

Run `prepare.sh` in Round 2 (see round budget). Then `read-sources.sh` in Round 3 to load the d.ts into context.

If d.ts is available, extract from it:
- All exported React components (e.g., `MetabaseProvider`, dashboard/question/collection components)
- Their prop types (resolved to concrete types, not just alias names)
- The `MetabaseProvider` config type (what fields it accepts)
- The auth config type

If d.ts is not available (very old SDK versions), mark Step 2 ❌ blocked — the user should target a newer SDK version.

### Step 3: Build migration mapping (after Steps 1–2 are ✅ complete)

**Scope: only map components and config actually found in Step 1's scan.**

Produce a mapping that covers:

#### Component mapping

For each web component found in Step 1, identify the SDK React equivalent from the d.ts. Map attributes to props:

```
## Migration Mapping

### <metabase-dashboard> → {SDK dashboard component from d.ts}
- `dashboard-id` → `dashboardId` (camelCase)
- `with-title` → `withTitle` (boolean prop)
- `drills` → check d.ts for equivalent prop name
- Other attributes → map to corresponding React props from d.ts

### <metabase-question> → {SDK question component from d.ts}
- `question-id` → `questionId` (camelCase)
- Other attributes → map from d.ts

### <metabase-browser> → {SDK collection component from d.ts}
- `initial-collection` → check d.ts for prop name
- Other attributes → map from d.ts
```

For each mapping, resolve the target prop type to its concrete type. If an attribute has no SDK equivalent, note it as "dropped (not supported in SDK)" or "requires alternative approach".

#### Auth config mapping

Map `window.metabaseConfig` fields to `MetabaseProvider` config:

```
### Auth & Config
- window.metabaseConfig.instanceUrl → config.metabaseInstanceUrl (check d.ts for exact field name)
- window.metabaseConfig.jwtProviderUri → authConfig.jwtProviderUri or config.jwtProviderUri (check d.ts)
- window.metabaseConfig.locale → locale prop or config field (check d.ts)
```

The d.ts is the authoritative source for field names — do not guess. If a `window.metabaseConfig` field has no equivalent in the SDK config type, note it.

#### MetabaseProvider placement

Determine where to add `<MetabaseProvider>`:
- Find the highest common ancestor component that contains all Modular embedding web components
- Typically this is the app root (`App.tsx`, `App.jsx`, or equivalent)
- The provider must wrap all SDK components but should not unnecessarily wrap the entire app if components are isolated to a subtree

#### Removal plan

- embed.js `<script>` tag: identify file and exact code to remove
- `window.metabaseConfig` assignment: identify file and exact code to remove

### Step 4: Apply code changes

**Before per-file work:**

1. Install the SDK package:
   ```bash
   {package-manager} add @metabase/embedding-sdk-react@{TARGET_VERSION}
   ```
2. Remove the embed.js `<script>` tag
3. Remove the `window.metabaseConfig` assignment
4. Add `<MetabaseProvider>` wrapper at the determined location with the migrated config

**Per-file task** (for each file containing web components):

1. **Read the file** — first time file content is loaded.
2. **Match mapping entries** — which web components are in this file, what are their current attributes?
3. **Convert each web component**:
   - Replace the web component tag with the SDK React component
   - Convert HTML attributes (kebab-case) to React props (camelCase)
   - Convert string attribute values to appropriate JS types (e.g., `"false"` → `{false}`, `"123"` → `{123}`)
   - Add the import statement for the SDK component
4. **Report** — output what was changed.

**Parallelization strategy:**

- **≤ 10 files**: process all in the main agent.
- **> 10 files**: batch into 3–5 sub-agents. Each receives its file paths and the full migration mapping.

#### Type conversion rules

When converting HTML attribute values to React props:
- String `"true"` / `"false"` → boolean `{true}` / `{false}`
- Numeric strings `"123"` → number `{123}` (only if the d.ts prop type is `number`)
- Template expressions already in JSX (e.g., `{dashboardId}`) → keep as-is
- Static string IDs → keep as strings if the d.ts prop type accepts strings, otherwise convert

### Step 5: Typecheck validation

1. **Run typecheck** — `npm run typecheck`, `tsc --noEmit`, or the project's equivalent.
2. **Analyze errors** — categorize SDK-related errors by root cause.
3. **Look up expected types** — search the installed `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` for each failing symbol.
4. **Fix in batch** — apply all fixes before re-running typecheck.
5. **Verify** — re-run typecheck. If errors remain after 3 rounds, mark ❌ blocked.

If the project does not use TypeScript, manually review each change against the d.ts to verify prop names and types match. Mark Step 5 ✅ with a note that validation was manual.

### Step 6: Output summary

Organize into these sections:

**1. Changes applied** — list every file modified and a one-line description of each change.

**2. Component mapping** — table showing each old web component → new React component:
```
| File | Old | New | Props Changed |
|---|---|---|---|
| src/Dashboard.tsx | <metabase-dashboard dashboard-id="1"> | <InteractiveDashboard dashboardId={1} /> | dashboard-id → dashboardId |
```

**3. Auth migration** — how `window.metabaseConfig` was converted to `MetabaseProvider` config.

**4. Removed artifacts** — embed.js script tag, window.metabaseConfig, any dead code.

**5. New capabilities** — SDK features now available that weren't in Modular embedding (e.g., React hooks, typed callbacks, sub-components like `InteractiveQuestion.FilterBar`). Keep brief.

**6. Instance requirements** — minimum Metabase instance version needed. The Metabase instance version must match the SDK version (e.g., SDK 0.58.x requires Metabase v0.58+).

## Retry policy

**npm pack:**
- If `npm pack` fails for the target version, it likely doesn't exist on npm. Mark as ❌ blocked and inform the user.

**npm install:**
- If package installation fails due to peer dependency conflicts, try with `--legacy-peer-deps` (npm) or equivalent. Report the conflict to the user.
