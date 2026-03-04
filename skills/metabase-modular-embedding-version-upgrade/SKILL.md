---
name: metabase-modular-embedding-version-upgrade
description: Helps to provide info about breaking changes between different Metabase versions. Use when the user wants to upgrade a Metabase Embedding SDK or Metabase EmbedJS/Modular Embedding version.
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

1. **Upgrade Plan Checklist** (Step 0)
2. **Parallel Plan (Single Launch)** (Step 0.1)
3. **Step 1 Results: Project Scan**
4. **Step 2 Results: d.ts Diff / Target Docs** (primary or fallback)
5. **Step 3: Combined Breaking Changes + Migrations**
6. **Step 4: Applied Code Changes**
7. **Step 5: Typecheck Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

### Step gating rules

Each step depends on the results of previous steps — starting early produces wrong output:

- Step 1 and Step 2 Phase 1 run concurrently (they're independent).
- Step 2 Phase 2 starts after BOTH Step 1 and Phase 1 are complete (it uses Step 1's usage inventory to target fetching).
- Do not start Step 3 until Steps 1–2 are ✅ complete (Step 3 cross-references their outputs).
- Do not start Step 4 until Step 3 is ✅ complete (Step 4 applies the changes Step 3 identified).
- Do not start Step 5 until Step 4 is ✅ complete.
- Do not output Step 6 until Step 5 is ✅ complete (or explicitly ❌ blocked).

### Evidence requirements

- Step 1 evidence: list every matched file path, every import/reference (from `@metabase/embedding-sdk-react` for SDK, or embed script tags/init calls for EmbedJS), every used component/hook/type, every prop/config option used per component, every dot-subcomponent used (e.g., `InteractiveQuestion.FilterBar`), and for callback props — where the callback parameter data flows in the project (e.g., `onClick: (item) => setSelectedId(item.id)` where `setSelectedId` is `useState<number>`).
- Step 2 evidence (primary path): show the diff output between d.ts files. (fallback path): list each fetched URL for both current and target versions + include raw extracted sections that contain prop tables / type definitions / migration sections from both. Do not summarize away details — Step 3 needs the full text to cross-reference both sides.
- Step 3 evidence: for each used prop/config option, show the target type (from d.ts for SDK, or from docs for EmbedJS) AND the current usage from the project side-by-side. Example format: `fetchRequestToken: project uses (url: string) => Promise<any>, target type is () => Promise<{jwt: string}> → BREAKING (arity change)`.
- Step 4 evidence: show the exact diffs applied (or file edits described precisely).
- Step 5 evidence: show the exact command run (e.g., `npm run typecheck` or `tsc --noEmit`) and summarize errors if any remain.

## Performance

Step 2 is split into two phases to balance parallelism with precision:

- **Phase 1 (parallel with Step 1)**: Run `npm pack` for both versions + curl the changelog. These are network calls that don't need project scan results.
- **Phase 2 (after Step 1 completes)**: Targeted doc/type fetching based on which components the project actually uses. This avoids fetching docs for unused components.

In Claude Code, launch Step 1 and Step 2 Phase 1 as parallel tool calls in the same message, or use `run_in_background: true` for one of them.

Do not parse repo branches, commits, PRs, or issues — they're noisy and irrelevant to version diffing.

## Scope

This skill handles upgrades for:

- `@metabase/embedding-sdk-react` (React SDK, v52+) — uses primary or fallback path
- EmbedJS / Modular Embedding (v56+) — always uses fallback path (no npm types available)
  - v56–v57: docs are at `embedded-analytics-js.md`
  - v58+: docs split into `components.md`, `appearance.md`, `authentication.md`

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com` (preserves `include_file` directives needed for snippet expansion)
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## Detecting versions

- Current version: read from the project's `package.json` (check `dependencies` and `devDependencies`) for `@metabase/embedding-sdk-react`. In monorepos, also check workspace-level `package.json` files.
- Target version:
  - If user specifies, use it.
  - Otherwise run `npm view @metabase/embedding-sdk-react version` in the terminal to get the latest.
- Package manager: detect from lock files — `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm, `package-lock.json` → npm. Use the matching install command in Step 4 (e.g., `yarn install`, `pnpm install`).

If package not present OR user is upgrading EmbedJS/Modular Embedding:

- Ask the user for the current Metabase instance version and current EmbedJS/Modular Embedding version. In Claude Code, use the AskUserQuestion tool for this.
- Mark Step 0 ❌ blocked until answered.

### Multi-version hops

When the upgrade spans a major structural boundary (e.g., v0.54 → v0.58 crosses the auth config change at v0.55 AND the doc layout change at v0.58), handle it as a single migration to the target version — do not do intermediate upgrades. However, during Step 3, check the auth config evolution section and account for every breaking change along the path. For example, v0.52 → v0.58 means the auth config changed shape (v0.55) AND gained `jwtProviderUri` (v0.58) — both changes need to be reflected in the migration.

## Pre-workflow steps

### Upgrade Plan Checklist (required before any other work)

Create a checklist to track progress through these steps. In Claude Code, use the TaskCreate/TaskUpdate tools to track each step's status:

- Step 1: Scan project usage
- Step 2: Extract d.ts diff or fallback to docs
- Step 3: Compile breaking changes + migrations
- Step 4: Apply code changes
- Step 5: Run typecheck and fix until clean
- Step 6: Final summary

### Parallel Plan (required)

State which steps will run in parallel:

- **Concurrent**: Step 1 (project scan) + Step 2 Phase 1 (npm pack both versions + curl changelog)
- **After both complete**: Step 2 Phase 2 (targeted doc/type fetching based on Step 1 results)
- **Sequential**: Steps 3 → 4 → 5 → 6

If your agent supports parallel execution or background tasks, plan accordingly. In Claude Code, you can use `run_in_background: true` for sub-agents or issue multiple tool calls in the same message.

### Path Selection

Determine which path to use:

- If upgrading `@metabase/embedding-sdk-react` → attempt **primary path** (d.ts diff), with fallback if d.ts unavailable (determined during Step 2)
- If upgrading EmbedJS/Modular Embedding → **fallback path** (skip d.ts extraction entirely)

## Workflow

### Step 1: Scan the project code

Keep scan results in the main context (not delegated to a sub-agent) — Step 3 needs them for cross-referencing.

**For SDK upgrades (`@metabase/embedding-sdk-react`):**

- Search the codebase for all imports from `@metabase/embedding-sdk-react`. In Claude Code, use the Grep tool; in other agents, use your codebase search or `grep -r`.
- Read all matching files. In Claude Code, read them in parallel in a single message for speed.
- Extract:
  - imports, components, hooks, types, helpers
  - every prop used per component
  - every dot-subcomponent used
  - for callback props (`onClick`, `onCreate`, `onNavigate`, etc.): what fields are accessed from the callback parameter and where those values flow in the project (state setters, variables, API calls, route params). This is critical — Step 3 needs this to catch data-flow breaking changes.
- Output a structured "Usage Inventory".

**For EmbedJS / Modular Embedding upgrades:**

- There is no npm package to scan. Instead, search the codebase for:
  - Metabase embed `<script>` tags (e.g., patterns like `metabase.js`, `embed.js`, `embedding-sdk`, or the Metabase instance URL)
  - Any JS calls to Metabase embedding APIs (e.g., `MetabaseEmbed`, `Metabase.embed`, `window.MetabaseEmbed`, `initMetabase`, component init calls)
  - Configuration objects passed to embed init functions (auth config, appearance, theme, component options)
- Read all matching files.
- Extract:
  - which components are embedded (dashboard, question, query builder, collection browser)
  - all configuration options / props passed to each component
  - authentication setup (JWT endpoint URL, auth config shape)
  - appearance / theme customizations
- Output a structured "Usage Inventory".

### Step 2: Extract API changes

Step 2 has two phases. Phase 1 runs concurrently with Step 1. Phase 2 runs after Step 1 completes.

#### Phase 1: Probe (concurrent with Step 1)

Launch these in parallel with Step 1 — they're all network calls that don't need project scan results.

**For SDK upgrades** — run the probe script to download both versions, fetch the changelog, and check d.ts availability:

```bash
bash <skill-path>/scripts/probe-versions.sh {CURRENT} {TARGET}
```

This outputs `SDK_TMPDIR`, `CHANGELOG`, and d.ts availability (`current_dts=yes/no`, `target_dts=yes/no`). Record the d.ts availability — it determines Phase 2's strategy.

If the script isn't available, the equivalent steps are: `npm pack` both versions into a temp directory, `tar xzf` each, `curl` the changelog, and check for `package/dist/index.d.ts` in each.

**For EmbedJS / Modular Embedding upgrades** — no npm pack, just fetch the changelog:

```bash
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" -o /tmp/sdk-changelog.md
```

#### Phase 2: Targeted fetch (after Step 1 + Phase 1 complete)

Now you have the project's Usage Inventory from Step 1 (which components/props are actually used) and the d.ts availability from Phase 1. Use both to minimize work.

**Determine the strategy based on d.ts availability:**

| Current d.ts | Target d.ts | Strategy |
|---|---|---|
| ✅ | ✅ | **Full d.ts diff** — diff both files, read changelog for migration instructions. Fastest path. |
| ✅ | ❌ | **Hybrid** — read current d.ts for type info, fetch target docs (targeted). |
| ❌ | ✅ | **Hybrid** — fetch current docs (targeted), read target d.ts for type info. |
| ❌ | ❌ | **Full docs comparison** — fetch docs for both versions (targeted). |
| EmbedJS | EmbedJS | **Full docs comparison** — always fetch docs for both versions (targeted). |

**Full d.ts diff** (both versions have d.ts):

```bash
diff -u "$SDK_TMPDIR/current/package/dist/index.d.ts" "$SDK_TMPDIR/target/package/dist/index.d.ts" || true
```

Read the changelog and extract entries between {CURRENT} and {TARGET} for migration instructions.

**Hybrid path** (one version has d.ts, the other doesn't):

For the version WITH d.ts: read the full `index.d.ts` file — it contains all type definitions.
For the version WITHOUT d.ts: fetch docs using the targeted approach below.
Also read the changelog for migration instructions.

**Targeted doc fetching** (for versions that need docs):

Use `scripts/fetch-docs.sh` to discover and fetch all available doc pages for each version. The script uses the GitHub Contents API to find what exists — no hardcoded page lists. It also automatically discovers and fetches snippet files referenced via `include_file` directives.

```bash
# Fetch target SDK docs (any version format works: 58, 0.58, v0.58, 0.58.1)
bash <skill-path>/scripts/fetch-docs.sh \
  --version {VER} --type sdk --prefix target --outdir /tmp/sdk-docs

# Fetch current EmbedJS docs
bash <skill-path>/scripts/fetch-docs.sh \
  --version {VER} --type embedjs --prefix current --outdir /tmp/embedjs-docs
```

Then read all fetched files from the output directory. The LLM focuses on pages relevant to the Usage Inventory from Step 1 — the script fetches everything available, and the analysis step filters by relevance.

#### What to extract from Phase 2 results

After reading all fetched data (d.ts files, docs, changelog), build the API change summary:
- **Full d.ts diff**: the diff output shows all type changes; supplement with changelog for migration instructions
- **Hybrid**: compare the d.ts types from one side against the doc-described API from the other
- **Full docs comparison**: for each component used in the project, compare props/options/types between current and target docs
- In all cases: identify added, removed, renamed, or type-changed props/options, and note migration instructions from changelog or target docs

### Step 3: Summarize changes (after Steps 1–2 are ✅ complete)

Cross-reference the project's actual usage (Step 1) against the API changes found in Step 2:

- **Primary path** (d.ts diff available): compare each used prop/subcomponent/type from Step 1 against the d.ts diff
- **Fallback path** (docs comparison): compare each used prop/subcomponent/type from Step 1 against the differences between current-version docs and target-version docs, supplemented by the changelog

#### Deep type resolution

For every prop identified in Step 1, resolve its type in the target d.ts **all the way down to the concrete signature**. Do not stop at type alias names — alias names can stay the same while the underlying type changes, which is a common source of missed breaking changes.

**Step A — Resolve the prop's own type:**
1. For each prop used in the project, search the target d.ts for that prop name and note its type.
2. If the type is a **type alias** (e.g., `MetabaseFetchRequestTokenFn`, `SdkDashboardId`, `SdkCollectionId`), search the target d.ts for that alias's definition and expand it to its concrete type (e.g., `() => Promise<{jwt: string}>`, `number | string`).
3. Compare the **fully resolved concrete type** against the project's current usage (argument counts, argument types, return types, value types).
4. A prop can have the same name but a completely different type signature — this is a breaking change. Renaming is not the only kind of breaking change.

Example: `fetchRequestToken` kept its name but changed from `(url: string) => Promise<any>` to `() => Promise<{jwt: string}>` — different arity, different return type.

**Step B — Trace callback data flow into project code:**

A callback prop can be "compatible" at the interface level but still break the project. The SDK sends data INTO the project through callback parameters — if the types of that data widened, the project code receiving it may not handle the new variants.

For every callback prop (e.g., `onClick`, `onCreate`, `onNavigate`):
1. Resolve the types of the callback's **parameters** in the target d.ts — not just the callback signature, but the fields accessed inside. For example, if `onClick` receives `(item) => void`, resolve what `item.id`, `item.model`, etc. are in the target.
2. In the project code, trace where those fields **flow to**: state setters (`useState<number>`), function arguments, variable assignments, API calls, route parameters.
3. Check if the project's receiving type is compatible with the target's widened type. For example, if `item.id` widened from `number` to `number | string | "personal" | "root"`, but the project assigns it to `useState<number>`, that's a breaking change — even though the callback signature itself is fine.

This matters because SDK type widenings (especially ID types like `SdkCollectionId`, `SdkDashboardId`, `SdkEntityId`) often add string union members to what was previously a plain `number`. Project code that stores these IDs in `number`-typed state, passes them to APIs expecting `number`, or uses them in arithmetic will break.

For each used symbol, output:

- breaking change (with evidence: diff line or doc section, AND the fully resolved type)
- downstream data flow impact (where the value ends up in project code and why it's incompatible)
- exact migration
- deprecated APIs
- new relevant features

#### Auth config changes

Auth configuration is a common source of breaking changes across Metabase versions — pay special attention to it during cross-referencing. The changelog and docs fetched in Step 2 contain the specifics. Look for: type renames, `fetchRequestToken` signature changes, and new properties like `jwtProviderUri`.

#### Step 3 output example

Each breaking change entry should look like this:

```
### fetchRequestToken (BREAKING — signature change)
- **Current usage** (v0.54): `fetchRequestToken: (url) => fetch(url).then(r => r.json())`
  Signature: `(url: string) => Promise<any>`
- **Target type** (v0.58): `() => Promise<{jwt: string}>`
  Resolved from: `MetabaseFetchRequestTokenFn` → `() => Promise<{jwt: string}>`
- **What changed**: arity (1 arg → 0 args), return type (`any` → `{jwt: string}`)
- **Migration**: Remove the `url` parameter. Hardcode the auth endpoint URL in the callback body.
  Also consider replacing with `jwtProviderUri` if the endpoint URL is known.
- **Severity**: 🔴 Breaking — will cause runtime error if not migrated

### CollectionBrowser.onClick (BREAKING — downstream data flow)
- **Current usage**: `onClick: (item) => setSelectedId(item.id)`
  where `setSelectedId` is `useState<number | undefined>[1]`
- **Target type**: callback param `item.id` is `SdkCollectionId`
  Resolved: `SdkCollectionId` → `number | "personal" | "root" | "tenant" | SdkEntityId`
- **What changed**: `item.id` widened from `number` to a union including strings.
  The callback signature `(item) => void` is still compatible, but `item.id` now
  includes string values that don't fit the project's `useState<number>`.
- **Data flow**: `item.id` → `setSelectedId()` → `selectedId: number | undefined`
  The string variants ("personal", "root") would cause a type error at the setter.
- **Migration**: Widen state type to `useState<SdkCollectionId | undefined>`,
  or narrow with a runtime guard: `if (typeof item.id === 'number') setSelectedId(item.id)`
- **Severity**: 🔴 Breaking — type error in state setter

### questionHeight (NON-BREAKING — new optional prop)
- **Current usage**: not used
- **Target type** (v0.58): `number | undefined`
- **What changed**: new optional prop added to `StaticQuestion`
- **Migration**: none required
- **Severity**: 🟢 Info — available if needed
```

### Step 4: Apply changes

- Update package.json version (for the SDK package, or embed script version for EmbedJS)
- Update code usage per Step 3 — apply all migrations identified. In Claude Code, issue all Edit calls in a single message where possible.
- Update Metabase instance version in docker files if present (docker-compose.yml, Dockerfile, .env)
- Install dependencies using the detected package manager (do not delete lockfiles or node_modules — only run the install command)

### Step 5: Validate typecheck (batch fix)

**For SDK upgrades (TypeScript projects):**

1. **Run typecheck once** — run the project's typecheck command (e.g., `npm run typecheck`, `tsc --noEmit`, or the equivalent for the project's build tool).
2. **Analyze ALL errors at once** — read the full error output and categorize every SDK-related error by root cause (e.g., "removed prop", "changed type signature", "renamed export"). Errors that share a root cause get fixed together.
3. **Look up expected types** — for each distinct failing symbol, search `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` to understand the target type. Do all lookups before making any fixes — this prevents back-and-forth between reading and editing.
4. **Apply ALL fixes in one batch** — fix every error across all files before re-running typecheck. In Claude Code, issue all Edit calls in a single message where possible.
5. **Verify with one final typecheck run** — re-run the typecheck command. If new errors appear (e.g., a fix introduced a secondary issue), apply another batch and re-run. If errors remain after 3 batch rounds, mark Step 5 ❌ blocked and report which errors could not be resolved.

**For SDK upgrades (plain JavaScript projects):**

- No typechecker available. Instead, manually review each change from Step 4 against the target SDK's API:
  - Verify function signatures match (argument count, return types)
  - Verify prop names and values match the target version's expectations
  - Check for renamed imports or removed exports
- Mark Step 5 ✅ complete with a note that validation was manual (no TypeScript).

**For EmbedJS / Modular Embedding upgrades:**

- There are no npm types to typecheck. Instead:
  - If the project uses TypeScript, run the typecheck command to catch any general TS errors introduced by the migration.
  - If the project is plain JavaScript, skip typechecking. Instead, manually review that all changed embed configuration objects match the target version's documented options.
- Mark Step 5 ✅ complete with a note on which validation was performed.

### Step 6: Output summary

Organize into these sections:

**1. Breaking changes fixed** — list each breaking change with severity and what was done:
- 🔴 **Breaking** (would cause build/runtime errors): e.g., "Migrated `fetchRequestToken` from 1-arg to 0-arg signature"
- 🟡 **Deprecation** (works now, will break later): e.g., "`appearance` prop renamed to `theme` — updated"

**2. Deprecation warnings** — APIs that still work but are marked deprecated in the target version. Include the recommended replacement so the user can plan future changes.

**3. New features available** — relevant new APIs or options in the target version that the project could benefit from (e.g., `jwtProviderUri` replacing manual `fetchRequestToken`). Keep brief — just flag them, don't advocate.

**4. Instance requirements** — minimum Metabase instance version needed for the target SDK/EmbedJS version. If the project has docker-compose or similar files, note whether the instance version was also updated.

**5. Technical details** — path used (primary d.ts diff / hybrid / fallback docs), versions upgraded (from → to), package manager used.

## Retry policy

**URL fetches:**
- The `fetch-docs.sh` script handles 404 skipping automatically. If you need to fetch manually: 404 on a version-specific page means it doesn't exist for that version — skip silently.
- For other errors (5xx, timeout, network): retry once immediately. If still failing, mark that step ❌ blocked and stop.

**npm pack:**
- If `npm pack` fails for a version, the version likely doesn't exist on npm. Mark as ❌ blocked and inform the user.
