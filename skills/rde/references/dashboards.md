# Dashboards

What a dashboard contains before it is laid out. Grid, filters, and interaction: `dashboard` skill; chart settings: `visualization`; deliveries: `notification`; documents: `document`.

## Start from the audience's questions

The questions in the audience's words first; a card answering none does not exist. Settle the audience (who opens it, what they know), the decision (what they do differently after looking), and the cadence (default period, granularity, whether the incomplete period shows). Different answers mean one page per audience and cadence, or one tab each for overlapping audiences; ask these only when they split the page. Match pages the audience already uses (`mb dashboard get <id>`). Targets are asked, never invented.

## Card order and composition

1. A KPI row of three to five headlines. 2. A trend of each at the audience's cadence. 3. The same numbers split by the one or two dimensions this audience acts on. 4. The row-level table, last, only when asked.

A card fitting no role is left off. Never a count without its denominator, a card frozen to one filter value, a dimension nobody owns, or two cards asking one question. The card name is the question as asked; grain and period go in its description (`Revenue by month (recognised, excludes the current month)`).

Each card names a metric, measure, or segment by id and adds only a breakout and a display; its headline equals the definition's number for the period (a mismatch means the card added a filter). A number the definitions cannot express is a gap for semantic or build, never a re-derived aggregation. On a page built from raw tables by the user's choice, each card's description opens `Ad hoc:` with what is unchecked.

```json
{"name": "<the question as asked>", "display": "line", "collection_id": <drafts-id>, "visualization_settings": {},
 "dataset_query": {"lib/type": "mbql/query", "database": <db-id>, "stages": [{"lib/type": "mbql.stage/mbql", "source-table": <table-id>,
   "aggregation": [["metric", {}, <metric-id>]], "filters": [["segment", {}, <segment-id>]],
   "breakout": [["field", {"temporal-unit": "month"}, <month-field-id>]]}]}}
```

Set `graph.dimensions`/`graph.metrics` (output column names) only when the automatic pick is wrong.

## What makes a number actionable

- Every KPI is a `smartscalar` with one comparison the audience uses in `scalar.comparisons`: previous period by default, twelve periods ago for seasonal cycles, a labelled static target where one exists. One value against a target is `progress`; a trend with a target gets `graph.show_goal` and `graph.goal_value`.
- Every KPI drills to its metric (`click_behavior`); a breakdown cross-filters the detail table, whose key links to the source-system record when a URL pattern exists.
- A text card on top of the first tab: data through, refresh (the job's schedule), lag, each headline's trust label (`Data through August; refreshed daily 03:00 UTC, one day behind billing. MRR: Reconciled to finance's export, August, within 1%. Activation rate: Draft.`). A `Definitions` text card at its foot: each headline with the first sentence of its description.
- The one or two numbers not to miss get an alert to a named owner: `goal_above`/`goal_below` on a trend with a goal, or `has_result` on an exception question.
- A wall or TV view is its own tab: at most six cards, no tables, no filters.

## Filters

- One per dimension the audience names, mapped to every card it should control (an unmapped parameter is inert).
- One date filter per date basis, mapped to the time column on every card sharing it; a card on another date sits on its own tab or stays unmapped and titled with its basis. Default matches the cadence; type matches the audience (`date/relative` for operations, `date/month-year` for monthly reviews); add a `temporal-unit` parameter where the audience switches grain.
- A linked filter needs a metadata FK; a join inside a question does not count. Parameters and dashcards replace whole on update: read, modify, write.

## The plausibility pass

Chase every implausible number; never ship it with a caveat.

- `mb card query <id>` returns rows for every card; a breakdown sums to its headline.
- `mb dashboard parameter-values <dashboard-id> <param-id>` lists values for every filter (empty: missing `has_field_values` or a rescan); test each filter with two values, one returning nothing.
- `mb card get <id> --fields display,visualization_settings` reads back chart, comparison, goal.
- `mb dashboard cards <dashboard-id>`: no duplicate questions; the text card's date matches the job's last run.
- `mb subscription get <id>` reads back schedule and recipients; every alert was sent once to yourself.

## Delivery per audience

- Non-openers: a subscription on the cadence, `skip_if_empty` for exception pages, per-recipient `parameters` where audiences differ; cards listed by dashcard id (`mb dashboard cards`), never card id. Real recipients are a stop.
- Prose readers: a document with the period's narrative, each headline embedded as its card (`cardEmbed`) and linked to its metric.
- Numbers not to miss: an alert, 7-field Quartz cron in the report timezone.
- Check the channel first (`mb setting get 'email-configured?'`); unconfigured is a stop for the admin.

## A content plan, shape only

Audience: the CEO. Decision: where the next hire goes, at the monthly review. Cadence: monthly, complete months, current month flagged.

| Card | Question | Definition, breakout | Display, comparison, drill |
| --- | --- | --- | --- |
| 1 | What is MRR? | Monthly recurring revenue | smartscalar, previous period, target; drill to metric |
| 2 | Are we adding more than we lose? | Net new MRR | smartscalar, previous period; drill to movements |
| 3 | What share of paying accounts left? | Logo churn rate, segment Paying accounts | smartscalar, twelve periods ago; alert on a churn-ceiling exception |
| 4 | Do signups reach value? | Activation rate by signup month, unmapped from the date filter | smartscalar, previous period; drill to cohorts |
| 5 | Which plans drive MRR? | MRR by plan through the FK | line, goal at the plan target |
| 6 | Who churned this month? | segment Churned this month, detail | table, key links to the CRM |

One `date/month-year` filter on the month column, default last complete month, mapped to cards 1, 2, 3, 5, 6. Subscription: monthly, first Monday, the CEO. Left off: ARR (MRR × 12, said in MRR's description), support tickets (no owner, not asked).
