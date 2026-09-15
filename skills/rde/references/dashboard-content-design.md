# Dashboard content design

What a dashboard contains before it is laid out; the router sends you here at the start of any dashboard work. Layout, wiring, and chart settings: `mb skills path dashboard` and `visualization`.

## Start from the audience's questions

Write the questions in the audience's words first; a card answering no named question does not exist. Settle:

| Setting | Decides |
| --- | --- |
| Audience | who opens it and what they already know |
| Decision | what they do differently after looking |
| Cadence | daily, weekly, monthly, quarterly: the default period, the granularity, and whether the flagged incomplete period shows ([modeling-decisions.md](modeling-decisions.md)) |

Different answers across the list mean more than one dashboard: one per audience and cadence; overlapping audiences get one self-contained tab each. Match the dashboards the audience already uses (`mb dashboard get <id> --json`); defaults below apply only where nothing exists.

## Card order

1. KPI row: three to five headline numbers (a default).
2. Trend: each headline over time at the audience's cadence.
3. Breakdown: the same numbers split by the one or two dimensions this audience acts on.
4. Detail: the row-level table people export, last, only when asked for.

A card fitting no role is deleted; never a count without its denominator, a card frozen to one filter value, or a dimension nobody owns. The card name is the question as the audience asks it; grain and period go in its description: `Revenue by month (recognised, excludes current month)`, never `Revenue`. Every card composes a published metric or measure by id with a segment and a breakout ([semantic-layer-design.md](semantic-layer-design.md)); a number the layer cannot express is a gap to log and a definition to build first, never a re-derived aggregation.

## What makes a number actionable

- Every KPI is a `smartscalar` with one comparison the audience already uses in `scalar.comparisons`: `previousPeriod` by default, `periodsAgo` with `value: 12` for seasonal cycles, `staticNumber` with `value` and `label` where a target exists (ask, never invent). A trend with a target gets `graph.show_goal: true` and `graph.goal_value`; one value against a target is `progress` with `progress.goal`.
- Every KPI has a drill: the tile's `click_behavior` links to the metric's own question, a breakdown card cross-filters the detail table, whose key column links to the source-system record when a URL pattern exists.
- A `Definitions` text card at the foot of the first tab: each headline with the first sentence of its metric description; card names are metric names.
- The one or two numbers a person must not miss get an alert to a named owner: `goal_below` or `goal_above` on the trend card carrying `graph.goal_value`, or `has_result` on an exception question returning rows only when the thing happened. Alerts and subscriptions need the channel configured (`mb setting get 'email-configured?'`); confirm before promising.
- A wall or TV view is its own tab: at most six cards, no tables, no filters.

## Filters

- One filter per dimension the audience names.
- One date filter per date basis, mapped to the metric's time column on every card sharing it; a card measured on another date column sits on a tab with its own date filter, or stays unmapped and titled with its basis. Its default matches the cadence; its type matches the audience (`date/relative` for operations, `date/month-year` for monthly reviews). Where the audience switches grain, add a `temporal-unit` parameter bound to the same column.
- Every filter maps to every card it should control; a dependent pair is a linked filter and needs a metadata FK.

## Draft, then review on screen

Build the plan as a dashboard in a `Drafts` collection (or the company's equivalent) and hand back the link with the card list and the omissions, and ask for reactions to the screen, not approval of a list; stop beforehand only when audience or cadence is the user's call. A `text` virtual dashcard (`card_id: null`, `visualization_settings.virtual_card.display: "text"`) at the top states as-of date, refresh schedule, data lag, and the trust label of each headline ([collaboration-contract.md](collaboration-contract.md)): `Data through August; refreshed nightly 02:00 UTC; one day lag. MRR: Self-consistent only. Activation rate: Draft, provisional decisions: D12.` Move to the final collection after the plausibility pass.

## Delivery per audience

- Readers who do not open Metabase: a subscription on the cadence (`mb subscription create`, monthly `first` or weekly `mon`), `skip_if_empty: true` for exception dashboards, `parameters` per recipient where audiences differ; recipients confirmed first.
- Readers of prose: a document (`mb document create`) with the period's narrative, each headline a `cardEmbed` linked to its metric by a `smartLink` (`model: "metric"`).

## The plausibility pass

Only what `mb` can check.

- `mb card query <id> --json` returns rows for every card; a breakdown's groups sum to its headline in one `mb query` on the metric.
- `mb dashboard parameter-values <dashboard-id> <param-id>` lists values for every filter (empty means `has_field_values` or a rescan is missing); each filter tested with two values, one returning no rows.
- `mb card get <id> --fields display,visualization_settings --json` reads back chart, comparison, and goal.
- `mb dashboard cards <id> --json`: no two cards are one question under two names; the text card's as-of date matches the last job run.
- `mb subscription get <id> --json` reads back the schedule and recipients; alerts on `has_result` cards were sent once to yourself (`mb alert send <id>`).

## Finished content plan

Audience: the CEO. Decision: where the next hire goes (sales or product) at the monthly review. Cadence: monthly, first Monday, complete months, current month flagged.

| Card | Question | Metric or segment, breakout | Display, comparison, drill |
| --- | --- | --- | --- |
| 1 | What is MRR? | `Monthly recurring revenue` | `smartscalar`, `previousPeriod`, `staticNumber` target; drill to the metric |
| 2 | Are we adding more than we lose? | `Net new MRR` | `smartscalar`, `previousPeriod`; drill to the movement table |
| 3 | What share of paying accounts left? | `Logo churn rate`, segment `Paying accounts` | `smartscalar`, `periodsAgo` 12; alert `has_result` on a churn-ceiling exception question |
| 4 | Do new signups reach value? | `Activation rate`, unmapped, titled by signup month | `smartscalar`, `previousPeriod`; drill to the cohort table |
| 5 | Which plans drive MRR? | `Monthly recurring revenue` by `plan` (FK) | `line`, goal line at the plan target |
| 6 | Who churned this month? | segment `Churned this month`, detail | `table`, key column links to the CRM record |

One `date/month-year` filter on `period_month`, default last complete month, mapped to cards 1, 2, 3, 5, 6. Text card: as-of, refresh, lag, trust labels. Subscription: monthly `first`, 08:00, the CEO. Left off: ARR (MRR times twelve, said in the MRR description) and support tickets (no owner, not in the question list).
