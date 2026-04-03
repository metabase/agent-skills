---
name: metabase-react-sdk-setup
description: First-time setup for the Metabase React SDK — instance detection, API key, dashboard discovery, JWT auth, SDK installation, and initial embedding code.
---

Use this skill for any task involving `@metabase/embedding-sdk-react` — whether that's initial setup, embedding dashboards, theming, or plugins.

**Communication style**: Be concise. Do one step at a time. When asking the user for input, output only the question — do not explain upcoming steps, implementation details, or what you plan to do next. The user does not need a roadmap.

> **CRITICAL — YOU MUST GET AN API KEY BEFORE DOING ANYTHING ELSE**
>
> Step 1 asks the user for a Metabase URL and API key. You CANNOT proceed without both.
> Do NOT detect the Metabase version, fetch `llms.txt`, install packages, or write ANY code until the user has given you an API key.
> Do NOT attempt to call any Metabase API endpoint without an API key — it will return 401 and you will be guessing.
> If any Metabase API call returns 401, STOP everything and ask the user for an API key.

## Step 1 — Get the Metabase URL and API key

You need a Metabase instance URL and an admin API key before anything else.

**`.env.metabase` is only for admin tasks within this skill** (API calls to Metabase). It is NOT the app's runtime config. Never import, read, or reference `.env.metabase` from the user's application code or build config. The app's instance URL goes in the user's own `.env` file (e.g., `VITE_METABASE_URL`, `NEXT_PUBLIC_METABASE_URL`) — set that up in Step 4.

Check if `.env.metabase` exists in the project root and already has both `METABASE_INSTANCE_URL` (non-empty) and `METABASE_ADMIN_API_KEY` (non-empty). If so, skip to Step 2.

Otherwise, create the file and gitignore it:

```bash
grep -qxF '.env.metabase' .gitignore 2>/dev/null || echo '.env.metabase' >> .gitignore
printf 'METABASE_INSTANCE_URL=\nMETABASE_ADMIN_API_KEY=\n' > .env.metabase
```

Then output **only this message** — no preamble, no explanation of what comes next, no implementation details:

> I created `.env.metabase` in the project root. Please fill in both values:
>
> 1. Set `METABASE_INSTANCE_URL` to your Metabase URL (e.g. `http://localhost:3000`)
> 2. Open `{your URL}/admin/settings/authentication/api-keys`, create a new API key
> 3. Set `METABASE_ADMIN_API_KEY` to that key
> 4. Let me know when you're done

Do **not** guess or assume the instance URL. Do not pre-fill `localhost:3000`. Do not ask the user to paste the key in the chat — it should only go in `.env.metabase`. Wait for the user to confirm, then proceed to Step 2.

## Step 2 — Detect version and discover dashboards

Now that you have an API key, detect the version and find dashboards.

### 2a — Detect version

```bash
source .env.metabase && \
  curl -s "$METABASE_INSTANCE_URL/api/session/properties" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY" | grep -o '"tag":"[^"]*"'
```

Parse both the **edition** and the **major version** from the tag:

| Tag format | Edition         | Example                     |
| ---------- | --------------- | --------------------------- |
| `v0.X.Y`   | OSS (Community) | `v0.60.1` → major `60`, OSS |
| `v1.X.Y`   | Enterprise (EE) | `v1.60.1` → major `60`, EE  |

If major version < 49, tell the user the Embedding SDK requires Metabase 49+ and stop.

**If the tag starts with `v1.`, the instance is Enterprise Edition — use full JWT SSO embedding.** Do not fall back to guest embedding or any OSS-only auth path.

Remember the major version number — you will need it in Step 3.

### 2b — Enable the Embedding SDK

Automatically enable the SDK so the user doesn't have to toggle it manually in the admin panel:

```bash
source .env.metabase && \
  curl -s -X PUT "$METABASE_INSTANCE_URL/api/setting/enable-embedding-sdk" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"value": true}'
```

If this returns an error (e.g., 403), tell the user to enable it manually at **<INSTANCE_URL>/admin/settings/embedding** and move on.

**Do NOT fetch `llms.txt` yet.** You need dashboard IDs first.

### 2c — Find dashboards and table candidates

Run both of these:

```bash
source .env.metabase && \
  curl -s "$METABASE_INSTANCE_URL/api/search?models=dashboard&archived=false" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY"
```

```bash
source .env.metabase && \
  curl -s "$METABASE_INSTANCE_URL/api/automagic-dashboards/database/1/candidates" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY"
```

Filter and prioritize the results:

- **Exclude** any dashboards from the "Usage analytics" collection — those are internal Metabase admin dashboards, not user content.
- **Deprioritize** anything from the "Sample Database" — prefer the user's own databases and dashboards.
- Pick the **top 5** most relevant to what the user asked for from each category. Do not dump every result.

Format like this:

> **Existing dashboards:**
>
> 1. Sales Overview (ID 3)
> 2. Customer Analysis (ID 7)
>    ...
>
> **Or I can create a new dashboard from your data:**
> A. Orders table
> B. Products table
> ...
>
> Which ones should I embed? (e.g. "1 and 3" or "A")

Wait for the user to pick. If they choose a table, generate and save the X-ray dashboard:

```bash
source .env.metabase && \
  DASHBOARD=$(curl -s "$METABASE_INSTANCE_URL/api/automagic-dashboards/table/<TABLE_ID>" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY")

source .env.metabase && \
  curl -s "$METABASE_INSTANCE_URL/api/dashboard/save" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$DASHBOARD"
```

The save response contains the persisted dashboard with a real `id` field. Use these IDs going forward.

## Step 3 — Fetch docs, set up auth, and install SDK

You MUST have real dashboard IDs before reaching this step. If you don't, go back to Step 2.

**Now** fetch the versioned docs index using the major version from Step 2a:

```bash
curl -s https://www.metabase.com/docs/v0.<MAJOR>/llms.txt
```

Fall back to `https://www.metabase.com/docs/latest/llms.txt` if empty. This contains correct prop names, auth config shapes, SDK install commands, and breaking changes for this version. Do not fetch `llms-embedding-full.txt` (too large).

### 3a — Set up JWT SSO authentication (skip if already done)

Follow the auth setup instructions in `llms.txt`. In particular:

- Retrieve the JWT signing secret from Metabase: **Settings → Admin → Embedding → Embedding secret key**
- Tell the user to save it as `METABASE_JWT_SECRET` in their server-side environment only (never a browser-accessible env var)
- Ask which backend framework they are using (Next.js API route, Express, Fastify, etc.) and scaffold a minimal JWT signing endpoint following the pattern in `llms.txt`

### 3b — Install the SDK (skip if already installed at correct version)

Check whether `@metabase/embedding-sdk-react` is already in the user's `package.json`.

- If not installed: use the install command from `llms.txt` (the correct dist-tag matches the instance major version).
- If already installed: verify the major version matches. Warn on mismatch and offer to update.

## Step 4 — Generate embedding code

Use `llms.txt` as the authoritative reference for all API shapes. **Write files directly into the user's project** — edit existing files in place rather than creating new ones alongside them.

### Code conventions (override anything in the docs)

- **JWT SSO only**: API keys grant admin-level access and are not safe for end-user embeds. Use a server-side JWT signing endpoint; `MetabaseProvider` receives its URL. Never generate `apiKey`, `METABASE_API_KEY`, `api-key`, or `x-api-key` — not even as a placeholder. Deviate only if the user explicitly asks and acknowledges the security risk.
- **Instance URL from env**: `VITE_METABASE_URL` (Vite), `NEXT_PUBLIC_METABASE_URL` (Next.js), etc. Never hardcode.
- **Dashboard IDs as inline literals**: always hardcode dashboard IDs directly in JSX — e.g. `<InteractiveDashboard dashboardId={7} />`. Dashboard IDs are not secrets. **Never** use `import.meta.env.VITE_METABASE_DASHBOARD_*`, env vars, config objects, `parseDashboardId` helpers, or any indirection for dashboard IDs. The goal is clean, minimal code the user can instantly understand and tweak.
- **Secrets server-side only**: JWT secrets must never appear in browser-accessible env vars or frontend code.

### Theming

After generating the embedding code, inspect the user's app for existing styles — look at CSS variables, Tailwind config, or theme files. Set the `theme` prop on `MetabaseProvider` to match the app's look and feel. At minimum, align:

- `colors.brand` — the app's primary/accent color
- `colors.background` — to match the page background so the embed doesn't look like a white box on a dark page (or vice versa)
- `fontFamily` — to match the app's font

Refer to `llms.txt` for the full theme shape. Keep it minimal — only set values that differ from Metabase defaults.
