---
name: metabase-embedding-sso-implementation
description: Implements JWT SSO authentication for Metabase embedding in a project. Supports all embedding types that use SSO — Modular embedding (embed.js web components), Modular embedding SDK (@metabase/embedding-sdk-react), and Full App embedding (iframe-based). Creates the JWT signing endpoint, configures the frontend auth layer, and sets up group mappings. Use when the user wants to add SSO/JWT auth to their Metabase embedding, implement user identity for embedded analytics, set up JWT authentication for Metabase, or connect their app's authentication to Metabase embedding.
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, Task, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
---

## Execution contract

Follow the workflow steps in order — do not skip any step. Create the checklist first, then execute each step and explicitly mark it done with evidence. Each step's output feeds into the next, so skipping steps produces incorrect implementations.

If you cannot complete a step due to missing info or tool failure, you must:

1. record the step as ❌ blocked,
2. explain exactly what is missing / what failed,
3. stop (do not proceed to later steps).

Each workflow step must end with `Status: ✅ complete` or `Status: ❌ blocked`. Steps are sequential — do not start a step until the previous one is complete. Each step must include evidence (detected code patterns, file paths, diffs applied, pass/fail results).

## Architectural conformance

Follow the app's existing architecture, template engine, layout/partial system, code style, and route patterns. Do not switch paradigms (e.g., templates to inline HTML or vice versa). If the app has middleware for shared template variables, prefer that over duplicating across route handlers.

The JWT SSO endpoint must integrate with the app's **existing authentication system**. The endpoint must only issue Metabase JWTs for users who are already authenticated in the host app. Never create an endpoint that issues tokens without verifying the user's session first.

**SSO requests to the Metabase instance should be proxied through the app's backend whenever possible** (FE → BE → Metabase `/auth/sso`). This keeps the Metabase instance URL and JWT tokens off the client, avoids CORS issues, and ensures auth is always validated server-side. Only fall back to direct FE→Metabase calls if the app has no backend (e.g., a static SPA with no server).

## Important performance notes

- Maximize parallelism within each step. Use parallel Grep/Glob/Read calls in a single message wherever possible.
- Do not use sub-agents for project scanning — results need to stay in the main context for cross-referencing in later steps.
- Do not parse repo branches, commits, PRs, or issues.

## Scope

This skill implements JWT SSO authentication for Metabase embedding. It supports all three embedding types that use SSO:

| Embedding type | Delivery mechanism | Frontend auth config |
|---|---|---|
| **Modular embedding** (embed.js) | Web components (`<metabase-dashboard>`, etc.) | `window.metabaseConfig` — see fetched docs for available auth fields |
| **Modular embedding SDK** (`@metabase/embedding-sdk-react`) | React components (`<InteractiveDashboard>`, etc.) | `defineMetabaseAuthConfig()` — see fetched docs for available auth fields |
| **Full App embedding** | iframe with full Metabase UI | iframe `src` points through SSO endpoint |

The SSO endpoint response format (JSON, redirect, proxy to Metabase `/auth/sso`, etc.) varies by embedding type and Metabase version — consult the fetched docs to determine the correct behavior.

**The consumer's app may be written in any backend language** (Node.js, Python, Ruby, PHP, Java, Go, .NET, etc.). Keep instructions language-agnostic unless a specific language is detected in Step 1.

### What this skill handles

- Creating a JWT signing endpoint that maps the app's authenticated user to Metabase JWT fields (`email`, `first_name`, `last_name`, `groups`, `exp`)
- Configuring the frontend auth layer based on the detected embedding type
- Adding the `METABASE_JWT_SHARED_SECRET` environment variable
- Installing a JWT signing library if one is not already present
- Producing Metabase admin configuration instructions (JWT settings, group mappings, CORS)

### What this skill does NOT handle

- Setting up the embedding itself (web components, SDK, or iframes) — use the migration skills for that
- Upgrading the embedding version — use the `metabase-modular-embedding-version-upgrade` skill
- Guest embedding auth (uses `METABASE_SECRET_KEY` with `{resource, params}` payloads, not SSO)
- SAML or LDAP authentication — this skill covers JWT SSO only

### JWT payload structure (SSO)

The JWT signed with `METABASE_JWT_SHARED_SECRET` must contain these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | Yes | User's email — Metabase uses this as the unique identifier. Auto-provisions account on first login. |
| `first_name` | string | Yes | User's first name — synced on every login. |
| `last_name` | string | Yes | User's last name — synced on every login. |
| `groups` | string[] | Yes | Array of group names — Metabase syncs group memberships on every login when group sync is enabled. |
| `exp` | number | Yes | Token expiration as Unix timestamp. Recommend 10 minutes: `Math.round(Date.now() / 1000) + 600`. |

Additional user attributes can be included as extra key/value pairs in the JWT — Metabase will store them as user attributes for use in sandboxing and data permissions.

## Allowed documentation sources

Use `scripts/fetch-docs.sh` to fetch docs — it discovers available pages dynamically via the GitHub Contents API, so it works with any version without hardcoded logic. Do not construct doc URLs manually.

Other constraints:
- No GitHub PRs/issues, npm pages, or metabase.com — only `raw.githubusercontent.com`
- Do not follow changelog links to GitHub or guess URLs not handled by the script

## AskUserQuestion triggers

Use AskUserQuestion and halt until answered if:

- No Metabase embedding code is detected in the project (ask which embedding type the user plans to use)
- The Metabase instance URL cannot be determined from project code or environment variables
- The Metabase instance version cannot be determined from the project code
- The app's user authentication mechanism cannot be determined (how do users log in? session? cookie? token?)
- The user model/schema cannot be identified (where are email, name, and group/role stored?)
- The user's group/role model does not clearly map to Metabase groups (ask the user how they want to map roles → Metabase groups)
- The backend language cannot be determined

### Implementation Plan Checklist

Create a checklist to track progress. In Claude Code, use TaskCreate/TaskUpdate tools:

- Step 0: Detect embedding type and Metabase version
- Step 1: Scan project + fetch detected version docs
- Step 2: Design auth architecture
- Step 3: Plan implementation changes
- Step 4: Apply code changes
- Step 5: Validate changes
- Step 6: Final summary

## Workflow

### Step 0: Detect embedding type and Metabase version

#### 0a: Detect embedding type

Grep the project for these patterns (in parallel) to determine which embedding type is in use:

**Modular embedding (embed.js):**
- `embed.js` or `/app/embed.js` in HTML/template files
- `window.metabaseConfig` or `defineMetabaseConfig`
- `<metabase-dashboard`, `<metabase-question`, `<metabase-browser`

**Modular embedding SDK:**
- `@metabase/embedding-sdk-react` in `package.json` or import statements
- `MetabaseProvider` or `defineMetabaseAuthConfig`
- `InteractiveDashboard`, `InteractiveQuestion`, `CollectionBrowser`

**Full App embedding:**
- `<iframe` with Metabase URLs (look for the instance URL or `/dashboard/`, `/question/`, `/auth/sso`)
- `/auth/sso` redirect logic
- `return_to` parameter construction

If no embedding code is found → AskUserQuestion: which embedding type does the user plan to use?

If multiple types are detected, the SSO endpoint must handle all of them (see dual-mode endpoint in Step 2).

Record the detected embedding type(s) — this controls the entire implementation.

#### 0b: Detect Metabase instance version

The Metabase **instance version** determines which auth config fields, function signatures, and SSO behavior are available. Always AskUserQuestion for the instance version — even if a version appears in Docker tags, env vars, or package.json, confirm it with the user. The instance version is the source of truth for fetching docs.

**SDK/instance version mismatch check**: If the project uses `@metabase/embedding-sdk-react` (npm package), compare the SDK package version with the instance version. The SDK package version must match the instance version — e.g., SDK v0.52.x requires instance v0.52.x. If they don't match, stop and tell the user to align the versions before proceeding with SSO. Suggest using the `metabase-modular-embedding-version-upgrade` skill to upgrade.

### Step 1: Scan the project + fetch docs

Perform the project scan and doc fetch concurrently — they are independent. Use parallel tool calls within a single message wherever there are no dependencies.

#### 1a: Fetch docs for the Metabase instance version

Use `scripts/fetch-docs.sh` to fetch the embedding documentation for the instance version confirmed in Step 0b:

```bash
bash <skill-path>/scripts/fetch-docs.sh {INSTANCE_VERSION}
```

The script discovers all available doc pages for that version via the GitHub Contents API. After it completes, read **all** fetched files from `/tmp/embedjs-docs/` — the file containing auth/SSO configuration details varies by version (e.g., `authentication.md` in newer versions, `interactive-embedding.md` in older ones). Search across all files for `fetchRequestToken`, `authProviderUri`, `jwtProviderUri`, `defineMetabaseAuthConfig`, `JWT`, and `SSO` to find the relevant auth documentation.

These docs are the authoritative source for auth configuration options, function signatures, deprecated fields, and endpoint response formats for the detected version. Use them in Step 2 when designing the auth architecture.

Launch this concurrently with the project scan steps below.

#### 1b: Identify backend language and framework

- Check for dependency/build files (`package.json`, `requirements.txt`, `Gemfile`, `pom.xml`, `go.mod`, `composer.json`, etc.).
- Identify the web framework (Express, Fastify, Flask, Django, Rails, Spring, Gin, Laravel, ASP.NET, etc.).
- Record the language, framework, and any middleware patterns.

#### 1c: Find existing authentication code

This is critical — the SSO endpoint must integrate with the app's existing auth. Search for:

- Session middleware (`express-session`, `cookie-session`, `flask-login`, `devise`, `Passport`, `next-auth`, etc.)
- Auth middleware patterns (`req.user`, `req.session`, `current_user`, `@login_required`, `[Authorize]`)
- User model/schema definitions (look for fields: `email`, `name`, `first_name`, `last_name`, `role`, `group`)
- Login routes (`/login`, `/auth`, `/signin`, `/api/auth`)
- Token/cookie based auth (JWT verification middleware, cookie parsers)

For each matching file, read the entire file.

#### 1d: Find existing Metabase embedding code

Read all files identified in Step 0a. Extract:

- The Metabase instance URL (env var or hardcoded)
- Current auth configuration (if any — may already have partial SSO setup)
- Layout/head files where embed.js or metabaseConfig is configured
- Any existing SSO/JWT endpoint for Metabase
- Environment variables related to Metabase (`METABASE_`, `MB_`)

#### 1e: Find user model and group/role structure

Search for the user model to understand available fields:

- Database schema files, ORM models, or type definitions containing user fields
- Group/role definitions (enums, database tables, constants)
- How the current user is attached to the request (e.g., `req.user`, session store)

#### Output: Structured Project Inventory

```
Backend: {language}, {framework}
Auth system: {mechanism} (e.g., express-session + Passport, next-auth, Django sessions)
User model: {file}:{line} — fields: {email, first_name, last_name, role, ...}
User on request: {how to access} (e.g., req.user, request.user, session[:user])
Groups/roles: {source} — values: {list of group/role names}
Embedding type: {modular | sdk | full-app | multiple}
Metabase URL: {env var or value}
Metabase version: {version}
Existing SSO endpoint: {file}:{line} or "none"
Existing auth config: {description} or "none"
```

### Step 2: Design auth architecture (only after Step 1 ✅)

Based on the project inventory, design the SSO implementation. This step produces the design — no code changes yet.

#### 2a: JWT endpoint design

Design the SSO endpoint route:

- **Route**: Choose a route that fits the app's existing patterns. Common choices: `/sso/metabase`, `/api/auth/metabase`, `/auth/metabase-sso`. Follow the app's existing route naming conventions.
- **HTTP method**: GET (Metabase's SDK/embed.js sends GET requests to the JWT provider URI)
- **Auth guard**: The endpoint MUST be protected by the app's existing auth middleware. Only authenticated users should receive a Metabase JWT. Specify which middleware/decorator to use based on Step 1c findings.
- **User mapping**: Define how to extract user fields from the request:

  ```
  email       ← {source} (e.g., req.user.email)
  first_name  ← {source} (e.g., req.user.firstName or req.user.name.split(' ')[0])
  last_name   ← {source} (e.g., req.user.lastName or req.user.name.split(' ')[1])
  groups      ← {source} (e.g., [req.user.role] or req.user.groups)
  ```

- **Group mapping strategy**: If the app's roles/groups don't directly match desired Metabase groups, define a mapping:

  ```
  App role "admin"    → Metabase group "Administrators"
  App role "analyst"  → Metabase group "Analysts"
  App role "viewer"   → Metabase group "Viewers"
  ```

  If the mapping is unclear → AskUserQuestion.

- **Token expiration**: 10 minutes (`Math.round(Date.now() / 1000) + 600`) unless the app has a specific session timeout that should be matched.

#### 2b: Endpoint response behavior

Consult the fetched docs to determine what the SSO endpoint should return for the detected embedding type and Metabase version. The response format (JSON with a signed JWT, redirect to Metabase `/auth/sso`, server-side proxy, etc.) varies — do not assume a fixed pattern. The docs describe how the SDK/embed.js/iframe expects to receive the authentication token for the detected version.

If the project uses multiple embedding types, the endpoint may need to support multiple response modes (e.g., distinguishing via a query parameter). Check the docs for how each embedding type calls the JWT provider.

#### 2c: Frontend auth configuration

Decide the frontend auth approach based on embedding type. Consult the docs fetched in Step 1a to determine which auth config fields are available for the detected version — field names, signatures, and supported options vary across versions. The exact code patterns are specified in Step 3d.

#### 2d: JWT library selection

If the project doesn't already have a JWT library:

| Language | Library | Install command |
|---|---|---|
| Node.js | `jsonwebtoken` | `npm install jsonwebtoken` |
| Python | `PyJWT` | `pip install PyJWT` |
| Ruby | `jwt` | `gem install jwt` |
| PHP | `firebase/php-jwt` | `composer require firebase/php-jwt` |
| Java | `io.jsonwebtoken:jjwt` | Add to Maven/Gradle |
| Go | `github.com/golang-jwt/jwt/v5` | `go get github.com/golang-jwt/jwt/v5` |
| .NET | `System.IdentityModel.Tokens.Jwt` | `dotnet add package System.IdentityModel.Tokens.Jwt` |

If a JWT library is already in the project, use it.

### Step 3: Plan implementation changes (only after Step 2 ✅)

Create a complete file-by-file change plan. Every change should be specified with the target file, the old code (if modifying), and the new code.

#### 3a: Environment variable

- Add `METABASE_JWT_SHARED_SECRET` to the project's environment configuration (`.env`, `.env.example`, `docker-compose.yml`, or wherever other Metabase env vars are defined)
- Value: placeholder string with a comment explaining it must match the key generated in Metabase admin

#### 3b: JWT library installation

- If no JWT library is present: specify the install command
- If one exists: skip this step

#### 3c: SSO endpoint implementation

Specify the exact code for the new endpoint:

- File: where to add the route (existing routes file, or new file if the app separates routes by feature)
- Auth middleware applied to the route
- User field extraction (from Step 2a mapping)
- JWT signing with `METABASE_JWT_SHARED_SECRET`
- Response format as determined in Step 2b (from the fetched docs)

**The endpoint must:**
- Read `METABASE_JWT_SHARED_SECRET` from environment
- Extract the authenticated user from the request (using the app's existing auth mechanism)
- Build the JWT payload with `email`, `first_name`, `last_name`, `groups`, `exp`
- Sign the token using the HS256 algorithm (Metabase's default)
- Return the response appropriate for the embedding type

**The endpoint must NOT:**
- Accept user identity from the request body or query params (security vulnerability — user could forge identity)
- Issue tokens without checking authentication
- Hardcode user information
- Use a different signing algorithm unless specifically configured in Metabase admin

#### 3d: Frontend auth configuration

Use the docs fetched in Step 1a as the authoritative source for auth config fields, function signatures, and deprecated options for the target Metabase version. Config fields, parameter signatures, and deprecated options change across versions — do not assume any specific field exists without confirming it in the docs.

**Modular embedding (embed.js):**
- Check the docs for which auth-related fields `window.metabaseConfig` supports in the detected version (e.g., `jwtProviderUri` may or may not be available).
- If the docs do not list a frontend auth config field, the JWT Identity Provider URI must be configured in Metabase admin only.

**Modular embedding SDK:**
- Check the docs for the `defineMetabaseAuthConfig` options and the `fetchRequestToken` function signature — especially whether it receives parameters or not.
- The endpoint URL should be hardcoded in the `fetchRequestToken` body unless the docs say otherwise.
- Remove any deprecated auth config fields that the existing code uses (e.g., `authProviderUri` was removed in later versions). The docs for the detected version are the source of truth for what fields are valid.

**Full App embedding:**
- Update iframe `src` to route through the SSO endpoint or Metabase's `/auth/sso` path with a `return_to` parameter containing the URL-encoded destination path (e.g., `%2Fdashboard%2F1`).

#### 3e: Remove development-only and deprecated auth (if present)

Remove any auth config fields that are not listed in the detected version's docs. Common examples:
- `apiKey` — API keys are for local dev only, not production SSO
- `useExistingUserSession` — uses the admin browser session, not for production
- Any other fields present in the existing code but absent from the detected version docs (they were likely deprecated or removed)

#### 3f: Metabase admin configuration notes (manual steps)

List these as part of the plan — they will be included in the final summary:

1. **Enable JWT authentication**: Admin > Settings > Authentication > JWT > enable
2. **Set JWT signing key**: Paste the same value as `METABASE_JWT_SHARED_SECRET`
3. **Set JWT Identity Provider URI**: The full URL of the SSO endpoint (e.g., `http://localhost:9090/sso/metabase`) — check the fetched docs to determine whether this is required or optional for the detected version (it depends on whether the frontend config supports a JWT provider field).
4. **Configure group sync** (if groups are used):
   - Enable "Synchronize Group Memberships"
   - Create matching groups in Metabase, or set up group mappings if names differ
5. **Configure CORS** (for modular embedding only): Admin > Embedding > Modular embedding > add the host app's domain
6. **SameSite cookie setting** (for cross-domain deployments): Admin > Embedding > set to "None" (requires HTTPS)

### Step 4: Apply code changes (only after Step 3 ✅)

Apply all changes from Step 3 in this order:

1. **First**: Add environment variable (Step 3a)
2. **Second**: Install JWT library if needed (Step 3b)
3. **Third**: Create the SSO endpoint (Step 3c) — this is the core change
4. **Fourth**: Configure frontend auth (Step 3d)
5. **Fifth**: Remove dev-only auth if present (Step 3e)

**Constraints:**

- Use the Edit tool with precise `old_string` / `new_string` for every change to existing files
- Use the Write tool only for new files
- Do not change the app's existing authentication system — only add the Metabase SSO layer on top
- Do not change environment variable names that already exist in the project
- If a file requires multiple edits, apply them top-to-bottom to avoid offset issues

### Step 5: Validate changes (only after Step 4 ✅)

Perform all of these checks. Each check should have an explicit pass/fail result.

#### 5a: SSO endpoint exists and is auth-protected

Read the SSO endpoint file. Verify:
- The route exists with the planned path
- Auth middleware is applied (the endpoint is protected)
- The JWT payload includes all required fields: `email`, `first_name`, `last_name`, `groups`, `exp`
- The token is signed with `METABASE_JWT_SHARED_SECRET` from environment
- The response format matches what the fetched docs specify for the embedding type

**Pass criteria**: endpoint is complete and auth-protected.

#### 5b: Frontend auth is configured

Verify the frontend auth config uses only fields listed in the detected version's docs. No deprecated or removed fields should remain.
- **embed.js**: `window.metabaseConfig` auth fields match what the docs support
- **SDK**: `defineMetabaseAuthConfig` options and `fetchRequestToken` signature match the docs
- **Full App**: iframe src routes through SSO

**Pass criteria**: frontend auth matches the embedding type and detected version docs.

#### 5c: No dev-only or deprecated auth remains

Use Grep to search for `useExistingUserSession` across all project files (excluding `node_modules`, `.git`). Also search for `apiKey` near `metabaseConfig` or `defineMetabaseAuthConfig` — a bare `apiKey` grep is too broad and will match unrelated code. Also verify no deprecated config fields remain (compare against the detected version docs).

**Pass criteria**: no Metabase-specific development-only or deprecated auth methods remain.

#### 5d: JWT library is available

Check that the JWT library is in the project's dependencies (e.g., `package.json`, `requirements.txt`).

**Pass criteria**: library is listed or was already present.

#### 5e: Spot-check the endpoint code

Verify the endpoint does NOT:
- Accept user identity from request body/query params
- Issue tokens without auth middleware
- Hardcode user information
- Use a signing key other than `METABASE_JWT_SHARED_SECRET`

**Pass criteria**: all security checks pass.

If any check fails:
- Fix the issue immediately
- Re-run the specific check
- If unable to fix after 3 attempts, mark Step 5 ❌ blocked and report which check failed and why

### Step 6: Output summary

Organize the final output into these sections:

1. **Changes applied**: list every file modified/created and a one-line description of each change
2. **SSO endpoint**: route path, HTTP method, response behavior, which auth middleware protects it
3. **JWT payload mapping**: table showing how app user fields map to Metabase JWT fields:
   ```
   | Metabase field | Source | Example value |
   |---|---|---|
   | email | req.user.email | "jane@example.com" |
   | first_name | req.user.firstName | "Jane" |
   | last_name | req.user.lastName | "Doe" |
   | groups | [req.user.role] | ["Analyst"] |
   | exp | Date.now()/1000 + 600 | 1700000600 |
   ```
4. **Group mapping**: how app roles/groups map to Metabase groups (if a mapping was defined)
5. **Manual steps required** (Metabase admin configuration from Step 3f):
   - Enable JWT authentication and set signing key
   - Set JWT Identity Provider URI
   - Configure group sync and mappings
   - Configure CORS (if modular embedding)
   - Set SameSite cookie (if cross-domain)
6. **Security notes**:
   - The endpoint is protected by `{middleware}` — only authenticated users can obtain a Metabase JWT
   - `METABASE_JWT_SHARED_SECRET` must be kept secret and match the value in Metabase admin
   - Each user gets their own Metabase account (auto-provisioned on first login)
   - Token expiration is set to {N} minutes

## Retry policy

- If AskUserQuestion is not answered, remain blocked on that step — do not guess or proceed with assumptions.
- If any validation check in Step 5 fails after 3 fix attempts, mark Step 5 ❌ blocked and report which check failed and why.
