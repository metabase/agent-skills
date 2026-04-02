---
name: metabase-react-sdk-setup
description: One-time setup for Metabase Embedding SDK. Confirms the Metabase instance URL and version, sets up authentication (API key for dev, JWT for production), and installs the SDK.
---

Run these steps to prepare a project for Metabase embedded analytics. This covers instance verification, auth mode selection, and SDK installation. Once complete, use the `metabase-react-sdk-docs` skill for any embedding tasks.

---

## Step 1 — Get the Metabase instance URL

Ask the user: "Do you have a Metabase instance URL, or would you like to set one up locally?"

- **If they provide a URL**: proceed to Step 2.
- **If they want a local instance**: invoke the `setup-metabase-instance` skill. Once it is running, use `http://localhost:3000` (or the port it started on) as the instance URL and continue with Step 2.

---

## Step 2 — Check Metabase version and fetch docs

Run **exactly this command** — do not try other endpoints:

```bash
curl -s <INSTANCE_URL>/api/session/properties | grep -o '"tag":"[^"]*"'
```

This returns something like `"tag":"v1.52.0"`. Extract the major version number (e.g. `52` from `v1.52.0`).

- If the major version is **below 49**: tell the user the Embedding SDK requires Metabase 49 or later and stop.
- If it is **49 or above**: continue.

Fetch the versioned documentation index for use in the remaining steps:

```bash
curl -s https://www.metabase.com/docs/v0.<MAJOR>/llms.txt
```

Fall back to `https://www.metabase.com/docs/latest/llms.txt` if the versioned URL returns empty. Keep this document in context — it contains the correct auth config shapes, SDK install commands, and any deprecations for this version.

---

## Step 3 — Choose authentication mode

Ask the user:

> "How will this embedding be used?
>
> - **API key** — easiest to set up, good for development and internal tools
> - **JWT** — recommended for production apps where end users access the embed"

### If they choose API key

1. Use the Metabase MCP to check whether an embedding-specific API key already exists.
2. If one does not exist, guide the user to create one:
   - Via the Metabase admin UI: **Settings → Admin → API Keys → Create API key**
   - Or via the API (requires an existing admin API key):
     ```bash
     curl -s -X POST <INSTANCE_URL>/api/api-key \
       -H "Content-Type: application/json" \
       -H "x-api-key: <ADMIN_API_KEY>" \
       -d '{"name": "Embedding", "group_id": 1}'
     ```
3. Tell the user to save the returned key as `METABASE_API_KEY` in their project's `.env` or `.env.local` file, and confirm it is in `.gitignore`.

### If they choose JWT

Follow the auth setup instructions in the `llms.txt` fetched in Step 2 — the JWT implementation details (endpoint shape, token fields, signing approach) vary by version. In particular:

- Retrieve the JWT signing secret from Metabase: **Settings → Admin → Embedding → Embedding secret key**
- Tell the user to save it as `METABASE_JWT_SECRET` in their server-side environment only (never a browser-accessible env var)
- Ask which backend framework they are using (Next.js API route, Express, Fastify, etc.) and scaffold a minimal auth endpoint following the pattern in the `llms.txt`

---

## Step 4 — Install the SDK

Check whether `@metabase/embedding-sdk-react` is already in the user's `package.json`.

- If not installed: use the install command from the `llms.txt` fetched in Step 2 (look for the SDK version compatibility section — the correct dist-tag matches the instance major version).
- If already installed: verify the major version matches the instance major. Warn the user if there is a mismatch and offer to update.

---

## Step 5 — Done

Tell the user setup is complete. Summarize:

- Instance URL and version confirmed
- Auth mode chosen (API key / JWT) and where credentials are stored
- SDK version installed

Stop here. Do not generate any React component code, Quick Reference snippets, MetabaseProvider examples, or any other code beyond what was already shown for auth and SDK installation. Simply tell the user setup is complete and suggest they use the `metabase-react-sdk-docs` skill for their next task.
