# The build plan

Read before writing or reading a build plan: where it lives, its sections, the entry format, status and severity, and how people answer it. The plan is the one deliverable outside `./.scratch`: written for people across the company (finance, product, data, security), forwarded and edited by them, and read back by the agent. STATE.md stays the agent's execution record ([state.md](state.md)); when STATE.md names a plan, every decision lives in the plan.

## Where it lives

`./plans/<dataset>-plan.md`, one per source system or migrated project (`plans/stripe-plan.md`, `plans/looker-migration-plan.md`), named so it still makes sense once forwarded; another plan is cited by file and id ("stripe-plan D4"). STATE.md `plan:` names it. The agent writes it and never commits or pushes it; sharing it is the user's. When the working directory is the remote-sync repository ([remote-sync.md](remote-sync.md)), confirm that import ignores a top-level `plans/` before writing there, and treat pushing it as a sync step. After every write the agent copies the plan to `./.scratch/<dataset>-plan.base.md`, so a returned plan can be compared with what the agent last wrote.

## What never goes in

Ids (database, collection, card, transform, user), profile names, URLs with tokens, credentials, and personal values from the data: an example names a record by its id, dates, and amounts, never a customer's name, email, phone, or address, and personal data appears as counts of columns and rows. Table and column names are fine. A filled plan from another business is a format, never a source of defaults.

## Sections

The header, then these sections in order; one that does not apply keeps its heading and says `Not applicable: <reason>`.

```markdown
# Stripe build plan
Draft 3 · approved by Jo (Data), 2026-10-02 · new source in an existing instance · Full: revenue data, read by finance
Waiting on: Finance 3, Product 1 · No default: D9 (blocks the retention table)
```

1. **Summary and purpose**: what will exist, for whom, the first question it answers; what the instance is for and how people read the numbers (SQL, the query builder, dashboards, customers in an app).
2. **Data handling**: the personal-data answer (columns and tables counted, who may see them, masked or counts only), the history-copies line, other sensitive fields.
3. **Sources**: tables in scope with rows and freshness, the source of truth per entity, what stays raw with its row count. A new source in an existing instance adds `Connections to existing data`: new table and column, existing table it joins, match rate, what happens to the unmatched.
4. **Shape**: the recommended shape in plain words, why, and what the alternative would cost; the inventory as entities, events, and rollups, each table as "one row per <thing>" with its key ([layering-and-naming.md](layering-and-naming.md)).
5. **Decisions**: entries waiting on someone, grouped by who usually answers (the part people forward); then decided entries, two lines each; then `Decided by the build`, one table row per routine reversible decision (decision, as built, evidence, affects).
6. **How we'll know it's right**: the reference and its grain; the validation mode in plain words ([reconciliation.md](reconciliation.md)): "matched to finance's export", "matches the old reports, which proves the move, not the numbers", or "self-consistent only"; the tolerance; the checks that fail the build.
7. **Migration** (a migration only): translate as it is or improve, the gap report's verdict counts, what changes on purpose and the number each change moves, what cannot come over and why, the cutover.
8. **Build order**: the named questions in the user's order, each with the tables it needs; the first is the first slice; what is not built now.
- **Change log**: dated lines, newest first: who answered or changed what, and what moved.
- **Words used here**: only when a reader outside data would stop at a term.

## Entries

One per decision, under an id only the agent mints (`D<n>`, one sequence per plan; an entry a person adds gets the next one). Labels are fixed so the plan reads back exactly:

```markdown
### D3 · Does a cancelled subscription still count in its last paid month?
**Proposed:** Yes, until its paid period ends.
**Example:** sub_4471 cancelled 30 July, paid through 31 August: counts in August.
**If the other way:** August churn goes from 41 to 48 accounts (+17%).
**Severity:** High · **Affects:** customer-month table, MRR and churn metrics, Revenue overview dashboard
**From:** lifted from code (fct_mrr.sql:42); profiled (214 subscriptions look like this)
**Usually answered by:** Finance · **Status:** PROVISIONAL, built on the default; waiting on Finance
**Answer:**
```

- The heading and `Proposed` are the decision; `If the other way` is its readings (both measured figures and the gap, `n/a` when no headline number depends on it); `Affects` names tables, metrics, and dashboards by their display names, existing ones from the dependents search in [semantic-layer-design.md](semantic-layer-design.md); `From` carries the specification's provenance tags (profiled, user-stated, lifted from code, defaulted) with the citation ([extraction-and-gap-report.md](extraction-and-gap-report.md)).
- `Usually answered by` (Data, Finance, Product, Security, Leadership) routes a question; it never asks who owns definitions ([collaboration-contract.md](collaboration-contract.md)). An entry the person in the session leaves for that role reads `Waiting on: Finance (default in use)`.
- A decided entry collapses to two lines: `### D1 · <decision as built> · decided, <name> (<role>), <date>`, then `<severity> · Affects: … · From: …`.

## Status and severity

`Status` opens with the keyword [state.md](state.md) defines, then a plain gloss: `decided` (who, when), `PROVISIONAL` (built on the default, waiting on someone), or `open`. An `open` entry names its kind: `default proposed`; `no default` (the value must come from the profile or a person, so it blocks the models it affects); `contradiction` (two sources disagree: both claims, citations, and dates shown); or `disputed` (two people disagree: the decided reading stands until answered).

| Severity | Means | Asked |
|---|---|---|
| High | irreversible (publishing, personal data, a definition already handed back), or its two readings differ beyond the materiality threshold on a headline number | in the gate's walk-through |
| Medium | material on one table, metric, or dashboard, or not yet measured on a column traced to a headline number | within the budget; else accepted from the memo |
| Low | below materiality | never: a `[DECIDED, reversible]` row in `Decided by the build` |

## How people answer

On the `Answer:` line, signed (`**Answer:** end of paid period — Priya, 2026-10-04`), in chat, or by sending the plan back. Anything else a person changes in the file is a proposed change, confirmed before it is used. A returned plan is read per [plan-the-build.md](../playbooks/plan-the-build.md), step 9; every answer and change lands in its entry and the change log in the response that receives it. A decision changed later, by a change request, a reconciliation finding, or a rule found mid-build, updates its entry and the change log the same way.

## Plain language

The contract's plain-language rules hold on every line ([collaboration-contract.md](collaboration-contract.md)): "one row per customer per month", never grain; a shape described by what a reader sees ("one table per real-world thing, linked by ids"); money decisions in dollars and months. Summary first, each decision a question about a record, nothing a reader must open SQL to follow.

Finished example, section 5 of a plan with one entry waiting and one decided (values illustrative):

```markdown
## 5. Decisions

### Waiting on Finance (1)

### D3 · Does a cancelled subscription still count in its last paid month?
(the entry above)

### Decided

### D1 · Annual invoices spread evenly over twelve months from the service start · decided, Priya (Finance), 2026-10-04
High · Affects: subscription-month table, MRR · From: user-stated

### Decided by the build
| decision | as built | evidence | affects |
|---|---|---|---|
| D12 line detail | invoice lines, not charges | lines cover 99.8% of invoices, charges 61% | every revenue table |
```
