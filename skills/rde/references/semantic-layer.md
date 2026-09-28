# Semantic layer

Which kind of definition a number needs, the bodies, the metadata pass, descriptions, verification, the Library, and ownership. Extend an existing definition by id, never a parallel one; two questions that disagree about one number are reconciled (`playbooks/reconcile.md`), not joined by a third.

## Which kind

| Kind | Stands for |
| --- | --- |
| Metric | the published number: one aggregation on a final table, at most one breakout (its default time dimension) |
| Measure | a formula two or more metrics share, once, on one table |
| Segment | a reused population people name ("Paying accounts") |
| Transform | a join people start from, a calculated column, a definitional flag; built before the metric reads it |
| Model | only where models already are the company's curated layer; metrics on it, and a measure it would need becomes a transform |

- No definitional filter hidden in a metric: it collides with filters people add. Compute the flag (in scope, recognised, not test) in the transform, then keep only in-scope rows in the final table or aggregate conditionally (`sum-where`, `count-where`, `distinct-where`).
- Slice by plain columns and segments; a breakout crosses a metadata foreign key with no join: `["field", {"source-field": <fk-field-id>}, <target-field-id>]`.
- Measures and segments work only on questions querying their own table directly, never across a join, a nested question, or a model; a definition needing two tables' columns means widening the table in a transform first.
- One starting object per table: the curated table itself, plumbing hidden, columns described; no model over it (measures and segments do not show on a model).

## Bodies

Ids come from the instance (`mb table get <id> --include fields` for fields; create output for definitions). MBQL 5; read the `mbql` skill before the first body. Dry-run every body; for definition references follow `SKILL.md`, mb conventions.

```json
{"name": "Revenue", "description": "<what it sums and excludes; owner>", "table_id": <table-id>,
 "definition": {"lib/type": "mbql/query", "database": <db-id>, "stages": [{"lib/type": "mbql.stage/mbql", "source-table": <table-id>,
   "aggregation": [["sum", {"name": "revenue_usd"}, ["field", {}, <revenue_usd-field-id>]]]}]}}
```

That is a measure (`mb measure create`); a segment has `"filters": [[…]]` and no aggregation (`mb segment create`). A metric is a card (`mb card create`):

```json
{"name": "Monthly recurring revenue", "type": "metric", "collection_id": <definitions-or-library-metrics-id>, "description": "<see Describe>",
 "display": "line", "visualization_settings": {},
 "dataset_query": {"lib/type": "mbql/query", "database": <db-id>, "stages": [{"lib/type": "mbql.stage/mbql", "source-table": <table-id>,
   "aggregation": [["measure", {}, <measure-id>]], "breakout": [["field", {"temporal-unit": "month"}, <month-field-id>]]}]}}
```

- Aggregation slot: inline (`["sum", {"name": "<out>"}, <field>]`, `["count-where", {"name": "churned_customers"}, ["=", {}, <movement-field>, "churned"]]`, `["share", {"name": "activation_rate"}, ["not-null", {}, <activated_at-field>]]`), a shared measure (`["measure", {}, <id>]`), or metrics for a derived metric (`["metric", {}, <id>]`, arithmetic over two for a ratio).
- A metric with a time column carries it as its one breakout, monthly by default, `display: "line"`; the default does not lock other groupings. None: `display: "scalar"`. A measure is one aggregation only; a segment is filters only. On a model, `"source-card": <model-id>` replaces `source-table`.
- Every literal was read from the data first (`mb field values`, an enum probe).

## The metadata pass

On the 5–15 tables people query, one batch per table, entity tables first, in this order, before any metric (value catalogs: `metadata` skill):

1. `type/PK` on the key; `type/FK` + `fk_target_field_id` on every column naming another final row (the target a `type/PK` in the same database). Joins, linked filters, and publishing depend on them.
2. `data_layer` (`final`/`internal`/`hidden`) and `data_source` (`transform` for externally built, `ingested` for raw). Before hiding, find what reads it (`mb search "<name>"`, card queries naming its id); hiding what a card reads breaks it. On a table you did not build, `data_layer` is asked, never written unasked.
3. `entity_type`; semantic types on every column with meaning (`type/Category`, `type/Currency`, `type/Email`, locations, `type/CreationTimestamp`); `has_field_values: "list"` for filter columns up to ~100 values, `"search"` for ids and emails.
4. `visibility_type: "hidden"` on plumbing, `"details-only"` on long text; at most 50 visible columns; unique display names; `field_order` when the default buries what matters.
5. `display_name` and a 20–400 character `description` on every column people read (what search and Metabot rank by); `data_sensitivity` on personal fields.
6. Table `description` (grain, scope, required filters), `caveats`, `owner_email`.

When a job run can add category values, schedule `mb db rescan-values <db-id>` beside the job (after each run).

```bash
mb table update <table-id> --body '{"description":"<grain, scope, required filters>","caveats":"<…>","owner_email":"<owner>","data_layer":"final","entity_type":"entity/TransactionTable"}' --profile <profile> --json
mb field update <field-id> --body '{"semantic_type":"type/FK","fk_target_field_id":<target-pk-field-id>}' --profile <profile> --json
```

## The questions table

In the state file, one row per cluster: home table, time column (the date basis, a decision), definitional flag, breakouts (own columns or through a foreign key), exists or build. Rows differing only by filter or breakout are one metric. A breakout shared across home tables lives once on an entity table every home table reaches by foreign key. A question the layer cannot answer is a gap for build, never a one-off SQL card.

## Describe and name

The name is the number as people say it, never a slug. The description opens `Draft.` only while an open decision shapes it or it is neither reconciled nor accepted; says what it counts and excludes (the largest exclusion's size), what it must not be compared to, whether past periods restate, which variant it is where the domain note lists several; ends with the owner. No decision keys, ids, or dated evidence.

- Metric shape: `Monthly recurring revenue at month end, in <currency>, from subscription lines spread over their service period. Excludes one-off charges, tax, and applied credits (one-offs are about 4% of invoiced amount). Not comparable to accounting revenue. Past months restate when a late invoice lands. Owner: <email>.`
- Segment shape: `Paying accounts: at least one paid invoice in the month; trials and internal accounts excluded (flagged on Customers). A move to a cheaper plan is a contraction, not churn. Owner: <email>.`

The CLI cannot write glossary terms: for each decided definitional choice and headline metric, the hand-back lists an entry for the user to add at `/data-studio/glossary` (plain definition in the company's words, variant chosen, the metric computing it, owner); organisation terms and headline names only, never synonym lists.

## Verify before handing back

- Three surfaces agree for one period: the measure summarised on its table, the metric (`mb card query <id>`), and a question aggregating `["metric", {}, <id>]`.
- A golden set: 10–20 of the owner's real questions with two to four phrasings each, plus out-of-scope ones the layer must not answer. Each in-scope question is a saved question composing the definitions in the domain's `Golden questions` collection, its expected result in the state file; re-run with `mb card query` after every change to what it reads.
- `mb search "<the user's wording>" --models metric,measure,segment,table` returns the intended object first for each phrasing; otherwise improve the name or description.
- One held-out question answered from the definitions, segments, and FK breakouts alone; needing native SQL is a gap to log.
- One headline reconciled (`playbooks/reconcile.md`); the rest labelled Draft or Self-consistent.
- The metadata pass left every table people read with a key, described columns, and a grain line.

## The Library and the canonical set

The canonical set: the home tables plus the entity tables they reach; nothing staging or intermediate. Publishing is a stop, never while a decision it reads is open. It cascades to FK targets, so first check every foreign key on those tables targets a final table (an FK into staging publishes staging); then `mb library publish --table-ids <ids>` and `mb library get` (no staging in Data). A metric enters the Library by filing it in the Library's Metrics collection (`mb card update <id> --body '{"collection_id":<library-metrics-id>}'`). No Library: a `Definitions` collection under the domain's is the canonical set, stated. On a git-synced instance, table metadata exports only if the Library's Data collection is in the sync scope (`playbooks/sync.md`). The CLI cannot set the verified badge: once the golden set passes, ask the user to verify the canonical metrics in the UI.

## Own, file, change, retire

- Default filing, to confirm: one collection per business domain for dashboards and documents, `Definitions` under it for non-Library metrics, `Drafts` for review.
- `owner_email` on every final table; the owner ends every definition's description.
- Changing, disputing, versioning, or retiring a delivered definition: `playbooks/change.md`.
