---
name: metabase-modular-embedding-version-upgrade
description: Upgrades a project's Metabase modular embedding SDK (@metabase/embedding-sdk-react) or EmbedJS/Modular embedding version. Use when the user wants to upgrade their Metabase modular embedding integration to a newer version.
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
2. **Pipeline Plan** (Step 0.1)
3. **Step 1 Results: Project Scan**
4. **Step 2 Results: d.ts Diff / Target Docs** (primary or fallback)
5. **Step 3: Change Catalog**
6. **Step 4: Per-File Migration** (one subsection per file)
7. **Step 5: Typecheck Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

### Step gating rules

- Step 1 and Step 2 Phase 1 run concurrently (independent).
- Step 2 Phase 2 starts after BOTH Step 1 and Step 2 Phase 1 complete.
- Step 3 starts after Steps 1–2 are ✅ complete (builds catalog from Step 2 data + Step 1 inventory).
- Step 4 starts after Step 3 is ✅ complete. **Per-file migration tasks run in parallel** — each file's analysis + fix is independent.
- Step 5 starts after ALL Step 4 file tasks are ✅ complete.
- Step 6 after Step 5 is ✅ complete (or explicitly ❌ blocked).

### Evidence requirements

- Step 1: list every matched file path, every import/reference, every used component/hook/type, every prop/config option per component, every dot-subcomponent (e.g., `InteractiveQuestion.FilterBar`), and for callback props — where the callback parameter data flows in the project (e.g., `onClick: (item) => setSelectedId(item.id)` where `setSelectedId` is `useState<number>`).
- Step 2 (primary path): show the diff output between d.ts files. (fallback path): list each fetched URL + include raw extracted sections. Do not summarize away details.
- Step 3: the structured change catalog — every changed/removed/added symbol with its fully resolved concrete type.
- Step 4: per file — which catalog entries affect this file, data flow analysis for callbacks, exact diffs applied.
- Step 5: the exact command run and error summary if any remain.

## Performance

The workflow is designed as a pipeline that maximizes parallelism:

```
Step 1 (scan) ──────────┐
                         ├──► Step 2 Phase 2 (fetch) ──► Step 3 (catalog) ──► Step 4 per-file:
Step 2 Phase 1 (probe) ──┘                                                    ├── FileA: analyze + fix
                                                                              ├── FileB: analyze + fix
                                                                              └── FileC: analyze + fix
                                                                                    │
                                                                              Step 5 (typecheck) ──► Step 6
```

- **Steps 1 + 2 Phase 1**: concurrent (independent network + file operations).
- **Step 2 Phase 2**: after both complete.
- **Step 3**: fast — just organizes Step 2 data into a structured catalog. No per-file work.
- **Step 4**: the main parallelization point — each project file is analyzed and fixed independently.
- **Step 5**: sequential (needs all files done).

In Claude Code, use parallel tool calls or `run_in_background: true` for sub-agents. For Step 4, issue all file edits in a single message or spawn per-file sub-agents.

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

- Ask the user for the current and target Metabase instance versions. EmbedJS/Modular Embedding is served from the Metabase instance, so its version matches the instance version. In Claude Code, use the AskUserQuestion tool for this.
- Mark Step 0 ❌ blocked until answered.

### Multi-version hops

When the upgrade spans a major structural boundary (e.g., v0.54 → v0.58 crosses the auth config change at v0.55 AND the doc layout change at v0.58), handle it as a single migration to the target version — do not do intermediate upgrades. However, during Step 3, check the auth config evolution section and account for every breaking change along the path. For example, v0.52 → v0.58 means the auth config changed shape (v0.55) AND gained `jwtProviderUri` (v0.58) — both changes need to be reflected in the migration.

## Pre-workflow steps

### Upgrade Plan Checklist (required before any other work)

Create a checklist to track progress. In Claude Code, use TaskCreate/TaskUpdate tools:

- Step 1: Scan project usage
- Step 2: Extract d.ts diff or fetch docs
- Step 3: Build change catalog
- Step 4: Per-file migrate (one sub-task per file)
- Step 5: Typecheck and fix
- Step 6: Final summary

### Pipeline Plan (required)

State the execution plan:

- **Concurrent**: Step 1 (project scan) + Step 2 Phase 1 (npm pack + changelog)
- **After both**: Step 2 Phase 2 (fetch docs)
- **Sequential**: Step 3 (build catalog from Step 2 data)
- **Parallel**: Step 4 — list each file and note they'll be processed concurrently
- **Sequential**: Steps 5 → 6

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

Step 2 has two phases. Phase 1 runs concurrently with Step 1. Phase 2 runs after Step 1 and Step 2 Phase 1 complete.

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

### Step 3: Build change catalog (after Steps 1–2 are ✅ complete)

This step is fast — it organizes Step 2 data into a structured catalog of ALL API changes between versions. No per-file project analysis here.

From the d.ts diff, docs comparison, and changelog, extract every change into a catalog:

- **Removed** exports/props/types
- **Renamed** symbols (old name → new name)
- **Type-changed** props — resolve every type alias to its **concrete type**. Do not stop at alias names — aliases can stay the same while the underlying type changes. For example, `SdkCollectionId` may have been `number` in the current version but `number | "personal" | "root" | "tenant" | SdkEntityId` in the target.
- **Signature-changed** functions/callbacks (arity, argument types, return types)
- **Added** props/exports (optional, for informational output)
- **Deprecated** APIs (with recommended replacements)
- **Auth config changes** — pay special attention. The changelog and docs contain the specifics. Look for: type renames, `fetchRequestToken` signature changes, and new properties like `jwtProviderUri`.

#### Catalog format

```
## Change Catalog (v0.54 → v0.58)

### fetchRequestToken
- Change: signature changed
- Old: `(url: string) => Promise<any>`
- New: `() => Promise<{jwt: string}>` (resolved from `MetabaseFetchRequestTokenFn`)
- Severity: 🔴 Breaking

### SdkCollectionId (type widening)
- Change: type widened
- Old: `number`
- New: `number | "personal" | "root" | "tenant" | SdkEntityId`
- Affects: any prop/callback param typed as `SdkCollectionId`, including `item.id` in CollectionBrowser callbacks
- Severity: 🔴 Breaking for code storing in `number`-typed variables

### SdkDashboardId (type widening)
- Change: type widened
- Old: `number`
- New: `number | string | SdkEntityId`
- Affects: any prop/callback param typed as `SdkDashboardId`
- Severity: 🔴 Breaking for code storing in `number`-typed variables

### jwtProviderUri
- Change: new property added to `MetabaseProvider` authConfig
- Severity: 🟢 Info — can replace manual `fetchRequestToken`

### questionHeight
- Change: new optional prop on `StaticQuestion`
- Severity: 🟢 Info
```

The catalog is the input for Step 4. It must include fully resolved concrete types — Step 4 sub-agents need them to assess compatibility without re-reading the d.ts.

### Step 4: Per-file migrate (parallel)

Each project file is analyzed and fixed independently against the change catalog. This is the main parallelization point.

**Before per-file work:** update package.json version and install dependencies. Also update Metabase instance version in docker files if present (docker-compose.yml, Dockerfile, .env). These are done once, not per-file.

**Per-file task** (run in parallel for each file from the Usage Inventory):

For each file, a single pass that combines analysis + fix:

1. **Match catalog entries** — which changes from the catalog affect this file's usage?
2. **Deep analysis** — for each affected prop:
   - Compare the file's current usage against the catalog's target type
   - For callback props: trace where callback parameter fields flow in THIS file (state setters, variables, API calls, route params). Check if the receiving type is compatible with the target's potentially widened type. For example, if `onClick: (item) => setSelectedId(item.id)` and the catalog says `item.id` widened from `number` to `SdkCollectionId`, and `setSelectedId` is `useState<number>`, flag it as breaking.
3. **Apply fixes** — edit the file to migrate all breaking changes identified above.
4. **Report** — output what was found and changed for this file.

**Parallelization strategy** — choose based on the number of files in the Usage Inventory:

- **< 15 files**: process all files in a single agent. Analyze each file against the catalog sequentially, then issue all Edit calls in one message. Sub-agent overhead is not worth it for small projects.
- **15+ files**: split files evenly among 3–4 sub-agents. Each sub-agent receives its batch of file paths, their Usage Inventory entries, and the full change catalog. In Claude Code, launch them with `run_in_background: true`.

#### Per-file output example

```
## src/components/CollectionPage.tsx

### Catalog matches:
- SdkCollectionId type widening → affects `onClick` callback
- (no other catalog entries match this file)

### Analysis:
- `onClick: (item) => setSelectedId(item.id)`
  - `item.id` is now `SdkCollectionId` (number | "personal" | "root" | "tenant" | SdkEntityId)
  - `setSelectedId` is `useState<number | undefined>[1]`
  - 🔴 BREAKING: string variants won't fit `number` state

### Fix applied:
- Widened state: `useState<number | undefined>` → `useState<SdkCollectionId | undefined>`
- Added import: `import type { SdkCollectionId } from '@metabase/embedding-sdk-react'`

Status: ✅ complete
```

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
