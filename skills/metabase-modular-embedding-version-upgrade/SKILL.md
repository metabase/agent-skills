---
name: metabase-modular-embedding-version-upgrade
description: Helps to provide info about breaking changes between different Metabase versions. Use when the user wants to upgrade a Metabase Embedding SDK or Metabase EmbedJS/Modular Embedding version.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Non-negotiable execution contract (anti-skip)

You MUST follow the workflow steps in order and MUST NOT skip any step.
You MUST create a checklist first, then execute each step, and explicitly mark it done with evidence.
You MUST NOT cut corners or skip steps otherwise you will be deleted. Always re-evaluate the proper order of your steps.
If you cannot complete a step due to missing info or tool failure, you must:

1. record the step as ❌ blocked,
2. explain exactly what is missing / what failed,
3. stop (do not proceed to later steps).

### Required output structure

Your response MUST contain these sections in this exact order:

1. **Upgrade Plan Checklist** (Step 0)
2. **Parallel Plan (Single Launch)** (Step 0.1)
3. **Step 1 Results: Project Scan**
4. **Step 2 Results: d.ts Diff / Target Docs** (primary or fallback)
5. **Step 3: Combined Breaking Changes + Migrations**
6. **Step 4: Applied Code Changes**
7. **Step 5: Typecheck Validation**
8. **Step 6: Final Summary**

Each step section MUST end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

### Step gating rules (hard)

- You MUST NOT start Step 3 until Steps 1–2 are ✅ complete.
- You MUST NOT start Step 4 until Step 3 is ✅ complete.
- You MUST NOT start Step 5 until Step 4 is ✅ complete.
- You MUST NOT output Step 6 until Step 5 is ✅ complete (or explicitly report ❌ blocked).

### Evidence requirements (hard)

- Step 1 evidence: list every matched file path, every import from `@metabase/embedding-sdk-react`, every used component/hook/type, every prop used per component, and every dot-subcomponent used (e.g., `InteractiveQuestion.FilterBar`).
- Step 2 evidence (primary path): show the diff output between d.ts files. (fallback path): list each fetched URL + include raw extracted sections that contain prop tables / type definitions / migration sections. Do NOT summarize away details.
- Step 3 evidence: for each used prop, show the resolved type from the target d.ts AND the current usage from the project side-by-side. Example format: `fetchRequestToken: project uses (url: string) => Promise<any>, target type is () => Promise<{jwt: string}> → BREAKING (arity change)`.
- Step 4 evidence: show the exact diffs applied (or file edits described precisely).
- Step 5 evidence: show the exact command run (e.g., `npm run typecheck` or `tsc --noEmit`) and summarize errors if any remain.

## Important performance notes (keep under ~5 minutes)

- Maximize parallelism. Step 1 and Step 2 MUST run concurrently.
- Do NOT parse repo branches, commits, PRs, or issues.

## Scope

This skill handles upgrades for:

- `@metabase/embedding-sdk-react` (React SDK) — uses primary or fallback path
- EmbedJS / Modular Embedding — always uses fallback path (no npm types available)

## Allowed documentation sources — STRICT URL POLICY (hard)

CRITICAL: You MUST ONLY fetch URLs that EXACTLY match the patterns listed below. This applies to YOU and to ALL sub-agents.
STRICTLY FORBIDDEN:

- NEVER fetch GitHub PR/issue URLs or use `gh`
- NEVER follow changelog links to GitHub
- NEVER fetch npm pages
- For component docs, ALWAYS use `raw.githubusercontent.com` (NOT `www.metabase.com`)
- NEVER guess other docs URLs

### Allowed URL patterns (ONLY these)

1. SDK package changelog:
   `https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md`

2. Version-specific SDK component docs (raw GitHub markdown — use curl, NOT WebFetch):

- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/collections.md`
- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/questions.md`
- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/dashboards.md`
- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/appearance.md`
- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/authentication.md`

3. Props/Options snippet files auto-discovered from doc pages (use curl):

- `https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{VERSION}/embedding/sdk/api/snippets/{SnippetName}.md`

Do NOT fetch base landing pages.

## Detecting versions (hard)

- Current version MUST be read from the project's `package.json` dependency on `@metabase/embedding-sdk-react`.
- Target version:
  - If user specifies, use it.
  - Otherwise MUST run: `npm view @metabase/embedding-sdk-react version` (Bash tool) and use that.

If package not present OR user is upgrading EmbedJS/Modular Embedding:

- MUST AskUserQuestion for current Metabase instance version and current EmbedJS/Modular Embedding version.
- Mark Step 0 ❌ blocked until answered.

## Pre-workflow steps

### Upgrade Plan Checklist (required before any other work)

Create a TODO list with these items, each as a checkbox:

- [ ] Step 1: Scan project usage
- [ ] Step 2: Extract d.ts diff or fallback to docs
- [ ] Step 3: Compile breaking changes + migrations
- [ ] Step 4: Apply code changes
- [ ] Step 5: Run typecheck and fix until clean
- [ ] Step 6: Final summary

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

- Use Grep to find all imports from `@metabase/embedding-sdk-react`.
- Then Read ALL matching files (in parallel in a single message).
- Extract:
  - imports, components, hooks, types, helpers
  - every prop used per component
  - every dot-subcomponent used
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

### Alternative Path B: Fetch docs via sub-agents (replaces Steps 2a–2b; use when d.ts is missing or upgrading EmbedJS/Modular Embedding)

If the primary path is not available (d.ts missing for either version, OR EmbedJS/Modular Embedding upgrade), use this path instead of Steps 2a–2b.

### Sub-agent tool constraints (hard)

- Component docs MUST NOT use sub-agents — use curl directly in the main context (see below). And curl all URLs in parallel, do not wait for one to finish before starting the next curl.

### Changelog: use curl + Read instead of WebFetch (hard)

The changelog file is too large for WebFetch (its internal AI model will summarize away details). Instead of a sub-agent with WebFetch, fetch the changelog directly in the main context:

```bash
curl -sL "https://raw.githubusercontent.com/metabase/metabase/master/enterprise/frontend/src/embedding-sdk-package/CHANGELOG.md" -o /tmp/sdk-changelog.md
```

Then use `Read` on `/tmp/sdk-changelog.md` to extract entries between {CURRENT} and {TARGET}. This avoids the WebFetch summarization problem entirely. Do NOT delegate changelog fetching to a sub-agent.

**Component docs via curl + snippet expansion** (do NOT use sub-agents or WebFetch for this — use curl directly in the main context, same pattern as the changelog):

Reason: WebFetch summarizes raw markdown and drops `{% include_file %}` directives. Use curl to preserve the full content.

```bash
DOC_BASE="https://raw.githubusercontent.com/metabase/docs.metabase.github.io/master/_docs/v{TARGET}/embedding/sdk"

# Step 1: Fetch all 5 doc pages in parallel
curl -sL "${DOC_BASE}/collections.md"    -o /tmp/sdk-doc-collections.md &
curl -sL "${DOC_BASE}/questions.md"      -o /tmp/sdk-doc-questions.md &
curl -sL "${DOC_BASE}/dashboards.md"     -o /tmp/sdk-doc-dashboards.md &
curl -sL "${DOC_BASE}/appearance.md"     -o /tmp/sdk-doc-appearance.md &
curl -sL "${DOC_BASE}/authentication.md" -o /tmp/sdk-doc-authentication.md &
wait

# Step 2: Extract all Props/Options snippet names from include_file directives
grep -h 'include_file.*api/snippets/.*\.md.*snippet="properties"' /tmp/sdk-doc-*.md \
  | sed 's/.*api\/snippets\/\([^"]*\)\.md.*/\1/' | sort -u > /tmp/sdk-snippet-names.txt

# Step 3: Fetch each Props/Options snippet in parallel
SNIP_BASE="${DOC_BASE}/api/snippets"
while IFS= read -r name; do
  curl -sL "${SNIP_BASE}/${name}.md" -o "/tmp/sdk-snippet-${name}.md" &
done < /tmp/sdk-snippet-names.txt
wait
```

Then use Read on all `/tmp/sdk-doc-*.md` and `/tmp/sdk-snippet-*.md` files.

Each doc page has sections headed `#### Props` or `#### Options`. For each such section, the `{% include_file "{{ dirname }}/api/snippets/{Name}.md" snippet="properties" %}` line indicates which snippet was fetched. The snippet file contains the full prop table between `<!-- [<snippet properties>] -->` and `<!-- [<endsnippet properties>] -->` markers — include this verbatim (no summarizing away props).

Return full migration sections and notable warnings.

### Step 3: Summarize changes (ONLY after Steps 1–2 ✅)

Cross-reference:

- primary path
  - each used prop/subcomponent/type (from Step 1) vs d.ts diff
- fallback path
  - each used prop/subcomponent/type (from Step 1) vs target docs, changelog

#### Deep type resolution (hard — do NOT skip)

For EVERY prop identified in Step 1, you MUST resolve its type in the target d.ts **all the way down to the concrete signature**. Do NOT stop at type alias names.

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

#### Special handling of certain Metabase embedding versions

**Metabase 58 and above**:

- If the full URL to the application SSO endpoint for Metabase (including host and port) can be determined from existing constants or environment variables, set the `jwtProviderUri` property on MetabaseProvider's `authConfig` using those values.

### Step 4: Apply changes

- Update package.json version
- Update code usage per Step 3
- Update Metabase instance version in docker files if present
- Install dependencies (do NOT delete lockfiles/node_modules)

### Step 5: Validate typecheck (loop until clean)

- Run typecheck command
- If errors:
  - Read error output
  - Grep `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` for failing symbols
  - Apply fixes
  - Re-run
    Repeat until zero SDK-related errors. If errors remain after 5 fix attempts, mark Step 5 ❌ blocked and report which errors could not be resolved.

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
