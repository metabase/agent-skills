---
name: metabase-react-sdk-docs
description: Loads version-accurate Metabase React SDK documentation and helps with any embedding task — components, auth, theming, plugins, etc.
---

Use this skill for any task involving `@metabase/embedding-sdk-react`. Fetches version-accurate docs and works from those as the source of truth.

## Step 1 — Get the Metabase instance URL

Use it from context if known, otherwise ask.

## Step 2 — Detect version and fetch docs

```bash
curl -s <INSTANCE_URL>/api/session/properties | grep -o '"tag":"[^"]*"'
```

Parse both the **edition** and the **major version** from the tag:

| Tag format | Edition | Example |
|------------|---------|---------|
| `v0.X.Y`   | OSS (Community) | `v0.60.1` → major `60`, OSS |
| `v1.X.Y`   | Enterprise (EE) | `v1.60.1` → major `60`, EE |

**If the tag starts with `v1.`, the instance is Enterprise Edition — use full JWT SSO embedding.** Do not fall back to guest embedding or any OSS-only auth path.

Extract just the major version number (e.g. `v1.60.3` → `60`), then fetch the versioned docs index:

```bash
curl -s https://www.metabase.com/docs/v0.<MAJOR>/llms.txt
```

Fall back to `https://www.metabase.com/docs/latest/llms.txt` if empty. **Read this before anything else** — it contains correct prop names, auth config shapes, and breaking changes for this version. Do not fetch `llms-embedding-full.txt` (too large).

## Step 3 — Discover existing dashboards (optional)

Look for `.env.metabase` in the project root. If it exists, source and search without reading its contents into context:

```bash
source .env.metabase 2>/dev/null && \
  curl -s "$METABASE_INSTANCE_URL/api/search?models=dashboard&archived=false" \
    -H "X-API-Key: $METABASE_ADMIN_API_KEY"
```

If the file doesn't exist, create it, gitignore it, and ask the user to fill in `METABASE_ADMIN_API_KEY`:

```bash
echo '.env.metabase' >> .gitignore
printf 'METABASE_INSTANCE_URL=http://localhost:3000\nMETABASE_ADMIN_API_KEY=\n' > .env.metabase
```

> "Fill in `METABASE_ADMIN_API_KEY` in `.env.metabase` — create a key at `<INSTANCE_URL>/admin/settings/authentication/api-keys` — or press Enter to skip."

If dashboards are found, share a brief summary and use the IDs in all generated code. **Skip silently on any failure or skip.**

## Step 4 — Help the user

Use `llms.txt` as the authoritative reference for all API shapes. **Write files directly into the user's project** using patterns from `llms.txt` — edit existing files in place rather than creating new ones alongside them.

### Code conventions (override anything in the docs)

- **JWT SSO only**: API keys grant admin-level access and are not safe for end-user embeds. Use a server-side JWT signing endpoint; `MetabaseProvider` receives its URL. Never generate `apiKey`, `METABASE_API_KEY`, `api-key`, or `x-api-key` — not even as a placeholder. Deviate only if the user explicitly asks and acknowledges the security risk.
- **Instance URL from env**: `VITE_METABASE_URL` (Vite), `NEXT_PUBLIC_METABASE_URL` (Next.js), etc. Never hardcode.
- **Secrets server-side only**: JWT secrets must never appear in browser-accessible env vars or frontend code.

For initial setup (JWT config, SDK install), use the `metabase-react-sdk-setup` skill instead.
