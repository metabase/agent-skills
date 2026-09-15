# Dashboard content design

What a dashboard contains before any of it is laid out: who it is for, which questions become cards, in which order, which filters exist, and what does not belong; the router sends you here at the start of any dashboard work. Layout, filter wiring, and chart settings are `mb skills get dashboard` and `mb skills get visualization`; decide here, execute there.

## Start from the audience's questions

Write the questions in the audience's words before opening the instance; a card that answers no named question does not exist. Settle three things first:

| Setting | Decides |
| --- | --- |
| Audience | who opens it and what they already know |
| Decision | what they do differently after looking |
| Cadence | daily, weekly, monthly, quarterly: the default period, the granularity, and whether the incomplete current period may appear |

When the answers differ across the question list, that is more than one dashboard; say so at the checkpoint ([collaboration-contract.md](./collaboration-contract.md)).

## Match the instance's conventions

Before proposing a layout family, read what exists: `mb dashboard list --json`, then `mb dashboard get <id> --json` on the ones the audience already uses. Match their tab structure, filter placement, naming, and card density; propose the defaults below only where nothing exists, and label them as defaults to confirm.

## One dashboard per audience and cadence

Split by who looks and how often, never by data source. A weekly operations funnel and a quarterly leadership headline do not share a dashboard even when every number comes from one table. Where audiences genuinely overlap, one self-contained tab per audience.

## Card order

1. KPI row: three to five headline numbers (a default), each with a previous-period comparison.
2. Trend: each headline over time at the audience's cadence.
3. Breakdown: the same numbers split by the one or two dimensions this audience acts on.
4. Detail: the row-level table people export, last, and only when asked for.

A card fitting none of the four roles is a candidate for deletion. Position follows role, not appearance.

## Every card names its question, grain, and period

Record before creating each card: the question in one sentence as the audience asks it; the grain of a row; the period and whether the incomplete current one is included; the metric and segment it is built from. The question goes in the card name, the grain and period in its description: `Revenue by month (recognised, excludes current month)`, never `Revenue`.

## Cards use the semantic layer, never re-derive

A card uses the published metric and segment. No re-derived aggregation inside a card query, no hand filter an existing segment already expresses; every re-derivation is a second definition that drifts. A card the published definitions cannot build is a gap in the layer: log it, build the definition ([semantic-layer-design.md](./semantic-layer-design.md)), then the card. Two cases that are not exceptions: a number needing a join (widen the table in a transform first) and a number needing an unagreed threshold (checkpoint with row counts).

## Filters are the dimensions the audience slices by

Choose filters from the question list and the existing saved questions, not from which columns exist.

- One filter per dimension the audience names; an unasked-for filter invites a misreading.
- A date filter whose default matches the cadence, so the dashboard is correct on open.
- Every filter maps to every card it should control; a filter governing three of eight cards makes the cards disagree.
- A dependent pair (region then country, plan family then plan) is planned as a cascade and wired per `mb skills get dashboard`.

## What not to chart

| Do not chart | Instead |
| --- | --- |
| A count with no denominator | the rate, or both |
| A card frozen to one period or one dimension value | a filter |
| A number the layer cannot defend (inclusions and exclusions unstated) | finish the definition first |
| Two numbers side by side whose descriptions say they cannot be reconciled | keep them apart or add a text card saying so |
| More than about eight cards on one tab (a default) | cut to the decision or split tabs by audience |
| A dimension nobody owns | drop it; no owner, no decision |

## The plausibility pass

Before calling a dashboard done:

- `mb card query <id> --json` returns rows for every card; cross-check each number against a query you run through `mb query` and against any independent reference the business already quotes.
- Confirm totals agree where they should; two cards from one metric with different filters must add up.
- Exclude or label the incomplete trailing period ([modeling-decisions.md](./modeling-decisions.md)).
- Test every filter with at least two values, one of which returns no rows.
- `display` on each card is the intended chart type.
- State the refresh schedule and the data's lag on the dashboard itself.
- Confirm no two cards are the same question under different names.

Hand back a one-line map: who it is for, which questions it answers, which it deliberately does not, and what each number was checked against.
