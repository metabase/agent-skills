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
- Answer data questions asked in plain English (**AI exploration**). As of Metabase 65,
  Metabot reads the query results and answers with the number itself ("ARR month-to-date
  is…"), not just a chart. See the privacy note in section 4.
- Create a chart by building a query in the **query builder** from a natural-language prompt.
- Generate **SQL** in the native editor from natural language (currently SQL only).
- **Fix errors** in SQL — the "Have Metabot fix it" button on a query error.
- **Inline SQL editing** — generate or edit SQL right in the editor.
- **Analyze a chart** — explain what a visualization shows.
- Create charts in **documents**, including **treemaps** and **box plots** when the data
  suits them.
- Answer questions from **Slack**.
- As of Metabase 64, Metabot no longer generates **transforms** (Session 8). Metabase has
  said a new way to generate transforms with AI is coming.
- Universal caveat: like all generative AI, **always double-check the results.**

### 3. How to Invoke Metabot
- **Chat sidebar**: `Cmd+E` (Mac) / `Ctrl+E` (Windows), or click the Metabot icon top-right.
- **Inline SQL editing**: `Cmd+Shift+I` / `Ctrl+Shift+I` in the SQL editor — enter the
  tables, describe the query or edit, accept or reject.
- **AI exploration**: **+ New → AI exploration** to start fresh with no existing question.
- **Research** (Metabase 65): **+ New → AI exploration → Research**, or search the command
  palette for "New research." Metabot picks relevant metrics, dimensions, and timelines,
  runs each metric across the dimensions, and ranks what it finds by how interesting it is.
  You can star results, comment on them, and curate them into a summary to share.
  Available on all plans, including open source.
- **Analyze a chart**: open a question and click the Metabot icon in the upper right.

### 3a. Working With Metabot Conversations (Metabase 64+)
- **Conversation history**: conversations save automatically. To pick one back up, open
  the Metabot sidebar and click the **Clock** icon. For AI explorations, go to
  **+ New → AI exploration** and click the **Clock** icon in the top right.
- **Fork a conversation** to try a different direction while keeping the original intact.
- **Reasoning**: on models that support it, Metabot shows how it reasoned toward an answer.
  Useful for spotting where it went wrong.
- **Save and Copy** buttons on inline charts in AI exploration let you paste a chart
  straight into a collection, document, or dashboard.
- Metabot **warns you** when a conversation nears its context limit, or when a response is
  cut off, and lets you continue.
- Admins can now connect **multiple AI providers** at once (Admin > AI > AI settings).
  Metabase 65 added Ollama, xAI, and Google Cloud Model Garden, and self-hosted Metabase
  can run Metabot on a self-hosted model (vLLM or Ollama).
- Metabot now explains **why a reply stopped** (for example, the provider hit a rate limit
  or ran out of credits) instead of a generic error.

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
- **What gets sent to the AI provider.** As of Metabase 65, Metabot reads query results by
  default, so result rows go to the AI provider your admin connected (always run with the
  asking user's own permissions). Admins can turn this off under **Admin > AI > Metabot
  settings → Allow Metabot to read query results**. Worth knowing before pointing Metabot
  at sensitive data.

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
- An admin enables it under **Admin > AI > MCP** with the **MCP server** toggle. AI features
  must be on, but no AI provider needs to be configured, since the client supplies the
  model. Per-client toggles (Claude, Cursor/VS Code, ChatGPT) and a custom-origin field
  control which clients can render inline charts.
- Clients point at `https://{your-metabase}/api/metabase-mcp`. Admins can copy the URL
  from **Admin > AI > MCP > Settings**.
- **Upgrading from an older version:** clients connected before Metabase 64 have to sign
  in again; the older `/api/mcp` connector should be removed and added again at the new URL.
- Auth is **OAuth 2.0** through Metabase's own embedded OAuth server. The first connection
  opens a Metabase consent page. The MCP endpoint doesn't accept Metabase session cookies or
  API keys. For headless use (a backend service, not a person), Pro and Enterprise can
  exchange a signed JWT for an MCP token.
- **Per-group tool access** (Metabase 65, Pro/Enterprise): admins choose which MCP tools
  each group can use under **Admin > AI > Usage controls > MCP tools access**. For example,
  a Viewers group could get search and read tools but not SQL or delivery tools. This sits
  on top of scopes and permissions: a tool has to be allowed for your group *and* granted
  on the consent page.

### 8. Scopes: What the Connection Is Allowed to Do
The consent page lists **scopes**, with a checkbox for each, so you grant only what you
choose:

| Scope | Lets the AI client… |
|---|---|
| `agent:content:read` | View content and data structure |
| `agent:content:write` | Create, edit, and trash content |
| `agent:query:run` | Run queries and see results |
| `agent:sql:run` | Write and run raw SQL |
| `agent:delivery:write` | Create alerts and subscriptions (also needs `agent:query:run`) |

Scopes **narrow** what the connection can do; they never grant more than your own Metabase
permissions. A connection with every scope still can't see data you can't see.

### 9. The Tools the MCP Server Exposes
The server builds on Metabase's **Agent API**. Tools fall into four groups (the server's
live tool list is authoritative; it changes between versions):

- **Find and read:** `search` (keyword and natural-language), `browse_collection`,
  `browse_data` (databases, tables, fields), `get_content` (questions, dashboards, metrics,
  documents, with layout, dimensions, and comments), `get_parameter_values`, `glossary`,
  `learn` (Metabase reference topics).
- **Query:** `execute_query` (structured queries), `execute_sql` (raw SQL),
  `run_saved_question`, plus `visualize_query` and `render_drill_through` for inline charts
  in clients that support them.
- **Create and edit:** `question_write`, `dashboard_write`, `document_write`,
  `metric_write`, `measure_write`, `segment_write`, `collection_write`,
  `duplicate_content`, `bookmark_content`.
- **Deliver:** `alert_write`, `subscription_write`.

Things worth knowing about how they behave:
- **No hard delete.** Content can only be archived (moved to trash). Alerts can be paused
  but not deleted or archived through MCP — you delete them in Metabase yourself.
- **Dry runs.** `execute_query`, `execute_sql`, and `dashboard_write` accept
  `validate_only`, which checks the request without running or saving it.
- **`execute_sql` can change data.** It runs whatever SQL it's given, so an UPDATE or
  DELETE really happens. This is why `agent:sql:run` is its own scope.
- **Row limits.** Queries return 100 rows by default, up to 2,000.
- **Monitoring.** On Pro and Enterprise, admins can see MCP usage, clients, and errors in
  **Monitor > AI Auditing > MCP analytics**.
- **Data apps (beta, Metabase 65).** Using the MCP server and the Metabase CLI, a coding
  agent like Claude Code can build custom React apps, internal tools, and forms on top of
  your semantic layer, with optional write-back to your database. Apps live in your Remote
  sync Git repository, show up under **Data apps** in the sidebar, and admins pick which
  groups can use each one. Pro/Enterprise, and needs Remote sync and a Library.

You can also use the MCP server for **agent-driven development**: pointing an agent at real
schema metadata so it writes questions and dashboards against real columns.

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

**Q8.** You're connecting Claude to Metabase and only want it to read dashboards, never
run SQL or create alerts. What do you do on the consent page?
> **A:** Grant only the scopes you want — `agent:content:read` (and `agent:query:run` if it
> should run queries) — and leave `agent:sql:run` and `agent:delivery:write` unchecked.

**Q9.** An AI client created a practice dashboard and an alert in your Metabase. How do you
get rid of each?
> **A:** The dashboard can be archived (moved to trash) — there's no hard delete through
> MCP. The alert can only be paused through MCP; to remove it, delete it yourself in
> Metabase.

**Q10.** You had a useful Metabot conversation yesterday. How do you pick it back up?
> **A:** Open the Metabot sidebar and click the Clock icon to see recent conversations.
> (For AI explorations: + New → AI exploration, then the Clock icon in the top right.)

**Q11.** Your finance team is nervous about Metabot. In Metabase 65, what happens to query
results when someone asks Metabot a question, and what can an admin do about it?
> **A:** Metabot reads the results by default, so result rows are sent to the connected AI
> provider (with the asking user's own permissions applied). An admin can turn that off in
> Admin > AI > Metabot settings with "Allow Metabot to read query results."

**Q12.** An admin wants analysts to use `execute_sql` through MCP, but wants everyone else
limited to searching and reading. Where do they set that up?
> **A:** Admin > AI > Usage controls > MCP tools access (Pro/Enterprise), which controls
> which MCP tools each group can use.

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
- **Old connectors break after upgrading.** If an MCP client stops working after moving
  to Metabase 64, sign in again or re-add it at `/api/metabase-mcp`.
- **Scopes are your safety rail, permissions are the ceiling.** Most clients request every
  scope by default. Uncheck what you don't need.
- **"Why can't my AI client see that tool?"** In Metabase 65, an admin may have limited
  the MCP tools available to your group. Check with them, or look at the consent page
  scopes.
- **Metabot isn't just reading metadata anymore.** It reads query results by default as of
  Metabase 65, so data goes to the AI provider unless an admin turns that off.
- **Inline charts depend on the client.** Claude Code doesn't show `visualize_query`, and
  Claude Desktop shows inline charts in Chat but not Cowork.
