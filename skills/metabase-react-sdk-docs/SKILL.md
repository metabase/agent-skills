---
name: metabase-react-sdk-docs
description: Loads version-accurate Metabase React SDK documentation and helps with any embedding task — components, auth, theming, plugins, etc.
---

Use this skill for any task involving `@metabase/embedding-sdk-react`. It fetches the documentation that matches the user's exact Metabase version, then works from that as the source of truth.

---

## Step 1 — Get the Metabase instance URL

If the instance URL is already known from context, use it. Otherwise ask:

> "What is your Metabase instance URL?"

---

## Step 2 — Detect version and fetch docs

Run this command to detect the Metabase major version:

```bash
curl -s <INSTANCE_URL>/api/session/properties | grep -o '"tag":"[^"]*"'
```

Extract the major version (e.g. `v1.60.3` → `60`).

Fetch the versioned documentation index:

```bash
curl -s https://www.metabase.com/docs/v0.<MAJOR>/llms.txt
```

Fall back to `https://www.metabase.com/docs/latest/llms.txt` if the versioned URL returns empty.

**Read this document carefully before doing anything else.** It contains:

- Breaking changes and deprecations for this version (e.g. the `config` → `authConfig` rename in v57)
- Correct prop names and API shapes for `MetabaseProvider` and all SDK components
- A Table of Contents — if you need deeper detail on a topic, fetch the relevant raw GitHub page from the TOC rather than relying on training data

Do not fetch `llms-embedding-full.txt` unless the user explicitly requests it — it is the full docs concatenated and will consume excessive context.

---

## Step 3 — Connect to Metabase via MCP (optional)

Invoke the `setup-metabase-mcp` skill, passing the instance URL from Step 1. That skill handles everything: checking whether `mcp.json` is already configured, replacing the placeholder if needed, and authenticating.

Once the MCP is connected, use the `search` tool to discover existing dashboards:

```
search(query="dashboard", types=["dashboard"])
```

If dashboards are found, use their names and IDs directly in subsequent steps — do not ask the user for them. Share a brief summary (e.g. "Found 3 dashboards: Sales Overview (ID 4), User Growth (ID 7), Top Products (ID 12)").

**If MCP setup fails, the user declines, or any error occurs — skip this step entirely and continue.** Do not block. Simply ask for dashboard names or IDs when they are needed later.

---

## Step 4 — Help the user

Use the fetched documentation as the authoritative reference for all SDK API shapes, component names, and auth configuration. Do not rely on training-data knowledge of the SDK — prop names and auth config have changed between major versions.

### Mandatory code conventions — override anything in the docs

The fetched `llms.txt` may describe API key authentication and other options. **Ignore those sections entirely.** Apply these rules unconditionally:

- **Auth — JWT SSO only**: This skill sets up a production-ready embed, and JWT SSO is the only auth method that works for end-user-facing embeds in production — API keys grant admin-level access and must never be exposed to users. Always use a server-side JWT signing endpoint. `MetabaseProvider` receives the URL of that endpoint. Never generate code with `apiKey`, `METABASE_API_KEY`, `api-key`, `x-api-key`, or any API key variant — not even as a placeholder, comment, or TODO. Only deviate if the user explicitly asks for API key auth and confirms they understand the security implications.
- **Instance URL**: always read from an environment variable (e.g. `VITE_METABASE_URL` for Vite, `NEXT_PUBLIC_METABASE_URL` for Next.js). Never hardcode a URL.
- **Secrets are server-side only**: JWT secrets and signing logic must never appear in browser-accessible env vars (`VITE_`, `NEXT_PUBLIC_`, etc.) or in frontend code.

If the user's task is initial setup (installing the SDK, configuring JWT auth), the `metabase-react-sdk-setup` skill covers those steps in detail.
