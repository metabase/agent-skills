---
name: metabase-full-app-to-modular-embedding-upgrade
description: Migrates a project from Metabase Full App / Interactive (iframe-based) embedding to Modular (web-component-based) embedding. Use when the user wants to replace Metabase iframes with Modular Embedding web components.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Execution contract

Follow the workflow steps in order — do not skip any step. Create the checklist first, then execute each step and explicitly mark it done with evidence. Each step's output feeds into the next, so skipping steps produces wrong migrations.

If you cannot complete a step due to missing info or tool failure:

1. record the step as ❌ blocked,
2. explain exactly what is missing / what failed,
3. stop (do not proceed to later steps).

### Required output structure

Your response should contain these sections in this order:

1. **Step 0 Results: Metabase Version Detection**
2. **Migration Plan Checklist**
3. **Step 1 Results: Project Scan**
4. **Step 2 Results: iframe Analysis & Web Component Mapping**
5. **Step 3: Migration Plan**
6. **Step 4: Applied Code Changes**
7. **Step 5: Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

Steps are sequential — do not start a step until the previous one is ✅ complete.

## Architectural conformance

Follow the app's existing architecture, template engine, layout/partial system, code style, and route patterns. Do not switch paradigms (e.g., templates to inline HTML or vice versa). If the app has middleware for shared template variables, prefer that over duplicating across route handlers.

## Important performance notes

- Maximize parallelism within each step. Use parallel Grep/Glob/Read calls in single messages wherever possible.
- Do not use sub-agents for project scanning — results need to stay in the main context for cross-referencing in later steps.
- Do not parse repo branches, commits, PRs, or issues.

## Scope

This skill converts Full App / Interactive Embedding (iframe-based) to Modular Embedding (web-component-based via `embed.js`).

**The consumer's app may be written in any backend language** (Node.js, Python, Ruby, PHP, Java, Go, .NET, etc.) with any template engine. Keep instructions language-agnostic unless a specific language is detected in Step 1.

### What this skill handles

- Replacing `<iframe>` elements pointing to Metabase with appropriate web components
- Adding the `embed.js` script tag (exactly once at app layout level)
- Adding `window.metabaseConfig` setup code (exactly once at app layout level)
- Modifying SSO/JWT endpoints to support modular embedding's JSON response format
- Mapping iframe URL customization parameters to theme config and component attributes

### Migration Plan Checklist

Create a TODO list using the TaskCreate tool with these items. Mark each task as `in_progress` (via TaskUpdate) before starting it and `completed` when done:

- Step 0: Detect Metabase version
- Step 1: Scan project
- Step 2: Analyze iframes and map to web components
- Step 3: Plan migration changes
- Step 4: Apply code changes
- Step 5: Validate changes
- Step 6: Final summary

## AskUserQuestion triggers

Use AskUserQuestion and halt until answered if:

- The Metabase instance URL cannot be determined from project code or environment variables
- An iframe URL pattern does not match any known content type (dashboard, question, collection, home)
- No SSO/JWT endpoint can be identified in the project
- No layout/head file can be identified (unclear where to inject embed.js)
- Multiple layout files exist and it is unclear which one(s) to use
- The backend language cannot be determined
- The Metabase instance version cannot be determined from the project code
- Multiple iframes specify different `locale` values (ask user which locale to set in `window.metabaseConfig`)

## Workflow

### Step 0: Detect Metabase version

Before anything else, determine the Metabase version. Grep the project for Docker image tags (`metabase/metabase:v`), `METABASE_VERSION`, or version references. If undetected, AskUserQuestion (options: `v53 or older`, `v54–v58`, `v59+`). Abort if < v53 (modular embedding not available). Record the version — it controls `jwtProviderUri` placement in later steps.

---

### Step 1: Scan the project (NO sub-agent)

Perform all of the following scans. Use parallel tool calls within a single message wherever there are no dependencies.

#### 1a: Identify backend language and framework

- Check for dependency/build files (`package.json`, `requirements.txt`, `Gemfile`, `pom.xml`, `go.mod`, `composer.json`, etc.).
- Identify the template engine and record the language and framework.

#### 1b: Find ALL Metabase iframes

Use Grep to search for all of these patterns (in parallel):

- `<iframe` in all template/HTML/JSX/view files
- `iframe` in all server-side code files (JS/TS/Python/Ruby/Go/Java/PHP) — catches iframes built via string concatenation or template literals
- `auth/sso` adjacent to `iframe` or `src` attributes

For each file with a match, read the entire file.

#### 1c: Find SSO/JWT authentication code

Use Grep to search for all of these patterns (in parallel):

- `/auth/sso`
- `/sso/metabase` or similar SSO route patterns
- `jwt.sign` or `jwt.encode` or `JWT` or `jsonwebtoken` or `PyJWT` or `jose`
- `JWT_SHARED_SECRET` or `METABASE_JWT_SHARED_SECRET`
- `return_to` (Metabase SSO redirect parameter)
- `redirect` near `auth/sso` (catches the SSO redirect logic)

For each matching file, read the entire file.

#### 1d: Find the layout/head file(s)

Find the single file (or common code path) where the HTML `<head>` section is defined — this is where `embed.js` and `window.metabaseConfig` will be injected.

Search for:

- `<head>` or `<!DOCTYPE` or `<html` in template/view files
- Layout/wrapper patterns: `include('head')`, `<%- include`, `{% extends`, `{% block`, `layout`, `base.html`, `_layout`, `application.html`
- If the app builds HTML via inline strings in server code (e.g., `res.send(...)`), identify where the `<head>` content is generated

#### 1e: Find Metabase configuration

Grep for `METABASE_` and `MB_SITE_URL` prefixed variables. Record every Metabase-related variable name and where it is read.

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

---

### Step 2: Analyze iframes and map to web components (ONLY after Step 1 ✅)

For EACH iframe found in Step 1:

#### 2a: Parse the iframe URL

Extract from the iframe `src` attribute (which may be a template expression, variable, or literal):

- **Metabase base URL**: may come from env var, constant, or be hardcoded
- **Content path**: the path after the base URL, e.g., `/dashboard/1`, `/question/entity/abc123`, `/collection/5`
- **Content type**: `dashboard`, `question`, `collection`, or `home` (if path is `/`)
- **Entity ID or numeric ID**: the identifier in the path.
  - An ID may be 
    - a numeric id, i.e. 123
    - a numeric id + slug, i.e. 123-slug, in this case you should drop off slug
    - an entity id
      - also there may be a case with url like `/question/entity/{entity_id}`
- **URL hash/query parameters** used for UI customization (e.g., `#logo=false&top_nav=false`)
- **SSO wrapping**: whether the iframe goes through an SSO endpoint first (e.g., `/sso/metabase?return_to=...`)

#### 2b: Map content type to web component

| Full App iframe path pattern | Modular Web Component | Required Attribute |
|---|---|---|
| `/dashboard/{id}` or `/dashboard/entity/{eid}` | `<metabase-dashboard>` | `dashboard-id="{id or eid}"` |
| `/question/{id}` or `/question/entity/{eid}` | `<metabase-question>` | `question-id="{id or eid}"` |
| `/model/{id}` or `/model/entity/{eid}` | `<metabase-question>` | `question-id="{id or eid}"` |
| `/collection/{id}` or `/collection/entity/{eid}` | `<metabase-browser>` | `initial-collection="{id or eid}"` |
| `/` (Metabase home / root) | `<metabase-browser>` | `initial-collection="root"` |

If the iframe path is built dynamically from a variable, the web component attribute should use the same variable/expression.

If an iframe path does not match any known pattern → AskUserQuestion.

#### 2c: Map URL customization parameters

**Parameters to DROP** (not applicable — modular web components do not include Metabase application chrome):

| Full App Parameter | Why it is dropped |
|---|---|
| `top_nav` | Web components have no Metabase top navigation bar |
| `side_nav` | Web components have no Metabase sidebar |
| `logo` | Web components have no Metabase logo |
| `search` | Web components have no Metabase search bar |
| `new_button` | No `+ New` button (use `with-new-question` / `with-new-dashboard` on `<metabase-browser>` if applicable) |
| `breadcrumbs` | Web components have no Metabase breadcrumbs |

**Parameters that map to web component ATTRIBUTES:**

| Full App Parameter | Modular Equivalent |
|---|---|
| `header=false` | `with-title="false"` on the component |
| `action_buttons=false` | `drills="false"` on the component |

**Parameters that map to `window.metabaseConfig`:**

| Full App Parameter | metabaseConfig Property |
|---|---|
| `locale={code}` | `locale: "{code}"` |

**Locale migration rules:**
- If ONE locale value is found across all iframes → add `locale: "{code}"` to `window.metabaseConfig` automatically
- If MULTIPLE DIFFERENT locale values are found across iframes → AskUserQuestion to let the user decide which single locale to set in `window.metabaseConfig` (modular embedding supports only one global locale)

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

---

### Step 3: Plan migration changes (ONLY after Step 2 ✅)

Create a complete file-by-file change plan covering all areas below. Every change should be specified with the target file, the old code, and the new code.

#### 3a: embed.js script injection — exactly once per app

- **Target**: the layout/head file identified in Step 1d
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
- **Code to add** (minimum required config):
  ```html
  <script>
    window.metabaseConfig = {
      instanceUrl: "{METABASE_SITE_URL}",
      jwtProviderUri: "{SSO_ENDPOINT_URL}",
    };
  </script>
  ```
- **Locale**: If a `locale` parameter was found on any iframe in Step 2c, add `locale: "{code}"` to the config object. If multiple iframes had different locale values, the user will have already been asked which one to use (per AskUserQuestion trigger).
- Both `instanceUrl` and `jwtProviderUri` should be rendered dynamically using the project's template expression syntax.
- **`jwtProviderUri`** must be a **full absolute URL** including protocol and host (e.g., `http://localhost:9090/sso/metabase`). Relative paths do not work because the browser needs the full origin to send the auth request. Pass the app's origin as a template variable (e.g., via middleware) and render: `jwtProviderUri: "{APP_URL}/sso/metabase"`.
  - **Version-dependent behavior** (use the version detected in Step 0):
    - **v59+**: Include `jwtProviderUri` in `window.metabaseConfig` (preferred approach).
    - **v53–v58**: Do not include `jwtProviderUri` in `window.metabaseConfig` — it is not supported on these versions. The JWT Identity Provider URI must be configured in Metabase admin settings instead (see Step 3g).
- `window.metabaseConfig` should be set exactly once — if it appears in per-iframe code instead of the layout, each component will re-initialize the SDK.

#### 3c: SSO endpoint modification

The existing SSO endpoint currently redirects the browser to Metabase's `/auth/sso?jwt={token}&return_to={path}`.

For modular embedding, the embed.js SDK sends a fetch request to the JWT Identity Provider URI and expects a JSON response. The endpoint should be converted to return JSON only — do not keep a fallback to the old redirect-based auth flow.

This is a full migration, not a gradual one. The old iframe-based embedding is being completely replaced, so the redirect behavior is no longer needed.

Refer to the Metabase authentication documentation for the expected endpoint behavior: https://www.metabase.com/docs/latest/embedding/authentication

**Constraints:**
- Do not modify the JWT signing logic — only change how the response is delivered
- Remove the old redirect behavior entirely — the endpoint should only return JSON
- The JSON response body should be exactly `{ "jwt": "<token>" }` — no other fields, because the SDK parses this exact shape
- Remove any code that builds the redirect URL (e.g., `new URL("/auth/sso", ...)`, `searchParams.set("return_to", ...)`) as it is now dead code

#### 3d: iframe replacement plan

For EACH iframe from Step 2d's Migration Mapping Table:

- Specify: file path, exact old code to replace, exact new code
- The new web component should preserve any dynamic ID expressions from the original iframe URL
- If the iframe had explicit `width`/`height` attributes, wrap the web component in a `<div>` with equivalent CSS dimensions (web components expand to fill their container)
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

#### 3g: Metabase admin configuration notes (manual steps for the user)

List these as part of the plan — they will be included in the final summary:

1. **Enable modular embedding**: Admin > Embedding > toggle "Enable modular embedding"
2. **Configure CORS origins**: Admin > Embedding > Modular embedding > add the host app's domain (e.g., `http://localhost:9090`)
3. **Configure JWT Identity Provider URI** (use the version detected in Step 0):
   - **v53–v58 (required)**: Admin > Authentication > JWT > set to the full URL of the SSO endpoint (e.g., `http://localhost:9090/sso/metabase`). This is the only way to configure JWT auth on these versions since `jwtProviderUri` in config is not supported.
   - **v59+ (optional if `jwtProviderUri` is set in `window.metabaseConfig`)**: Admin > Authentication > JWT > set to the full URL of the SSO endpoint. If `jwtProviderUri` was added to `window.metabaseConfig` in Step 3b, this admin setting is not strictly required but can serve as a backup.
4. **JWT shared secret**: No change needed — reuse the existing shared secret from Full App embedding setup

---

### Step 4: Apply code changes (ONLY after Step 3 ✅)

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

---

### Step 5: Validate changes (ONLY after Step 4 ✅)

Perform all of these checks. Each check should have an explicit pass/fail result.

#### 5a: No remaining Metabase iframes

Use Grep to search for `<iframe` and `iframe` across all project files (excluding `node_modules`, `.git`, lockfiles).
Verify that NO iframes pointing to Metabase URLs remain.
Non-Metabase iframes (if any) should be untouched.

**Pass criteria**: zero Metabase-related iframes found.

#### 5b: embed.js appears exactly once

Use Grep to search for `embed.js` across all project files (excluding `node_modules`, `.git`).
**Pass criteria**: exactly ONE occurrence in the layout/head file.

#### 5c: window.metabaseConfig is set exactly once

Use Grep to search for `window.metabaseConfig` across all project files (excluding `node_modules`, `.git`).
**Pass criteria**: exactly ONE occurrence (the assignment in the layout/head file).

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

If ANY check fails:
- Fix the issue immediately
- Re-run the specific check
- If unable to fix after 3 attempts, mark Step 5 ❌ blocked and report which check failed and why

---

### Step 6: Output summary

Organize the final output into these sections:

1. **Changes applied**: list every file modified and a one-line description of each change
2. **Web component mapping**: table showing each old iframe → new web component
3. **Dropped parameters**: list of Full App iframe parameters that were dropped, with brief explanation of why they don't apply to modular embedding
4. **Theme configuration**: any theme/appearance settings mapped into `window.metabaseConfig`
5. **Manual steps required** (Metabase admin configuration from Step 3g):
   - Enable modular embedding
   - Configure CORS origins
   - Configure JWT Identity Provider URI
   - Any other admin steps identified
6. **Behavioral differences the user should be aware of**:
   - Users can no longer navigate between dashboards/questions/collections within a single embed (each web component is standalone)
   - The Metabase application shell (nav, sidebar, search) is no longer present
   - Any iframe parameters that could not be mapped
