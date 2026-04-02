---
name: metabase-embed-dashboard
description: Generates ready-to-use React components that embed Metabase dashboards using the Embedding SDK. Accepts a natural-language description of the dashboards needed, finds or creates them in Metabase, and outputs working component code.
---

Use this skill when the user describes dashboards they want to embed (e.g. "embed a sales overview and a user growth chart"). The skill finds or creates those dashboards in Metabase and generates the corresponding React components.

---

## Step 1 — Get the Metabase instance URL and fetch version-aware docs

If the instance URL is already known from context (e.g. the user provided it earlier in the conversation), use it. Otherwise, ask: "What is your Metabase instance URL?"

Run this command to detect the Metabase major version:

```bash
curl -s <INSTANCE_URL>/api/session/properties | grep -o '"tag":"[^"]*"'
```

Extract the major version number from the tag (e.g. `v1.60.3` → `60`).

Fetch the versioned documentation index:

```bash
curl -s https://www.metabase.com/docs/v0.<MAJOR>/llms.txt
```

Fall back to `https://www.metabase.com/docs/latest/llms.txt` if the versioned URL returns empty.

**Read the fetched document carefully.** It contains:

- Critical deprecations and breaking changes for the detected version
- The correct prop names and API shapes for `MetabaseProvider` and dashboard components (these change between major versions — do not rely on training data)
- A Table of Contents with links to raw GitHub markdown pages for deeper reference

If you need detail on a specific topic (e.g. authentication, a specific component), fetch the relevant page from the Table of Contents in that document. Do not fetch `llms-embedding-full.txt` unless the user explicitly asks — it is the entire docs concatenated and will consume excessive context.

---

## Step 2 — Understand what the user wants

Ask the user (or infer from their prompt) which dashboards they need embedded. For each, collect:

- A plain-language description (e.g. "sales overview", "user growth", "top products")
- Whether it should be **static** (read-only) or **interactive** (users can filter and explore)
- Any specific filters or parameters to pre-apply (optional)

---

## Step 3 — Find or create dashboards in Metabase

Use the Metabase MCP tools to search for existing dashboards that match the descriptions.

For each requested dashboard:

1. Call the MCP `search` tool (or equivalent) with the description as the query, filtering for `type: dashboard`.
2. If a matching dashboard is found: note its numeric `id`.
3. If no matching dashboard is found:
   - Ask the user: "I couldn't find a dashboard for '[description]'. Would you like me to create one, or do you have an existing dashboard ID?"
   - If they want one created: use the MCP to create a new dashboard with an appropriate name, then guide the user to add questions/cards to it inside Metabase.
   - If they provide an ID: use that.

---

## Step 4 — Determine auth config

Read the auth mode from the user's project context:

- If `METABASE_API_KEY` is referenced anywhere in their env files or existing code → API key auth.
- If a JWT auth endpoint exists → JWT auth.
- If unclear, ask the user: "Are you using API key auth or JWT auth for embedding?"

If auth is not yet set up at all, suggest running the `metabase-embedding-setup` skill first.

---

## Step 5 — Generate React components

For each dashboard, generate a self-contained React component. Use **only** the SDK documentation fetched in Step 1 as the reference for prop names, auth config shape, and component APIs — these change between major versions and your training data may be stale.

Key conventions that are stable across versions:

- Import from `@metabase/embedding-sdk-react`
- Use `StaticDashboard` for read-only embeds; `InteractiveDashboard` when users need to filter and explore
- `dashboardId` must be a number (integer), not a string — `parseInt` if sourced from a URL param
- Never hardcode credentials — read from environment variables
- Prefix browser-visible env vars per the user's framework convention (`NEXT_PUBLIC_` for Next.js, `VITE_` for Vite)

**Naming**: derive the component name from the dashboard description in PascalCase (e.g. "sales overview" → `SalesOverviewDashboard`).

**MetabaseProvider placement**: if the user is embedding multiple dashboards in the same app, generate a single shared provider component and have each dashboard component consume it, rather than repeating the provider in every file.

---

## Step 6 — Insert components into the project

1. Determine a sensible file location in the user's project (e.g. `src/components/analytics/`, `components/dashboards/`). Ask if unsure.
2. Write each component to its own file, named in kebab-case matching the component name (e.g. `SalesOverviewDashboard.tsx` → `sales-overview-dashboard.tsx`).
3. If a shared provider was generated, write it to `src/components/analytics/MetabaseEmbedProvider.tsx` (or equivalent).

---

## Step 7 — Usage summary

After inserting the files, show the user a brief usage example:

```tsx
import { SalesOverviewDashboard } from "@/components/analytics/sales-overview-dashboard";

export default function AnalyticsPage() {
  return (
    <main>
      <SalesOverviewDashboard />
    </main>
  );
}
```

Remind the user to:

- Add the required environment variables (instance URL, API key or JWT secret) to their `.env.local`. Never commit these to source control.
- Restart their dev server after updating env vars.
- Install the SDK if not yet done — the correct install command for this version is in the `llms.txt` fetched in Step 1.
