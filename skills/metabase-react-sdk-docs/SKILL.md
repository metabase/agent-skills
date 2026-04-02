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

## Step 3 — Help the user

Use the fetched documentation as the authoritative reference for all SDK API shapes, component names, and auth configuration. Do not rely on training-data knowledge of the SDK — prop names and auth config have changed between major versions.

If the user's task is initial setup (installing the SDK, configuring auth), the `metabase-react-sdk-setup` skill covers those steps in detail.
