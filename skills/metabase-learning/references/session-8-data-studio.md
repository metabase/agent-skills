# Session 8: Data Studio — Reference File

## Key Concepts to Teach

### 1. What Data Studio Is
- Data Studio is an analyst workbench inside Metabase: a dedicated space with tools to
  *shape* your data and *curate* your semantic layer, so everyone can trust the numbers.
- It's not a separate product — it's a section of Metabase you open from the **grid icon**
  in the upper right → **Data Studio**.
- Access is restricted: only people in the **Admin** group or the special **Data Analysts**
  group get the keys. Regular viewers don't see it. (As of Metabase 65, the Data Analysts
  group only appears on plans that include it, or if it already has members.)
- Mental-model placement: Data Studio sits *below* the Questions layer. Everything earlier
  in the curriculum (Questions, Visualizations, Dashboards) consumes data. Data Studio is
  where you *prepare and describe* that data before anyone queries it.

### 2. What's Inside Data Studio
Data Studio's tools group loosely into "shape your data" and "describe/track your data."
Metabase 64 renamed several of them; learners on older versions may see the old names.

| Tool (Metabase 64 name) | Older name | What it does | Shape or describe? |
|------|------|--------------|--------------------|
| Data transformation | Transforms | Clean, join, and pre-compute data, writing results back to your database | Shape |
| Semantic layer | Library | A curated home for your most-trusted tables, metrics, and SQL snippets | Describe |
| Connected data | Tables | Edit table metadata so tables are easier to work with | Describe |
| Glossary | — | Define business terms for both people and AI agents | Describe |
| Dependency graph | — | A visual map of how content connects | Track |

**Dependency diagnostics** (surfacing broken or unused items) moved out of Data Studio in
Metabase 64, into the new **Monitor** area (grid icon → Monitor).

(The semantic layer, dependency graph, and dependency diagnostics are Pro/Enterprise
features.)

### 3. Transforms — the Heart of Data Studio
- A transform does the **"T" in ETL** (Extract, **Transform**, Load) *inside* Metabase.
- You write a query or a script; the transform runs it, **creates a new table in your
  target database** with the results, and syncs that table back into Metabase so it can be
  a data source for questions or even other transforms.
- Two flavors:
  - **Query-based transforms** — written in the query builder *or* SQL. They run in your
    database.
  - **Python transforms** — written in Python, run in a dedicated execution environment.
- **Incremental transforms**: mark a transform as incremental and Metabase only writes
  *new* data to the target table instead of rebuilding it every run.
- **Lookback window** (Metabase 64): incremental transforms normally only process rows
  newer than their last checkpoint, so late-arriving rows get missed. A lookback window
  re-processes a slice of already-seen data to catch them. Set it in the transform's
  **Settings**.
- **Jobs** run one or more transforms on a schedule, selected by transform **tags**.
- **Re-run the DAG** (Metabase 64): click the arrow next to **Run** on a transform to also
  rerun everything upstream or downstream of it in one go.
- **Index manager** (Metabase 64): create and maintain indexes on transform-created tables
  from the transform's **Indexes** tab, to speed up common queries against them.
- **Transform tests** (Metabase 65, Pro): give a transform fixed input rows, then check its
  output against exact expected rows or a check query that should return nothing. Tests run
  in temporary tables that roll back afterward, and sync to Git with the transform. Open a
  transform and go to its **Tests** tab; tests can also be written with the Metabase CLI or
  a coding agent.
- Admins can **disable transforms** entirely in Data Studio settings, to avoid unexpected
  warehouse charges.
- **Metabot no longer generates transforms** as of Metabase 64. Metabase has said a new way
  to generate them with AI is coming.

### 4. Transforms vs Models (important distinction)
This is the concept most likely to trip up someone who finished Session 6.
- A **model** (Session 6) is a saved, virtual layer over a question. The transformed data
  is computed *on the fly* every time someone queries it — nothing new is written to your
  warehouse.
- A **transform** physically **materializes a new table** in your database. The work is
  done once, on a schedule, and stored.
- Rule of thumb: reach for a model to clean up and rename for reuse; reach for a transform
  when the computation is expensive and you want it pre-computed and stored (e.g.
  pre-joining Orders, Products, and People into one wide reporting table refreshed nightly).

### 5. The Semantic Layer (formerly the Library)
- The **semantic layer** is a curated space for the organization's most trusted analytics
  content — the tables, metrics, and SQL snippets the data team recommends people start
  from. The curated content itself is often still called the **Library**: it shows up as
  the Library section of the main sidebar, and Data Studio labels its home "Semantic layer."
- As of Metabase 65, **dashboards** can be published to the Library too, alongside tables
  and metrics. Curators manage them in a **Dashboards** section of the semantic layer, and
  SQL snippets and data actions get their own tabs.
- Together with **Connected data** (table metadata) and the **Glossary**, it makes up the
  human-friendly description of what your data *means*, layered on
  top of the raw tables.
- The semantic layer pays off twice: people find trustworthy starting points, and AI
  features (Metabot, the MCP server — Session 9) get accurate grounding instead of guessing.

### 6. Glossary
- Define terms specific to your business — what "active account," "churn," or "MQL" means.
- The glossary serves *both* humans browsing data *and* AI agents trying to interpret a
  natural-language question correctly. A good glossary entry is one of the highest-leverage
  things you can do to make Metabot answer reliably.
- As of Metabase 64, external AI clients can read it too, through the MCP server's
  `glossary` tool, so they look up your definition of "churn" instead of guessing from the
  word.

### 7. Dependency Graph and Diagnostics
- The **dependency graph** is a visual map of how your content connects — which questions
  feed which dashboards, which transforms feed which tables.
- Use it to understand the **blast radius of a change** *before* you make it. ("If I rename
  this column, what breaks?")
- **Dependency diagnostics** flag items with broken dependencies, or content that isn't
  used by anything — useful for cleanup. Since Metabase 64 they live in **Monitor**, not
  Data Studio. Metabase 65 adds **Content diagnostics** there too: nightly scans for stale,
  duplicate, and slow content that admins can clear in bulk (Pro).

### 8. Permissions
- To *see* the transforms list, a person must be able to access Data Studio: Admin or the
  **Data Analysts** group.
- To *execute* transforms against a database, they additionally need **Transform
  permissions** for that database.
- Transforms write to your database, so the underlying database connection must be
  **writeable**.

---

## Active Recall Questions

**Q1.** What does a transform actually *do* to your database, and how is that different from
a model?
> **A:** A transform runs a query or script and writes the results as a new physical table
> in your database (then syncs it back into Metabase). A model is virtual — it's a saved
> question that recomputes on the fly and stores nothing new. Transforms materialize;
> models don't.

**Q2.** You want a nightly-refreshed table that pre-joins Orders, Products, and People into
one wide reporting table. Model or transform? Why?
> **A:** A transform — ideally an incremental one on a scheduled job. The join is expensive
> and you want it pre-computed and stored so dashboards read from a ready-made table rather
> than re-joining every load. A model would re-run the join on every query.

**Q3.** Name the two types of transforms and where each one runs.
> **A:** Query-based transforms (written in the query builder or SQL) run in your database.
> Python transforms (written in Python) run in a dedicated execution environment.

**Q4.** Who can get into Data Studio, and what extra permission is needed to actually run a
transform against a specific database?
> **A:** Admins and members of the Data Analysts group can access Data Studio. To execute
> transforms on a database, a person also needs Transform permissions for that database.

**Q5.** What is the Glossary for, and why does it matter beyond just helping people?
> **A:** It defines business-specific terms. It helps people understand the data, and it
> also grounds AI agents (like Metabot and MCP clients) so they interpret natural-language
> questions correctly instead of guessing.

**Q6.** You're about to rename a column that several questions and dashboards might depend
on. Which Data Studio tool helps you avoid breaking things, and how?
> **A:** The dependency graph — it visually maps how content connects, so you can see the
> blast radius of the change before you make it. Dependency diagnostics would then flag
> anything that did break or went unused.

**Q7.** An incremental transform runs nightly, but some orders arrive a day late and never
show up in the output table. What Metabase 64 setting fixes this?
> **A:** A lookback window. It makes the incremental transform re-process a slice of data
> behind its checkpoint, so late-arriving rows get picked up.

**Q8.** A teammate edits a transform and accidentally drops every refund from the output.
What Metabase 65 feature would have caught this before it shipped?
> **A:** Transform tests. Give the transform sample input that includes a refund and check
> that the refund appears in the output (or write a check query that should return no rows
> if refunds are missing).

---

## Common Gotchas
- **Transforms need a writeable database connection.** They create tables in your database;
  a read-only connection can't do that.
- **Materialized, not live.** A transform's output table is only as fresh as its last run.
  If numbers look stale, check the job schedule — it's not recomputing on every query the
  way a model does.
- **Data Studio is gated.** Most learners who only *use* Metabase won't see it at all; it's
  for Admins and the Data Analysts group. Some pieces (semantic layer, dependency graph and
  diagnostics) are Pro/Enterprise.
- **Names keep shifting.** Metabase 64 renamed "Library" to "Semantic layer" and
  "Transforms" to "Data transformation," but Metabase 65's own announcement still uses
  "Library" and "Transforms" in places. If a learner's menus don't match, check with the
  MCP `learn` tool or ask which version they're on.
- **Don't confuse a transform's output table with a "model."** Both give you cleaner data
  to build on, but one writes to your warehouse and one doesn't.
