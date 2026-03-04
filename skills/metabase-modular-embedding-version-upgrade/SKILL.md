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

- Step 1 evidence: list every matched file path, every import/reference (from `@metabase/embedding-sdk-react` for SDK, or embed script tags/init calls for EmbedJS), every used component/hook/type, every prop/config option used per component, and every dot-subcomponent used (e.g., `InteractiveQuestion.FilterBar`).
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

Only fetch URLs that exactly match the patterns listed below. This applies to you and to all sub-agents. Other sources (GitHub PRs/issues, npm pages, metabase.com) contain rendered HTML or unstructured data that produces unreliable results.

Do not:
- Fetch GitHub PR/issue URLs or use `gh`
- Follow changelog links to GitHub
- Fetch npm pages
- Guess docs URLs not listed below

For component docs, always use `raw.githubusercontent.com` (not `www.metabase.com`) — the raw files preserve `include_file` directives needed for snippet expansion.

### Allowed URL patterns

All versioned docs URLs use the `v0.XX` format (e.g., `v0.58`), not `vXX`.

1. **SDK package changelog:**
   `https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md`

2. **Embedding SDK doc pages (v0.52+):**
   - All versions (v0.52+):
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/collections.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/questions.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/dashboards.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/config.md`
   - v0.52–v0.57 only (removed in v0.58):
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/appearance.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/authentication.md`

3. **EmbedJS / Modular Embedding doc pages:**
   - v0.56–v0.57:
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/embedded-analytics-js.md`
   - v0.58+:
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/modular-embedding.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/components.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/appearance.md`
     - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/authentication.md`

4. **Props/Options snippet files** (v0.54+ only — v0.52–v0.53 have props inline in doc pages, no snippets directory):
   - `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VERSION}/embedding/sdk/api/snippets/{SnippetName}.md`

Do not fetch base landing pages.

## Detecting versions

- Current version: read from the project's `package.json` dependency on `@metabase/embedding-sdk-react`.
- Target version:
  - If user specifies, use it.
  - Otherwise run `npm view @metabase/embedding-sdk-react version` in the terminal to get the latest.

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

**For SDK upgrades** — npm pack both versions + changelog:

```bash
SDK_TMPDIR=$(node -e "
  const path = require('path');
  const fs = require('fs');
  const dir = path.join(require('os').tmpdir(), 'sdk-diff-' + Date.now());
  fs.mkdirSync(dir, { recursive: true });
  console.log(dir);
")

mkdir -p "$SDK_TMPDIR/current" "$SDK_TMPDIR/target"

(cd "$SDK_TMPDIR/current" && npm pack @metabase/embedding-sdk-react@{CURRENT} --quiet 2>/dev/null && tar xzf *.tgz)
(cd "$SDK_TMPDIR/target"  && npm pack @metabase/embedding-sdk-react@{TARGET}  --quiet 2>/dev/null && tar xzf *.tgz)

echo "SDK_TMPDIR=$SDK_TMPDIR"
```

Also always fetch the changelog — it's one file but gives valuable migration instructions that type diffs alone don't provide:

```bash
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" -o /tmp/sdk-changelog.md
```

After npm pack completes, check d.ts availability for **each** version independently:

```bash
[ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ] && echo "current: has d.ts" || echo "current: no d.ts"
[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ] && echo "target: has d.ts" || echo "target: no d.ts"
```

Record which versions have d.ts — this determines Phase 2's strategy.

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

Only fetch docs for the components the project actually uses (from Step 1's Usage Inventory). This avoids loading docs for unused components.

Fetch via `curl` directly (not through a web-fetching AI tool that may summarize content) — the doc pages contain `{% include_file %}` directives that get stripped by HTML-to-markdown converters, and results need to stay in the main context for Step 3. In Claude Code, use the Bash tool with curl.

Use the output prefix `current` or `target` to keep files separate. Fetch all needed URLs in parallel.

**For SDK versions — map components to doc pages:**

| Used component (from Step 1) | Doc page to fetch |
|---|---|
| `MetabaseDashboard`, dashboard-related hooks | `dashboards.md` |
| `InteractiveQuestion`, `StaticQuestion`, question-related hooks | `questions.md` |
| `CollectionBrowser` | `collections.md` |
| Auth config (`MetabaseProvider`, `fetchRequestToken`, etc.) | `authentication.md` (v0.52–v0.57) or `config.md` (v0.52+) |
| Appearance/theme props | `appearance.md` (v0.52–v0.57) or `config.md` (v0.52+) |

Always fetch `config.md` (it covers auth + appearance for v0.58+). Only fetch the component-specific pages that Step 1 found usage for.

```bash
# Replace {VER} with the version number and {PREFIX} with "current" or "target"
DOC_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VER}/embedding/sdk"

# Always fetch config:
curl -sL "${DOC_BASE}/config.md" -o /tmp/sdk-doc-{PREFIX}-config.md &

# Only fetch pages for components found in Step 1:
# (include/exclude based on Usage Inventory)
curl -sL "${DOC_BASE}/dashboards.md"     -o /tmp/sdk-doc-{PREFIX}-dashboards.md &   # if dashboards used
curl -sL "${DOC_BASE}/questions.md"      -o /tmp/sdk-doc-{PREFIX}-questions.md &     # if questions used
curl -sL "${DOC_BASE}/collections.md"    -o /tmp/sdk-doc-{PREFIX}-collections.md &   # if collections used
# v0.52–v0.57 only:
curl -sL "${DOC_BASE}/appearance.md"     -o /tmp/sdk-doc-{PREFIX}-appearance.md &    # if theme/appearance used
curl -sL "${DOC_BASE}/authentication.md" -o /tmp/sdk-doc-{PREFIX}-authentication.md & # if auth config used
wait

# v0.54+ only — extract and fetch snippet files for the pages you fetched:
grep -h 'include_file.*api/snippets/.*\.md.*snippet="properties"' /tmp/sdk-doc-{PREFIX}-*.md 2>/dev/null \
  | sed 's/.*api\/snippets\/\([^"]*\)\.md.*/\1/' | sort -u > /tmp/sdk-snippet-{PREFIX}-names.txt

SNIP_BASE="${DOC_BASE}/api/snippets"
while IFS= read -r name; do
  curl -sL "${SNIP_BASE}/${name}.md" -o "/tmp/sdk-snippet-{PREFIX}-${name}.md" &
done < /tmp/sdk-snippet-{PREFIX}-names.txt
wait
```

Then read all fetched `/tmp/sdk-doc-{PREFIX}-*.md` and `/tmp/sdk-snippet-{PREFIX}-*.md` files.

For v0.54+: each doc page has sections headed `#### Props` or `#### Options`. The `{% include_file %}` line indicates which snippet was fetched. The snippet file contains the full prop table between `<!-- [<snippet properties>] -->` and `<!-- [<endsnippet properties>] -->` markers — include this verbatim (no summarizing away props).

For v0.52–v0.53: there are no `api/snippets/` files. Props are documented inline in the markdown pages themselves (look for `## ... props` headings and the tables/lists that follow). Extract these directly.

**For EmbedJS / Modular Embedding versions — map components to doc pages:**

| Used component (from Step 1) | v0.56–v0.57 doc | v0.58+ doc |
|---|---|---|
| Any embed component | `embedded-analytics-js.md` (single file) | `components.md` |
| Auth/JWT config | (same file) | `authentication.md` |
| Appearance/theme | (same file) | `appearance.md` |

For v0.56–v0.57 there's only one doc page, so always fetch it. For v0.58+, fetch only the relevant pages + always fetch `modular-embedding.md` (overview).

```bash
# Replace {VER} and {PREFIX} as above
EMBED_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{VER}/embedding"

# v0.56–v0.57: single file
curl -sL "${EMBED_BASE}/embedded-analytics-js.md" -o /tmp/embedjs-doc-{PREFIX}-main.md

# v0.58+: targeted
curl -sL "${EMBED_BASE}/modular-embedding.md" -o /tmp/embedjs-doc-{PREFIX}-modular-embedding.md &
curl -sL "${EMBED_BASE}/components.md"        -o /tmp/embedjs-doc-{PREFIX}-components.md &   # if any components used
curl -sL "${EMBED_BASE}/appearance.md"        -o /tmp/embedjs-doc-{PREFIX}-appearance.md &   # if theme/appearance used
curl -sL "${EMBED_BASE}/authentication.md"    -o /tmp/embedjs-doc-{PREFIX}-authentication.md & # if auth used
wait
```

Then read all fetched `/tmp/embedjs-doc-{PREFIX}-*.md` files.

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

Specifically:
1. For each prop used in the project, search the target d.ts for that prop name and note its type.
2. If the type is a **type alias** (e.g., `MetabaseFetchRequestTokenFn`, `SdkDashboardId`, `SdkCollectionId`), search the target d.ts for that alias's definition and expand it to its concrete type (e.g., `() => Promise<{jwt: string}>`, `number | string`).
3. Compare the **fully resolved concrete type** against the project's current usage (argument counts, argument types, return types, value types).
4. A prop can have the same name but a completely different type signature — this is a breaking change. Renaming is not the only kind of breaking change.

Example of what this catches: `fetchRequestToken` kept its name but changed from `(url: string) => Promise<any>` to `() => Promise<{jwt: string}>` — different arity, different return type.

For each used symbol, output:

- breaking change (with evidence: diff line or doc section, AND the fully resolved type)
- exact migration
- deprecated APIs
- new relevant features

#### Version-specific auth config changes

**v0.52–v0.54**: Auth config uses `MetabaseAuthConfigWithProvider` shape. The `fetchRequestToken` prop signature is `(url: string) => Promise<any>`.

**v0.55–v0.57**: Auth config types renamed to `MetabaseAuthConfigWithJwt` and `MetabaseAuthConfigWithSaml`. The `fetchRequestToken` signature changed to `() => Promise<{jwt: string}>` — this is a **breaking change** (different arity AND different return type). Code using `(url) => fetch(url)...` must be migrated to `() => fetch(YOUR_AUTH_ENDPOINT)...`.

**v0.58+**: Added `jwtProviderUri` property on `MetabaseProvider`'s `authConfig`. If the full URL to the application SSO endpoint for Metabase (including host and port) can be determined from existing constants or environment variables, set `jwtProviderUri` using those values — this replaces the need for a manual `fetchRequestToken` function.

### Step 4: Apply changes

- Update package.json version
- Update code usage per Step 3
- Update Metabase instance version in docker files if present
- Install dependencies (do not delete lockfiles or node_modules — only run the install command)

### Step 5: Validate typecheck (batch fix)

**For SDK upgrades:**

1. **Run typecheck once** — run the project's typecheck command (e.g., `npm run typecheck` or `tsc --noEmit`).
2. **Analyze ALL errors at once** — read the full error output and categorize every SDK-related error by root cause (e.g., "removed prop", "changed type signature", "renamed export"). Errors that share a root cause get fixed together.
3. **Look up expected types** — for each distinct failing symbol, search `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` to understand the target type. Do all lookups before making any fixes — this prevents back-and-forth between reading and editing.
4. **Apply ALL fixes in one batch** — fix every error across all files before re-running typecheck. In Claude Code, issue all Edit calls in a single message where possible.
5. **Verify with one final typecheck run** — re-run the typecheck command. If new errors appear (e.g., a fix introduced a secondary issue), apply another batch and re-run. If errors remain after 3 batch rounds, mark Step 5 ❌ blocked and report which errors could not be resolved.

**For EmbedJS / Modular Embedding upgrades:**

- There are no npm types to typecheck. Instead:
  - If the project uses TypeScript, run the typecheck command to catch any general TS errors introduced by the migration.
  - If the project is plain JavaScript, skip typechecking. Instead, manually review that all changed embed configuration objects match the target version's documented options.
- Mark Step 5 ✅ complete with a note on which validation was performed.

### Step 6: Output summary

Organize into:

1. Breaking changes fixed
2. Deprecations
3. Notes (notable architecture changes, instance version requirement)
4. Path used (primary d.ts diff / fallback docs)

## Retry policy

If any URL fetch or curl fails:

- retry once immediately (same URL)
- if still failing, mark that step ❌ blocked and stop.

If the `npm pack` command fails for a specific version:

- This likely means the version doesn't exist on npm. Mark as ❌ blocked and inform the user.
