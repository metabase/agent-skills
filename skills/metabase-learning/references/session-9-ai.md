# Session 9: AI in Metabase — Metabot & the MCP Server — Reference File

## Key Concepts to Teach

### 1. Two Directions of AI in Metabase
There are two distinct ways AI shows up in Metabase, and the key is which way the
integration points:
- **Metabot** — Metabase's *built-in* AI assistant. The AI lives **inside** Metabase and
  helps you work *in* the app.
- **MCP server** — lets an **external** AI client (like Claude, Cursor, or ChatGPT) reach
  **into** your Metabase from outside.
Get this directionality straight first; everything else hangs off it.

### 2. What Metabot Can Do
Metabot helps you analyze data using natural language. A non-exhaustive list:
- Answer data questions asked in plain English (**AI exploration**).
- Create a chart by building a query in the **query builder** from a natural-language prompt.
- Generate **SQL** in the native editor from natural language (currently SQL only).
- **Fix errors** in SQL — the "Have Metabot fix it" button on a query error.
- **Inline SQL editing** — generate or edit SQL right in the editor.
- **Analyze a chart** — explain what a visualization shows.
- Generate **transforms** (ties back to Session 8) and charts in documents.
- Answer questions from **Slack**.
- Universal caveat: like all generative AI, **always double-check the results.**

### 3. How to Invoke Metabot
- **Chat sidebar**: `Cmd+E` (Mac) / `Ctrl+E` (Windows), or click the Metabot icon top-right.
- **Inline SQL editing**: `Cmd+Shift+I` / `Ctrl+Shift+I` in the SQL editor — enter the
  tables, describe the query or edit, accept or reject.
- **AI exploration**: **+ New → AI exploration** to start fresh with no existing question.
- **Analyze a chart**: open a question and click the Metabot icon in the upper right.

### 4. How Metabot Grounds Itself (and where it goes wrong)
- Metabot builds queries using your **semantic layer** — your models, metrics, and the
  **glossary** (Session 8). That's how it returns working SQL with real field names instead
  of hallucinated ones.
- When you ask it to create a chart, it first looks for an **existing question** that
  answers you and points you there before building something new.
- **The 100-table trap**: if you don't name a table, Metabot only checks the first ~100
  tables in the selected database. If your answer lives outside those, it may hallucinate
  table names and the query fails. Fix: name the table/fields in your prompt.
- It works most reliably in **English**, and benefits enormously from a well-maintained
  glossary.

### 5. Metabot's Current Limitations
Worth knowing so learners don't fight the tool:
- Can't generate SQL with **SQL variables / parameters** (filters, field filters).
- Can't add **goal lines** to charts.
- Can't change **chart formatting** (colors, axis labels, number formatting).
- Can't **modify or delete** existing alerts/subscriptions (Slack Metabot can create them).
- **Search scope**: it finds tables, metrics, questions, models, and dashboards — not
  segments, documents, collections, or actions on its own (though it can *use* segments and
  measures in ad-hoc queries).

### 6. The MCP Server — What and Why
- **MCP** = Model Context Protocol, an open standard for connecting AI clients to tools and
  data. Metabase ships an **MCP server** (over Streamable HTTP).
- It lets MCP-compatible AI clients connect **directly to your Metabase**, with everything
  **scoped to the connecting person's permissions** — the AI can't see more than that user
  could.
- Crucial distinction: **your client provides the AI**, not Metabase. If you ask your
  desktop AI app "what's our Q3 revenue," *your client* decides which MCP tools to call;
  Metabase just exposes the tools and runs them.
- Because the AI comes from your client, MCP calls **don't consume your Metabase AI
  provider's tokens** (the provider that powers Metabot is separate and untouched).

### 7. Connecting and Securing the MCP Server
- An admin enables it under **Admin > AI > MCP**: a master toggle, plus per-client toggles
  for **Claude, Cursor/VS Code, and ChatGPT** (toggling a client adds its sandbox domains
  to the CORS allowlist). Self-hosted clients can be added via **Custom MCP client domains**.
- Clients point at the endpoint `https://{your-metabase}/api/mcp`.
- Auth is **OAuth 2.0** — Metabase runs its own embedded OAuth server, so there's a
  Metabase-branded consent screen and no external OAuth provider to set up.

### 8. The Tools the MCP Server Exposes
The server builds on Metabase's **Agent API** and exposes tools your AI client can call:
- **search** — find tables and metrics by keyword or natural language.
- **get_table** / **get_table_field_values** — table details, fields, related tables,
  metrics, and sample field values.
- **get_metric** / **get_metric_field_values** — metric details and sample values.
- **construct_query** → **execute_query** — build a query (returns an opaque query string),
  then run it.
- **query** — query a table or metric and return results in one step.
- **create_question**, **create_dashboard** — create content.
You can also use the MCP server for **file-based development**: pointing an agent at real
schema metadata so it writes questions/dashboards (as serialized YAML) against real columns.

---

## Active Recall Questions

**Q1.** Metabot and the MCP server both involve AI. In one sentence each, how do they differ
in *direction*?
> **A:** Metabot is AI built *into* Metabase that helps you work inside the app; the MCP
> server lets an external AI client reach *into* Metabase from outside.

**Q2.** With the MCP server, where does the actual AI model come from — Metabase, or your
client? Why does that matter for token usage?
> **A:** From your client (Claude, Cursor, ChatGPT, etc.), not Metabase. So MCP requests
> don't consume tokens from the AI provider configured in Metabase for Metabot — the two
> are independent.

**Q3.** You ask Metabot to write a query but don't mention a table, and it invents a table
that doesn't exist. What likely happened, and how do you prevent it?
> **A:** When no table is named, Metabot only checks the first ~100 tables in the selected
> database; if your answer lives outside that set it can hallucinate. Prevent it by naming
> the table and fields in your prompt.

**Q4.** Name two things Metabot currently *can't* do.
> **A:** Any two of: generate SQL with variables/parameters, add goal lines, change chart
> formatting (colors/axis/number format), or modify/delete existing alerts and
> subscriptions.

**Q5.** A teammate connects Claude to your Metabase via MCP. Can they query data they don't
have permission to see in Metabase?
> **A:** No. MCP access is scoped to the connecting person's own Metabase permissions — the
> AI can't reach anything that user couldn't reach directly.

**Q6.** What makes Metabot's generated SQL use real column names instead of guessing, and
how does Session 8 help?
> **A:** It grounds queries in the semantic layer — models, metrics, and especially the
> glossary. Curating those in Data Studio (Session 8) directly improves Metabot's accuracy.

**Q7.** Which keyboard shortcut opens the Metabot chat sidebar, and which one triggers
inline SQL editing?
> **A:** `Cmd/Ctrl+E` opens the chat sidebar; `Cmd/Ctrl+Shift+I` triggers inline SQL
> editing in the native editor.

---

## Common Gotchas
- **AI isn't deterministic.** The same prompt can give different answers on a re-run, and
  results can be wrong — always verify before trusting or sharing.
- **The 100-table limit** is the most common cause of hallucinated queries. Name your
  tables.
- **English works best.** Metabot may understand other languages but is most reliable in
  English.
- **MCP ≠ Metabot's AI.** The MCP server doesn't use Metabase's configured AI provider; the
  intelligence comes from whatever client connects. You don't even need an AI provider
  configured in Metabase to use the MCP server.
- **A good glossary is the cheapest accuracy win.** Vague or missing business-term
  definitions are a top reason AI features misinterpret questions.
- **Permissions still apply.** MCP and Metabot both respect the user's existing
  permissions — AI is not a back door around data access controls.
