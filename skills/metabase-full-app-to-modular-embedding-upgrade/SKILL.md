---
name: metabase-full-app-to-modular-embedding-upgrade
description: Migrates a project from Metabase Full App / Interactive (iframe-based) embedding to Modular (web-component-based) embedding. Use when the user wants to replace Metabase iframes with Modular embedding web components.
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

1. **Step 0: Metabase Version Detection**
2. **Step 0.1: Migration Plan Checklist**
3. **Step 1: Project Scan**
4. **Step 2: iframe Analysis & Web Component Mapping**
5. **Step 3: Migration Plan**
6. **Step 4: Applied Code Changes**
7. **Step 5: Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

Steps are sequential — do not start a step until the previous one is ✅ complete.

### Evidence requirements

- Step 0: Metabase version detected (source: Docker tag, env var, or user answer).
- Step 1: every matched file path, every iframe location, SSO endpoint, layout/head file, Metabase config variables.
- Step 2: per iframe — parsed URL, content type, ID, hash params, mapped web component with attributes.
- Step 3: the complete file-by-file change plan with exact old/new code.
- Step 4: per file — what was changed and exact diffs applied.
- Step 5: each validation check's pass/fail result with evidence.

## Architectural conformance

Follow the app's existing architecture, template engine, layout/partial system, code style, and route patterns. Do not switch paradigms (e.g., templates to inline HTML or vice versa). If the app has middleware for shared template variables, prefer that over duplicating across route handlers.

## Performance

- Maximize parallelism within each step. Use parallel Grep/Glob/Read calls in a single message wherever possible.
- Do not use sub-agents for project scanning — results need to stay in the main context for cross-referencing in later steps.
- Do not parse repo branches, commits, PRs, or issues.

## Scope

This skill converts Full App / Interactive embedding (iframe-based) to Modular embedding (web-component-based via `embed.js`).

**The consumer's app may be written in any backend language** (Node.js, Python, Ruby, PHP, Java, Go, .NET, etc.) with any template engine. Keep instructions language-agnostic unless a specific language is detected in Step 1.

### What this skill handles

- Replacing `<iframe>` elements pointing to Metabase with appropriate web components (e.g. `<metabase-question>`, `<metabase-dashboard>`)
- Adding the `embed.js` script tag (exactly once at app layout level)
- Adding `window.metabaseConfig` setup code (exactly once at app layout level)
- Modifying SSO/JWT endpoints to support modular embedding's JSON response format
- Mapping iframe URL customization parameters to theme config and component attributes

### What this skill does not handle

- Migrating from Static (signed/guest) embedding

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com`
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com`
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com`
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## AskUserQuestion triggers

Use AskUserQuestion and halt until answered if:

- The Metabase instance URL cannot be determined from project code or environment variables
- Always ask for the Metabase instance version — do not rely solely on code detection
- An iframe URL pattern does not match any known resource type (dashboard, question, collection, home)
- No SSO/JWT endpoint can be identified in the project
- No layout/head file can be identified (unclear where to inject embed.js)
- Multiple layout files exist and it is unclear which one(s) to use
- The backend language cannot be determined
- Multiple iframes specify different `locale` values (ask user which locale to set in `window.metabaseConfig`)

## Pre-workflow steps

### Migration Plan Checklist

Create a checklist to track progress. In Claude Code, use TaskCreate/TaskUpdate tools:

- Step 0: Detect Metabase version
- Step 1: Scan project + fetch target version docs
- Step 2: Analyze iframes and map to web components (using docs)
- Step 3: Plan migration changes
- Step 4: Apply code changes
- Step 5: Validate changes
- Step 6: Final summary

## Workflow

### Step 0: Detect Metabase instance version

Always AskUserQuestion for the Metabase instance version — even if a version appears in Docker tags or env vars, confirm it with the user. Abort if v52 or older (modular embedding was introduced in v53).

Then fetch the embedding docs for the confirmed version:

```bash
bash <skill-path>/scripts/fetch-docs.sh {INSTANCE_VERSION}
```

Before anything else, determine the Metabase version. Grep the project for Docker image tags (`metabase/metabase:v`, `metabase/metabase-enterprise:v`), `METABASE_VERSION`, or version references. If undetected, AskUserQuestion (options: `v52 or older`, `v53`, `v54–v58`, `v59+`). Abort if v52 or older (modular embedding not available — it was introduced in v53). Record the version — it controls `jwtProviderUri` placement in later steps.

### Step 1: Scan the project + fetch docs no sub-agent)

Perform the project scan and doc fetch concurrently — they are independent. Use parallel tool calls within a single message wherever there are no dependencies.

#### 1a: Fetch target version docs

Use `scripts/fetch-docs.sh` to fetch the embedding documentation for the target Metabase version:

```bash
bash <skill-path>/scripts/fetch-docs.sh {TARGET_VERSION}
```

The script discovers all available doc pages for that version via the GitHub Contents API — no hardcoded page lists. After it completes, read all fetched files from `/tmp/embedjs-docs/`.

These docs are the authoritative source for web component attributes, `window.metabaseConfig` options, and SSO endpoint behavior for the target version. Use them in Step 2 for mapping instead of relying on hardcoded tables alone.

Launch this concurrently with the project scan steps below.

#### 1b: Identify backend language and framework

- Check for dependency/build files (`package.json`, `requirements.txt`, `Gemfile`, `pom.xml`, `go.mod`, `composer.json`, etc.).
- Identify the template engine and record the language and framework.

#### 1c: Find ALL Metabase iframes

Use Grep to search for all of these patterns (in parallel):

- `<iframe` in all template/HTML/JSX/view files
- `iframe` in all server-side code files (JS/TS/Python/Ruby/Go/Java/PHP) — catches iframes built via string concatenation or template literals
- `auth/sso` adjacent to `iframe` or `src` attributes. Note: the SSO URL may be constructed in a separate variable or function and passed to the iframe `src` — if the iframe `src` is a variable, trace its definition to check for `auth/sso`.

For each file with a match, read the entire file.

#### 1d: Find SSO/JWT authentication code

Use Grep to search for all of these patterns (in parallel):

- `/auth/sso`
- `/sso/metabase` or similar SSO route patterns
- `jwt.sign` or `jwt.encode` or `JWT` or `jsonwebtoken` or `PyJWT` or `jose`
- `JWT_SHARED_SECRET` or `METABASE_JWT_SHARED_SECRET`
- `return_to` (Metabase SSO redirect parameter)
- `redirect` near `auth/sso` (catches the SSO redirect logic)

For each matching file, read the entire file.

#### 1e: Find the layout/head file(s)

Find the single file (or common code path) where the HTML `<head>` section is defined — this is where `embed.js` and `window.metabaseConfig` will be injected.

Search for:

- `<head>` or `<!DOCTYPE` or `<html` in template/view files
- Layout/wrapper patterns: `include('head')`, `<%- include`, `{% extends`, `{% block`, `layout`, `base.html`, `_layout`, `application.html`
- If the app builds HTML via inline strings in server code (e.g., `res.send(...)`), identify where the `<head>` content is generated

#### 1f: Find Metabase configuration

Grep for `METABASE_` and `MB_` prefixed variables. Record every Metabase-related variable name and where it is read.

#### Output: Structured Project Inventory

Compile all findings into:

```
Backend: {language}, {framework}, {template engine}
Metabase config:
  - Site URL variable: {name} (read at {file}:{line})
  - Dashboard path variable: {name} (read at {file}:{line})
  - JWT secret variable: {name} (read at {file}:{line})
  - Other variables: ...
Layout/head file: {path}:{line range} (or "inline HTML in {file}:{line range}")
Iframes found: {count}
  - {file}:{line} — {brief description}
  - ...
SSO endpoint: {file}:{line} — {route} ({method})
```

### Step 2: Analyze iframes and map to web components (only after Step 1 ✅)

Use the documentation fetched in Step 1a as the authoritative reference for web component attributes, `window.metabaseConfig` options, and SSO endpoint behavior. The hardcoded tables below are fallbacks — if the docs describe additional attributes or different behavior for the target version, prefer the docs.

For each iframe found in Step 1:

#### 2a: Parse the iframe URL

Extract from the iframe `src` attribute (which may be a template expression, variable, or literal):

- **Metabase base URL**: may come from env var, constant, or be hardcoded
- **Resource path**: the path after the base URL, e.g., `/dashboard/1`, `/question/entity/abc123`, `/collection/5`
- **Resource type**: `dashboard`, `question`, `collection`, or `home` (if path is `/`)
- **Entity ID or numeric ID**: the resource identifier in the path.
  - An ID may be:
    - a numeric id, e.g. 123
    - a numeric id + slug, e.g. 123-slug. You need to remove the slug completely; including the slug will prevent the resource from loading.
    - an entity id — URLs with pattern `/{resource_type}/entity/{entity_id}` use entity IDs
- **URL hash/query parameters** used for UI customization (e.g., `#logo=false&top_nav=false`)
- **SSO wrapping**: whether the iframe goes through an SSO endpoint first (e.g., `/sso/metabase?return_to=...`)

#### 2b: Map content type to web component

| Full App iframe path pattern | Modular Web Component | Required Attribute |
|---|---|---|
| `/dashboard/{id}` or `/dashboard/entity/{entity_id}` | `<metabase-dashboard>` | `dashboard-id="{id or entity_id}"` |
| `/question/{id}` or `/question/entity/{entity_id}` | `<metabase-question>` | `question-id="{id or entity_id}"` |
| `/model/{id}` or `/model/entity/{entity_id}` | `<metabase-question>` | `question-id="{id or entity_id}"` |
| `/collection/{id}` or `/collection/entity/{entity_id}` | `<metabase-browser>` | `initial-collection="{id or entity_id}"` |
| `/` (Metabase home / root) | `<metabase-browser>` | `initial-collection="root"` |

If the iframe path is built dynamically from a variable, the web component attribute should use the same variable/expression.

If an iframe path does not match any known pattern → AskUserQuestion.

#### 2c: Map URL customization parameters

**Parameters to drop** (not applicable — modular web components do not include Metabase application chrome):

| Full App Parameter | Why it is dropped |
|---|---|
| `top_nav` | Web components have no Metabase top navigation bar |
| `side_nav` | Web components have no Metabase sidebar |
| `logo` | Web components have no Metabase or whitelabel logo |
| `search` | Web components have no Metabase search bar |
| `new_button` | No `+ New` button (use `with-new-question` / `with-new-dashboard` on `<metabase-browser>` if applicable) |
| `breadcrumbs` | Web components have no Metabase breadcrumbs |

**Parameters that map to web component attributes:**

| Full App Parameter | Modular Equivalent |
|---|---|
| `header=false` | `with-title="false"` on the component |
| `action_buttons=false` | `drills="false"` on the component |

**Parameters that map to `window.metabaseConfig`:**

| Full App Parameter | metabaseConfig Property |
|---|---|
| `locale={code}` | `locale: "{code}"` |

**Locale migration rules:**
- If one locale value is found across all iframes → add `locale: "{code}"` to `window.metabaseConfig` automatically
- If multiple different locale values are found across iframes → AskUserQuestion to let the user decide which single locale to set in `window.metabaseConfig` (modular embedding supports only one global locale)

#### 2d: Output Migration Mapping Table

For each iframe, output:

```
iframe #{n}: {file}:{line}
  Old: {full iframe HTML or code}
  Content type: {dashboard|question|collection|home}
  ID: {static value or variable expression}
  Dropped params: {list}
  Mapped attributes: {list}
  New: {exact replacement web component HTML}
```

### Step 3: Plan migration changes (only after Step 2 ✅)

Create a complete file-by-file change plan covering all areas below. Every change should be specified with the target file, the old code, and the new code.

#### 3a: embed.js script injection — exactly once per app

- **Target**: the layout/head file identified in Step 1e
- **Location**: inside `<head>` (or as close as possible to other `<script>` tags)
- **Code to add**:
  ```html
  <script defer src="{METABASE_SITE_URL}/app/embed.js"></script>
  ```
- `{METABASE_SITE_URL}` should be rendered dynamically using the project's existing template expression syntax.
- If the Metabase URL variable is only available in specific routes, pass it to the layout via middleware or template context.
- Verify this will appear exactly once in the rendered HTML regardless of which page the user visits — if it loads twice, the SDK reinitializes and breaks auth state.

#### 3b: metabaseConfig — exactly once per app

Modular embedding reads its configuration from `window.metabaseConfig`. There is no `defineMetabaseConfig()` function — assign the config object directly.

- **Target**: same layout/head file as 3a
- **Location**: before the embed.js script tag (the config must be set before embed.js loads, otherwise the SDK has no config to read)
- **Code to add** (minimum — add auth fields only if the fetched docs list them for this version):
  ```html
  <script>
    window.metabaseConfig = {
      instanceUrl: "{METABASE_SITE_URL}",
      // Add auth fields here only if supported by the confirmed version's docs
    };
  </script>
  ```
- **Locale**: If a `locale` parameter was found on any iframe in Step 2c, add `locale: "{code}"` to the config object. If multiple iframes had different locale values, the user will have already been asked which one to use (per AskUserQuestion trigger).
- `instanceUrl` (and `jwtProviderUri` if supported) should be rendered dynamically using the project's template expression syntax.
- **Auth config fields**: Consult the docs fetched in Step 0 to determine which fields `window.metabaseConfig` supports for the confirmed version. For example, `jwtProviderUri` may or may not be available. If the docs list it, include it as a **full absolute URL** (e.g., `http://localhost:9090/sso/metabase`) — relative paths don't work. If the docs don't list it, the JWT Identity Provider URI must be configured in Metabase admin settings instead (see Step 3f).
- `window.metabaseConfig` should be set exactly once — if it appears in per-iframe code instead of the layout, each component will re-initialize the SDK.

#### 3c: SSO endpoint modification

The existing SSO endpoint currently redirects the browser to Metabase's `/auth/sso?jwt={token}&return_to={path}`.

For modular embedding, the embed.js SDK sends a fetch request to the JWT Identity Provider URI and expects a JSON response. The endpoint should be converted to return JSON only — do not keep a fallback to the old redirect-based auth flow.

This is a full migration, not a gradual one. The old iframe-based embedding is being completely replaced, so the redirect behavior is no longer needed.

Consult the auth docs fetched in Step 0 for the expected SSO endpoint response format for the confirmed version.

**Constraints:**
- Do not modify the JWT signing logic — only change how the response is delivered
- Remove the old redirect behavior entirely — the endpoint should only return JSON
- The JSON response body should be exactly `{ "jwt": "<token>" }` — no other fields, because the SDK parses this exact shape
- Remove any code that builds the redirect URL (e.g., `new URL("/auth/sso", ...)`, `searchParams.set("return_to", ...)`) as it is now dead code

#### 3d: iframe replacement plan

For each iframe from Step 2d's Migration Mapping Table:

- Specify: file path, exact old code to replace, exact new code
- The new web component should preserve any dynamic ID expressions from the original iframe URL
- If the iframe had explicit `width`/`height` attributes or inline `style`, apply them directly to the web component element (e.g., `<metabase-dashboard dashboard-id="1" style="width:800px;height:600px">`) — do not wrap in a `<div>`
- If the iframe was styled via CSS classes, apply those classes directly to the web component
- If the iframe was inside a container element with styles, keep that container
- Remove any server-side SSO URL construction that was used only for the iframe src (e.g., building `/sso/metabase?return_to=...`). But do not remove the SSO endpoint itself — it is still needed for modular embedding auth.
- If the iframe src was built via a server-side route handler that sends inline HTML (e.g., Express `res.send('<iframe ...')`), replace the iframe HTML within that handler's response string

#### 3e: Dead code removal

After replacing iframes and converting the SSO endpoint, identify and remove:

- Variables that built the iframe `src` URL (e.g., `iframeUrl`, `mbUrl`) if they are no longer used anywhere
- URL parameter/modifier strings that were appended to iframe URLs (e.g., `mods = "logo=false"`) if they are no longer referenced anywhere (check the SSO endpoint — if the redirect logic was removed, these strings may now be dead code too)
- Redirect-related code removed from the SSO endpoint (e.g., URL construction for `/auth/sso`, `return_to` parameter handling) — this is already handled as part of Step 3c
- Helper functions that constructed Metabase iframe URLs if they are no longer called
- Do not remove: the SSO endpoint itself, JWT signing function, environment variable reads, or any code that is used by other parts of the application

#### 3f: Metabase admin configuration notes (manual steps for the user)

List these as part of the plan — they will be included in the final summary:

1. **Enable modular embedding**: Admin > Embedding > toggle "Enable modular embedding"
2. **Configure CORS origins**: Admin > Embedding > Modular embedding > add the host app's domain (e.g., `http://localhost:9090`)
3. **Configure JWT Identity Provider URI**: Admin > Authentication > JWT > set to the full URL of the SSO endpoint (e.g., `http://localhost:9090/sso/metabase`). Check the fetched docs to determine whether this is required or optional for the confirmed version (it depends on whether `window.metabaseConfig` supports a JWT provider field).
4. **JWT shared secret**: No change needed — reuse the existing shared secret from Full App embedding setup

### Step 4: Apply code changes (only after Step 3 ✅)

Apply all changes from Step 3 in this order (backend changes first to minimize the window where things are broken):

1. **First**: Modify the SSO endpoint to return JSON (Step 3c) — this is backend-only
2. **Second**: Add `window.metabaseConfig` assignment and embed.js script tag to the layout/head file (Step 3b + 3a, config before embed.js)
3. **Third**: Replace each iframe with its web component (Step 3d), one file at a time
4. **Fourth**: Remove dead code (Step 3e)

**Constraints:**

- Use the Edit tool with precise `old_string` / `new_string` for every change
- Do not add new package dependencies — modular embedding requires only the embed.js script served by the Metabase instance
- Do not change environment variable names
- If a file requires multiple edits, apply them top-to-bottom to avoid offset issues

### Step 5: Validate changes (only after Step 4 ✅)

Perform all of these checks. Checks 5a–5c can run in parallel (all are independent grep searches). Check 5d and 5e require reading specific files. Each check should have an explicit pass/fail result.

#### 5a: No remaining Metabase iframes

Use Grep to search for `<iframe` and `iframe` across all project files (excluding `node_modules`, `.git`, lockfiles).
Verify that no Full App / Interactive Embedding iframes pointing to Metabase remain.
Non-Metabase iframes should be untouched. Also leave any guest embedding (formerly "static embedding") or public embedding iframes untouched — those use different URL patterns (e.g., `/embed/` or `/public/`) and are not part of this migration.

**Pass criteria**: zero Full App / Interactive Embedding iframes found (guest/public embed iframes are excluded).

#### 5b: embed.js appears exactly once

Use Grep to search for `/app/embed.js` across all project files (excluding `node_modules`, `.git`). This pattern is specific to Metabase's embed script URL and avoids false positives from other tools that may use a generic `embed.js` filename.
**Pass criteria**: exactly one occurrence in the layout/head file.

#### 5c: window.metabaseConfig is set exactly once

Use Grep to search for `window.metabaseConfig` across all project files (excluding `node_modules`, `.git`).
**Pass criteria**: exactly one occurrence (the assignment in the layout/head file).

#### 5d: SSO endpoint returns JSON only

Read the SSO endpoint file. Verify:
- The endpoint returns a JSON response with `{ jwt: token }`
- The old redirect logic (`res.redirect`, `new URL("/auth/sso", ...)`, `return_to`) has been fully removed
- No conditional check for `response=json` exists (since JSON is the only response format now)

**Pass criteria**: endpoint returns JSON only, no redirect fallback remains.

#### 5e: Spot-check modified files

Read each modified file and verify:
- Web components have required attributes (`dashboard-id`, `question-id`, or `initial-collection`)
- Template syntax is valid (no unclosed tags, correct expressions)
- Dead-code variables identified in Step 3e have been removed

**Pass criteria**: all checks pass.

If any check fails:
- Fix the issue immediately
- Re-run the specific check
- If unable to fix after 3 attempts, mark Step 5 ❌ blocked and report which check failed and why

### Step 6: Output summary

Organize the final output into these sections:

1. **Changes applied**: list every file modified and a one-line description of each change
2. **Web component mapping**: table showing each old iframe → new web component
3. **Dropped parameters**: list of Full App iframe parameters that were dropped, with brief explanation of why they don't apply to modular embedding
4. **Theme configuration**: any theme/appearance settings mapped into `window.metabaseConfig`
5. **Manual steps required** (Metabase admin configuration from Step 3f):
   - Enable modular embedding
   - Configure CORS origins
   - Configure JWT Identity Provider URI
   - Any other admin steps identified
6. **Behavioral differences the user should be aware of**:
   - Users can no longer navigate between dashboards/questions/collections within a single embed (each web component is standalone)
   - The Metabase application shell (nav, sidebar, search) is no longer present
   - Any iframe parameters that could not be mapped

## Retry policy

- If any validation check in Step 5 fails after 3 fix attempts, mark Step 5 ❌ blocked and report which check failed and why.
- If AskUserQuestion is not answered, remain blocked on that step — do not guess or proceed with assumptions.
