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

- Do not start Step 3 until Steps 1–2 are ✅ complete (Step 3 cross-references their outputs).
- Do not start Step 4 until Step 3 is ✅ complete (Step 4 applies the changes Step 3 identified).
- Do not start Step 5 until Step 4 is ✅ complete.
- Do not output Step 6 until Step 5 is ✅ complete (or explicitly ❌ blocked).

### Evidence requirements

- Step 1 evidence: list every matched file path, every import/reference (from `@metabase/embedding-sdk-react` for SDK, or embed script tags/init calls for EmbedJS), every used component/hook/type, every prop/config option used per component, and every dot-subcomponent used (e.g., `InteractiveQuestion.FilterBar`).
- Step 2 evidence (primary path): show the diff output between d.ts files. (fallback path): list each fetched URL + include raw extracted sections that contain prop tables / type definitions / migration sections. Do not summarize away details — Step 3 needs the full text to cross-reference.
- Step 3 evidence: for each used prop/config option, show the target type (from d.ts for SDK, or from docs for EmbedJS) AND the current usage from the project side-by-side. Example format: `fetchRequestToken: project uses (url: string) => Promise<any>, target type is () => Promise<{jwt: string}> → BREAKING (arity change)`.
- Step 4 evidence: show the exact diffs applied (or file edits described precisely).
- Step 5 evidence: show the exact command run (e.g., `npm run typecheck` or `tsc --noEmit`) and summarize errors if any remain.

## Important performance notes (keep under ~5 minutes)

- Maximize parallelism. Step 1 and Step 2 should run concurrently.
- Do not parse repo branches, commits, PRs, or issues.

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
  - Otherwise run: `npm view @metabase/embedding-sdk-react version` (Bash tool) and use that.

If package not present OR user is upgrading EmbedJS/Modular Embedding:

- Use AskUserQuestion for current Metabase instance version and current EmbedJS/Modular Embedding version.
- Mark Step 0 ❌ blocked until answered.

### Multi-version hops

When the upgrade spans a major structural boundary (e.g., v0.54 → v0.58 crosses the auth config change at v0.55 AND the doc layout change at v0.58), handle it as a single migration to the target version — do not do intermediate upgrades. However, during Step 3, check the auth config evolution section and account for every breaking change along the path. For example, v0.52 → v0.58 means the auth config changed shape (v0.55) AND gained `jwtProviderUri` (v0.58) — both changes need to be reflected in the migration.

## Pre-workflow steps

### Upgrade Plan Checklist (required before any other work)

Create a TODO list using the TaskCreate tool with these items. Mark each task as `in_progress` (via TaskUpdate) before starting it and `completed` when done:

- Step 1: Scan project usage
- Step 2: Extract d.ts diff or fallback to docs
- Step 3: Compile breaking changes + migrations
- Step 4: Apply code changes
- Step 5: Run typecheck and fix until clean
- Step 6: Final summary

### Parallel Plan (required)

State which steps will run in parallel and how. Specifically, identify:

- which steps will be issued as background sub-agents (`run_in_background: true`)
- which steps will run as local Bash/Grep/Read tool calls in the same message

### Path Selection

Determine which path to use:

- If upgrading `@metabase/embedding-sdk-react` → attempt **primary path** (d.ts diff), with fallback if d.ts unavailable (determined during Step 2)
- If upgrading EmbedJS/Modular Embedding → **fallback path** (skip d.ts extraction entirely)

## Workflow

### Step 1: Scan the project code (NO sub-agent — results must remain in the main context for Step 3 cross-referencing)

**For SDK upgrades (`@metabase/embedding-sdk-react`):**

- Use Grep to find all imports from `@metabase/embedding-sdk-react`.
- Then Read ALL matching files (in parallel in a single message).
- Extract:
  - imports, components, hooks, types, helpers
  - every prop used per component
  - every dot-subcomponent used
- Output a structured "Usage Inventory".

**For EmbedJS / Modular Embedding upgrades:**

- There is no npm package to scan. Instead, use Grep to search for:
  - Metabase embed `<script>` tags (e.g., patterns like `metabase.js`, `embed.js`, `embedding-sdk`, or the Metabase instance URL)
  - Any JS calls to Metabase embedding APIs (e.g., `MetabaseEmbed`, `Metabase.embed`, `window.MetabaseEmbed`, `initMetabase`, component init calls)
  - Configuration objects passed to embed init functions (auth config, appearance, theme, component options)
- Then Read ALL matching files (in parallel in a single message).
- Extract:
  - which components are embedded (dashboard, question, query builder, collection browser)
  - all configuration options / props passed to each component
  - authentication setup (JWT endpoint URL, auth config shape)
  - appearance / theme customizations
- Output a structured "Usage Inventory".

### Step 2: Extract d.ts diff (primary path)

**This step runs concurrently with Step 1.**

#### Step 2a: Extract d.ts files via npm pack

Use `node -e` to create a temp directory in the OS temp folder (works on macOS, Linux, and Windows):

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

Replace `{CURRENT}` and `{TARGET}` with the actual version numbers.

After both complete, check d.ts layout for each version:

```bash
[ -f "$SDK_TMPDIR/current/package/dist/index.d.ts" ] && ls -la "$SDK_TMPDIR/current/package/dist/index.d.ts"
[ -f "$SDK_TMPDIR/target/package/dist/index.d.ts" ] && ls -la "$SDK_TMPDIR/target/package/dist/index.d.ts"
```

- **If BOTH exist** → primary path confirmed. Start curling the upgrade path and continue to Step 2b.
- **If EITHER is missing** → switch to **Alternative Path B** (below). Output: "d.ts not available for version X.Y.Z, switching to fallback (docs fetch)."

#### Step 2b: Diff the d.ts files

Run:

```bash
diff -u "$SDK_TMPDIR/current/package/dist/index.d.ts" "$SDK_TMPDIR/target/package/dist/index.d.ts" || true
```

Save the diff output — this is the source of truth for all API changes.

### Alternative Path B: Fetch docs via curl (replaces Steps 2a–2b; use when d.ts is missing or upgrading EmbedJS/Modular Embedding)

If the primary path is not available (d.ts missing for either version, OR EmbedJS/Modular Embedding upgrade), use this path instead of Steps 2a–2b.

All doc fetching below happens via curl directly in the main context (not sub-agents, not WebFetch). This matters because:
- The changelog is too large for WebFetch — its internal model will summarize away breaking-change details you need.
- Doc pages contain `{% include_file %}` directives that WebFetch strips.
- Results need to stay in the main context for Step 3 cross-referencing.

Curl all URLs in parallel — do not wait for one to finish before starting the next.

### Changelog:

```bash
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" -o /tmp/sdk-changelog.md
```

Then use `Read` on `/tmp/sdk-changelog.md` to extract entries between {CURRENT} and {TARGET}.

**Component docs via curl + snippet expansion:**

**For SDK upgrades:**

```bash
DOC_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{TARGET}/embedding/sdk"

# Step 1: Fetch doc pages in parallel (adjust based on target version)
curl -sL "${DOC_BASE}/collections.md"    -o /tmp/sdk-doc-collections.md &
curl -sL "${DOC_BASE}/questions.md"      -o /tmp/sdk-doc-questions.md &
curl -sL "${DOC_BASE}/dashboards.md"     -o /tmp/sdk-doc-dashboards.md &
curl -sL "${DOC_BASE}/config.md"         -o /tmp/sdk-doc-config.md &
# For v0.52–v0.57 only (these files don't exist in v0.58+):
curl -sL "${DOC_BASE}/appearance.md"     -o /tmp/sdk-doc-appearance.md &
curl -sL "${DOC_BASE}/authentication.md" -o /tmp/sdk-doc-authentication.md &
wait

# Step 2: Extract snippet names from include_file directives (v0.54+ only — skip for v0.52–v0.53)
grep -h 'include_file.*api/snippets/.*\.md.*snippet="properties"' /tmp/sdk-doc-*.md 2>/dev/null \
  | sed 's/.*api\/snippets\/\([^"]*\)\.md.*/\1/' | sort -u > /tmp/sdk-snippet-names.txt

# Step 3: Fetch each Props/Options snippet in parallel (only if snippet names were found)
SNIP_BASE="${DOC_BASE}/api/snippets"
while IFS= read -r name; do
  curl -sL "${SNIP_BASE}/${name}.md" -o "/tmp/sdk-snippet-${name}.md" &
done < /tmp/sdk-snippet-names.txt
wait
```

Then use Read on all `/tmp/sdk-doc-*.md` and `/tmp/sdk-snippet-*.md` files.

For v0.54+: each doc page has sections headed `#### Props` or `#### Options`. For each such section, the `{% include_file "{{ dirname }}/api/snippets/{Name}.md" snippet="properties" %}` line indicates which snippet was fetched. The snippet file contains the full prop table between `<!-- [<snippet properties>] -->` and `<!-- [<endsnippet properties>] -->` markers — include this verbatim (no summarizing away props).

For v0.52–v0.53: there are no `api/snippets/` files. Props are documented inline in the markdown pages themselves (look for `## ... props` headings and the tables/lists that follow). Extract these directly from the doc pages.

**For EmbedJS / Modular Embedding upgrades:**

Pick ONE of the following based on target version — do not run both.

If target is **v0.56–v0.57** (single doc):

```bash
EMBED_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{TARGET}/embedding"
curl -sL "${EMBED_BASE}/embedded-analytics-js.md" -o /tmp/embedjs-doc-main.md
```

If target is **v0.58+** (split docs):

```bash
EMBED_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v0.{TARGET}/embedding"
curl -sL "${EMBED_BASE}/modular-embedding.md" -o /tmp/embedjs-doc-modular-embedding.md &
curl -sL "${EMBED_BASE}/components.md"        -o /tmp/embedjs-doc-components.md &
curl -sL "${EMBED_BASE}/appearance.md"        -o /tmp/embedjs-doc-appearance.md &
curl -sL "${EMBED_BASE}/authentication.md"    -o /tmp/embedjs-doc-authentication.md &
wait
```

Then use Read on all `/tmp/embedjs-doc-*.md` files.

Return full migration sections and notable warnings.

### Step 3: Summarize changes (ONLY after Steps 1–2 ✅)

Cross-reference:

- primary path
  - each used prop/subcomponent/type (from Step 1) vs d.ts diff
- fallback path
  - each used prop/subcomponent/type (from Step 1) vs target docs, changelog

#### Deep type resolution

For every prop identified in Step 1, resolve its type in the target d.ts **all the way down to the concrete signature**. Do not stop at type alias names — alias names can stay the same while the underlying type changes, which is a common source of missed breaking changes.

Specifically:
1. For each prop used in the project, grep the target d.ts for that prop name and note its type.
2. If the type is a **type alias** (e.g., `MetabaseFetchRequestTokenFn`, `SdkDashboardId`, `SdkCollectionId`), grep the target d.ts for that alias's definition and expand it to its concrete type (e.g., `() => Promise<{jwt: string}>`, `number | string`).
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

### Step 5: Validate typecheck (loop until clean)

**For SDK upgrades:**

- Run typecheck command
- If errors:
  - Read error output
  - Grep `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` for failing symbols
  - Apply fixes
  - Re-run
    Repeat until zero SDK-related errors. If errors remain after 5 fix attempts, mark Step 5 ❌ blocked and report which errors could not be resolved.

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

If any WebFetch fails:

- retry once immediately (same URL)
- if still failing, mark that step ❌ blocked and stop.

If the `npm pack` command fails for a specific version:

- This likely means the version doesn't exist on npm. Mark as ❌ blocked and inform the user.
