---
name: metabase-static-embedding-to-modular-guest-embedding-upgrade
description: Migrates a project from Metabase Static embedding to Modular guest embedding (web components via embed.js). Use when the user wants to migrate/convert/switch/upgrade from static embedding to modular embedding, from signed embed iframes to web components, or replace /embed/ iframes with metabase-dashboard/metabase-question components.
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

1. **Step 0 Results: Metabase Version Detection**
2. **Migration Plan Checklist**
3. **Step 1 Results: Project Scan + Docs Fetch**
4. **Step 2 Results: Static Embed Analysis & Web Component Mapping**
5. **Step 3: Migration Plan**
6. **Step 4: Applied Code Changes**
7. **Step 5: Validation**
8. **Step 6: Final Summary**

Each step section should end with a status line:

- `Status: ✅ complete` or `Status: ❌ blocked`

Steps are sequential — do not start a step until the previous one is ✅ complete.

### Evidence requirements

- Step 0: Metabase version detected (source: Docker tag, env var, or user answer).
- Step 1: every matched file path, every static embed location, JWT signing code, layout/head file, Metabase config variables, fetched docs listing.
- Step 2: per embed — parsed iframe URL, content type, token variable, hash params, mapped web component with attributes.
- Step 3: the complete file-by-file change plan with exact old/new code.
- Step 4: per file — what was changed and exact diffs applied.
- Step 5: each validation check's pass/fail result with evidence.

## Architectural conformance

Follow the app's existing architecture, template engine, layout/partial system, code style, and route patterns. Do not switch paradigms (e.g., templates to inline HTML or vice versa). If the app has middleware for shared template variables, prefer that over duplicating across route handlers.

The web component must be rendered using the **same delivery mechanism** as the static iframe it replaces. If the iframe was rendered by a server-side template (EJS, Jinja, ERB, Blade, etc.), the web component should be rendered by the same template. If the iframe was returned as inline HTML from a route handler (e.g., `res.send('<iframe ...')`), the web component should be returned the same way. If the iframe was in a static HTML file, the web component goes in that same file. Do not move rendering from one layer to another — the migration should be a drop-in replacement at the same point in the rendering pipeline.

**Token delivery must also stay server-side.** If the original static embedding generated the JWT on the server and rendered it directly into the HTML (e.g., `res.send(\`<iframe src=".../${token}">\`)`), then the migrated web component must receive its token the same way — rendered server-side into the `token` attribute (e.g., `<metabase-dashboard token="${token}">`). Do NOT introduce a client-side `fetch()` call to a new `/api/token` endpoint to deliver the token — `embed.js` may intercept such requests and return HTML instead of JSON, causing `SyntaxError: Unexpected token '<'` errors. Keep the token generation and delivery in the same server-side route handler where the page is rendered.

## Performance

- Maximize parallelism within each step. Use parallel Grep/Glob/Read calls in single messages wherever possible.
- Do not use sub-agents for project scanning — results need to stay in the main context for cross-referencing in later steps.
- Do not parse repo branches, commits, PRs, or issues.

## Scope

This skill converts Static (signed/guest) iframe embedding to Modular guest embedding (web-component-based via `embed.js`). Both approaches use the same authentication model — signed JWTs with `METABASE_SECRET_KEY` — so the backend signing logic is preserved. The migration changes how the signed content is delivered: from iframes with JWT-in-URL to web components with a `token` attribute.

**The consumer's app may be written in any backend language** (Node.js, Python, Ruby, PHP, Java, Go, .NET, etc.) with any template engine. Keep instructions language-agnostic unless a specific language is detected in Step 1.

### What this skill handles

- Replacing signed `<iframe>` elements (`/embed/dashboard/{JWT}`, `/embed/question/{JWT}`) with web components (`<metabase-dashboard token="...">`, `<metabase-question token="...">`)
- Adding the `embed.js` script tag (exactly once at app layout level)
- Adding `window.metabaseConfig` with `isGuest: true` (exactly once at app layout level)
- Mapping iframe hash parameters (`#titled=true`, `#bordered=true`) to web component attributes
- Preserving the existing JWT signing logic — the backend still signs tokens with `METABASE_SECRET_KEY` using the same `{resource, params}` payload
- Converting how the signed token reaches the frontend (from iframe URL path to template variable passed as `token` attribute)
- Mapping locked `params` in the JWT to `initial-parameters` attribute where applicable
- Removing `iframeResizer.js` references if present

### What this skill does not handle

- Migrating to SSO-based modular embedding (with user accounts) — this skill targets guest embedding only

### How guest modular embedding differs from static iframe embedding

The auth model is the **same** — both use `METABASE_SECRET_KEY` to sign JWTs with `{resource, params, exp}`. What changes is how the embed is rendered:

| Aspect | Static (iframe) | Modular guest (web component) |
|---|---|---|
| **Element** | `<iframe src="/embed/dashboard/{JWT}#params">` | `<metabase-dashboard token="{JWT}">` |
| **Token delivery** | Baked into iframe URL path | Passed as `token` attribute |
| **Config** | None (iframe is self-contained) | `window.metabaseConfig = { isGuest: true, instanceUrl: "..." }` |
| **Script** | Optional `iframeResizer.js` | Required `embed.js` |
| **Appearance** | Hash params (`#titled=true`) | Component attributes (`with-title="true"`) |
| **Locked params** | In JWT `params` field | Same JWT `params` field (unchanged) |
| **Editable params** | Not supported | `initial-parameters` attribute on component |
| **Downloads** | Not available | `with-downloads="true"` attribute (Pro/Enterprise) |
| **Secret key** | `METABASE_SECRET_KEY` | Same `METABASE_SECRET_KEY` |

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com`
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## AskUserQuestion triggers

Use AskUserQuestion and halt until answered if:

- The Metabase instance URL cannot be determined from project code or environment variables
- The backend language cannot be determined
- The Metabase instance version cannot be determined from the project code
- No layout/head file can be identified (unclear where to inject embed.js)
- Multiple layout files exist and it is unclear which one(s) to use

## Pre-workflow steps

### Migration Plan Checklist

Create a checklist to track progress. In Claude Code, use TaskCreate/TaskUpdate tools:

- Step 0: Detect Metabase version
- Step 1: Scan project + fetch target version docs
- Step 2: Analyze static embeds and map to web components (using docs)
- Step 3: Plan migration changes
- Step 4: Apply code changes
- Step 5: Validate changes
- Step 6: Final summary

## Workflow

### Step 0: Detect Metabase version

Before anything else, determine the Metabase version. Grep the project for Docker image tags (`metabase/metabase:v`, `metabase/metabase-enterprise:v`), `METABASE_VERSION`, or version references. If undetected, AskUserQuestion (options: `v53 or older`, `v54–v58`, `v59+`). Abort if < v53 (modular embedding not available). Record the version.

### Step 1: Scan the project + fetch docs

Perform the project scan and doc fetch concurrently — they are independent. Use parallel tool calls within a single message wherever there are no dependencies.

#### 1a: Fetch target version docs

Use `scripts/fetch-docs.sh` to fetch the embedding documentation for the target Metabase version:

```bash
bash <skill-path>/scripts/fetch-docs.sh {TARGET_VERSION}
```

The script discovers all available doc pages for that version via the GitHub Contents API — no hardcoded page lists. After it completes, read all fetched files from `/tmp/embedjs-docs/`.

These docs are the authoritative source for web component attributes, `window.metabaseConfig` options, and guest embedding configuration for the target version. Use them in Step 2 for mapping instead of relying on hardcoded tables alone.

Launch this concurrently with the project scan steps below.

#### 1b: Identify backend language and framework

- Check for dependency/build files (`package.json`, `requirements.txt`, `Gemfile`, `pom.xml`, `go.mod`, `composer.json`, etc.).
- Identify the template engine and record the language and framework.

#### 1c: Find ALL static embedding code

Use Grep to search for all of these patterns (in parallel):

- `/embed/dashboard/` in all files — static embed dashboard URLs
- `/embed/question/` in all files — static embed question URLs
- `<iframe` in all template/HTML/JSX/view files — the embed elements
- `METABASE_SECRET_KEY` or `METABASE_EMBEDDING_SECRET_KEY` — the signing secret
- `resource:` near `dashboard` or `question` — JWT payload structure
- `iframeResizer` — optional auto-resize script

For each file with a match, read the entire file.

#### 1d: Find JWT signing code

Use Grep to search for all of these patterns (in parallel):

- `jwt.sign` or `jwt.encode` or `JWT` or `jsonwebtoken` or `PyJWT` or `jose`
- `METABASE_SECRET_KEY` or `MB_EMBEDDING_SECRET_KEY`
- `resource:` combined with `params:` (the static embed JWT payload shape)

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
  - Secret key variable: {name} (read at {file}:{line})
  - Other variables: ...
Layout/head file: {path}:{line range}
Static embeds found: {count}
  - {file}:{line} — {brief description} (dashboard/question, ID: {id})
  - ...
JWT signing: {file}:{line} — {library used}
JWT payload: resource type={dashboard|question}, params={list or "none"}
iframeResizer: {present|not present}
```

### Step 2: Analyze static embeds and map to web components (ONLY after Step 1 ✅)

Use the documentation fetched in Step 1a as the authoritative reference for web component attributes, `window.metabaseConfig` options, and guest embedding behavior. The hardcoded tables below are fallbacks — if the docs describe additional attributes or different behavior for the target version, prefer the docs.

For EACH static embed found in Step 1:

#### 2a: Parse the signed iframe URL

Extract from the iframe `src` attribute:

- **Metabase base URL**: may come from env var, constant, or be hardcoded
- **Content type**: `dashboard` or `question` (from the `/embed/{type}/` path)
- **Resource ID**: the numeric ID from the JWT `resource` field (e.g., `resource: { dashboard: 10 }`)
- **Locked parameters**: any `params` in the JWT payload (e.g., `params: { category: ["Gadget"] }`)
- **Hash parameters**: appearance customization after `#` (e.g., `#titled=true&bordered=false`)
- **iframeResizer usage**: whether `iFrameResize()` is called on this iframe

#### 2b: Map content type to web component

| Static embed URL pattern | Modular Web Component | Required Attribute |
|---|---|---|
| `/embed/dashboard/{JWT}` | `<metabase-dashboard>` | `token="{JWT}"` |
| `/embed/question/{JWT}` | `<metabase-question>` | `token="{JWT}"` |

The `token` attribute receives the same signed JWT that was previously baked into the iframe URL. The backend signing code stays the same — only the delivery mechanism changes.

If the token was built dynamically in a template (e.g., `src="<%= metabaseUrl %>/embed/dashboard/<%= token %>"`), extract the token variable and pass it as the `token` attribute (e.g., `token="<%= token %>"`).

#### 2c: Map hash parameters

**Parameters that map to web component ATTRIBUTES:**

| Static Embed Hash Param | Modular Equivalent |
|---|---|
| `titled=true/false` | `with-title="true/false"` on the component |
| `bordered=true/false` | No direct equivalent — drop (web components have no border chrome) |
| `refresh=N` | No direct equivalent — drop (handled by Metabase instance config) |
| `theme=night` | Use `window.metabaseConfig.theme` instead (if supported by version) |

#### 2d: Map locked and editable parameters

**Locked parameters** (in JWT `params` field) — no change needed. They remain in the JWT and continue to work the same way. The signed token already contains them.

**Editable parameters** — if the static embed allowed users to interact with filters, these can now be set as defaults via the `initial-parameters` attribute:

```html
<metabase-dashboard
  token="{JWT}"
  initial-parameters='{"category":["Doohickey","Gizmo"]}'
></metabase-dashboard>
```

`initial-parameters` sets default filter values that the user can change. This is a new capability not available in static iframe embedding.

#### 2e: Output Migration Mapping Table

For each static embed, output:

```
embed #{n}: {file}:{line}
  Old: {iframe HTML or signing + iframe code}
  Content type: {dashboard|question}
  Token variable: {template expression for the signed JWT}
  Locked params: {in JWT — no change needed}
  Hash params: {list or "none"}
  Dropped params: {list}
  Mapped attributes: {list}
  New: {exact replacement web component HTML}
```

### Step 3: Plan migration changes (ONLY after Step 2 ✅)

Create a complete file-by-file change plan covering all areas below. Every change should be specified with the target file, the old code, and the new code.

#### 3a: embed.js script injection — exactly once per app

- **Target**: the layout/head file identified in Step 1e
- **Location**: inside `<head>` (or as close as possible to other `<script>` tags)
- **Code to add**:
  ```html
  <script defer src="{METABASE_SITE_URL}/app/embed.js"></script>
  ```
- `{METABASE_SITE_URL}` should be rendered dynamically using the project's existing template expression syntax.
- Verify this will appear exactly once in the rendered HTML regardless of which page the user visits.

#### 3b: metabaseConfig — exactly once per app

- **Target**: same layout/head file as 3a
- **Location**: before the embed.js script tag (the config must be set before embed.js loads)
- **Code to add**:
  ```html
  <script>
    window.metabaseConfig = {
      isGuest: true,
      instanceUrl: "{METABASE_SITE_URL}",
    };
  </script>
  ```
- `isGuest: true` is required — it tells embed.js to use guest (signed token) mode instead of SSO mode.
- `instanceUrl` should be rendered dynamically using the project's template expression syntax.
- **Locale**: If a `locale` parameter was found in any static embed hash, add `locale: "{code}"` to the config object.
- Consult the fetched docs (Step 1a) for any additional `window.metabaseConfig` options supported by the target version (e.g., `theme`, `font`).
- `window.metabaseConfig` should be set exactly once.

#### 3c: Refactor backend token delivery

The backend already has JWT signing code that produces the token. Currently it builds a full iframe URL (`/embed/dashboard/{token}#params`). The signing logic stays — but how the token reaches the frontend changes:

- **Before**: Backend builds full iframe URL string, passes to template, template renders `<iframe src="{url}">`
- **After**: Backend passes just the signed token to the template, template renders `<metabase-dashboard token="{token}">`

For each signing location found in Step 1d:

1. Keep the JWT signing call (`jwt.sign(payload, METABASE_SECRET_KEY)`) unchanged
2. Remove the URL construction code that prepended `{baseUrl}/embed/dashboard/` and appended hash params
3. Pass the raw token string to the template context instead of the full URL

If the signing happens inline in the template handler (not in a shared function), the change is local to that handler.

#### 3d: iframe replacement plan

For EACH iframe from Step 2e's Migration Mapping Table:

- Specify: file path, exact old code to replace, exact new code
- The new web component uses `token="{token_variable}"` where `{token_variable}` is the template expression for the signed JWT
- Map hash parameters to component attributes per Step 2c
- **Preserve styling**: Transfer the iframe's sizing directly to the web component element — no wrapper `<div>` needed:
  - If the iframe had `width`/`height` HTML attributes or inline `style`, apply them directly to the web component (e.g., `<metabase-dashboard token="..." style="width:800px;height:600px">`)
  - If the iframe was styled via CSS classes, apply those classes directly to the web component
  - If the iframe was inside a container that already controls sizing, no extra styling needed — the web component will fill that container
  - If the iframe used `iframeResizer` for auto-height, drop it — web components handle their own sizing
- Remove any `iframeResizer` calls associated with this iframe

#### 3e: Dead code removal

After replacing iframes, identify and remove:

- URL construction code that built `/embed/dashboard/{token}#params` or `/embed/question/{token}#params` strings
- `iframeResizer.js` script tag and any `iFrameResize()` calls
- Hash parameter string construction (e.g., `const mods = "titled=true&bordered=false"`)
- Any helper functions that were only used for building static embed iframe URLs

Do not remove:
- JWT signing code (`jwt.sign(payload, METABASE_SECRET_KEY)`) — still used
- `METABASE_SECRET_KEY` env var — still used
- JWT library imports — still used
- Any code used by other parts of the application

#### 3f: Metabase admin configuration notes (manual steps for the user)

List these as part of the plan — they will be included in the final summary:

1. **Enable modular embedding**: Admin > Embedding > toggle "Enable modular embedding"
2. **Enable guest embedding**: Admin > Embedding > ensure "Guest embedding" (or "Static embedding" in older UI) is enabled. The existing static embedding secret key is reused.
3. **Configure CORS origins**: Admin > Embedding > Modular embedding > add the host app's domain (e.g., `http://localhost:9090`). This is new — static iframe embedding did not require CORS configuration.

### Step 4: Apply code changes (ONLY after Step 3 ✅)

Apply all changes from Step 3 in this order:

1. **First**: Add `window.metabaseConfig` assignment and embed.js script tag to the layout/head file (Step 3b + 3a, config before embed.js)
2. **Second**: Refactor backend token delivery — keep signing, remove URL construction (Step 3c)
3. **Third**: Replace each iframe with its web component (Step 3d), one file at a time
4. **Fourth**: Remove dead code — iframeResizer, URL builders (Step 3e)

**Constraints:**

- Use the Edit tool with precise `old_string` / `new_string` for every change
- Do not add new package dependencies — modular embedding requires only the embed.js script served by the Metabase instance
- Do not change or remove `METABASE_SECRET_KEY` — it is still used for signing
- If a file requires multiple edits, apply them top-to-bottom to avoid offset issues

### Step 5: Validate changes (ONLY after Step 4 ✅)

Perform all of these checks. Each check should have an explicit pass/fail result.

#### 5a: No remaining static embed iframes

Use Grep to search for `/embed/dashboard/` and `/embed/question/` across all project files (excluding `node_modules`, `.git`, lockfiles).

**Pass criteria**: zero static embed URL constructions found (the pattern may still appear in comments — verify these are not live code).

#### 5b: embed.js appears exactly once

Use Grep to search for `/app/embed.js` across all project files (excluding `node_modules`, `.git`).

**Pass criteria**: exactly ONE occurrence in the layout/head file.

#### 5c: window.metabaseConfig is set exactly once

Use Grep to search for `window.metabaseConfig` across all project files (excluding `node_modules`, `.git`).

**Pass criteria**: exactly ONE occurrence with `isGuest: true`.

#### 5d: JWT signing code is preserved

Read the JWT signing file(s). Verify:
- `jwt.sign` (or equivalent) call still exists
- `METABASE_SECRET_KEY` is still read from environment
- JWT payload still contains `resource` and `params` fields

**Pass criteria**: signing logic intact.

#### 5e: No remaining iframeResizer references

Use Grep to search for `iframeResizer` and `iFrameResize` across all project files.

**Pass criteria**: zero references remain (or only in unrelated code).

#### 5f: Spot-check modified files

Read each modified file and verify:
- Web components have `token` attribute with correct template expression
- Template syntax is valid (no unclosed tags, correct expressions)
- Dead code identified in Step 3e has been removed

**Pass criteria**: all checks pass.

If ANY check fails:
- Fix the issue immediately
- Re-run the specific check
- If unable to fix after 3 attempts, mark Step 5 ❌ blocked and report which check failed and why

### Step 6: Output summary

Organize the final output into these sections:

1. **Changes applied**: list every file modified and a one-line description of each change
2. **Web component mapping**: table showing each old signed iframe → new web component:
   ```
   | File | Old | New |
   |---|---|---|
   | views/analytics.ejs | <iframe src="/embed/dashboard/{token}#titled=true"> | <metabase-dashboard token="{token}" with-title="true"> |
   ```
3. **What stayed the same**: JWT signing logic, `METABASE_SECRET_KEY`, locked parameters in JWT `params` field
4. **Dropped parameters**: list of static embed hash parameters that were dropped, with brief explanation
5. **New capabilities available**: features now accessible that weren't in static iframe embedding:
   - `initial-parameters` attribute for editable filter defaults
   - `with-downloads` attribute for enabling downloads (Pro/Enterprise)
   - Better mobile responsiveness (web components adapt to container)
6. **Manual steps required** (Metabase admin configuration from Step 3f):
   - Enable modular embedding
   - Ensure guest embedding is enabled (reuses existing secret key)
   - Configure CORS origins (new requirement)
7. **Behavioral differences the user should be aware of**:
   - Web components expand to fill their container — if the iframe had fixed dimensions, verify the container provides appropriate sizing
   - The `bordered` appearance option is no longer available — web components render without a frame
   - Auto-refresh (`refresh=N`) is no longer controlled per embed — configure it in Metabase instance settings instead

## Retry policy

**Doc fetching:**
- The `scripts/fetch-docs.sh` script exits with an error if the version's docs directory does not exist. If this happens, verify the Metabase version number and retry. If still failing, mark Step 1 ❌ blocked.

**Validation:**
- If any validation check in Step 5 fails after 3 fix attempts, mark Step 5 ❌ blocked and report which check failed and why.
- If AskUserQuestion is not answered, remain blocked on that step — do not guess or proceed with assumptions.
