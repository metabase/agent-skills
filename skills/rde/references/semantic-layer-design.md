# Semantic layer design

What deserves a definition, which kind it is, how to keep one definition per number, and how to document it so caveats travel with the number; the router sends you here before any model, metric, measure, segment, or field-metadata edit. Mechanics are `mb skills get semantic-layer` and `mb skills get metadata`; decide here, execute there.

## Discover what exists

`mb segment list --json`, `mb measure list --json`, `mb library get --json`, `mb collection tree --json`, `mb card list --fields id,name,type,collection_id --json` (rows carry `type`, so metrics and models are in it), `mb search "<term>" --models metric,segment,measure,dataset --json`; then `mb card get <id> --fields dataset_query --json` on the saved questions that repeat, for the filters and calculations people re-type. Extend an existing definition instead of creating a parallel one; match its casing and noun order. Disagreements among saved questions are definitions to settle at a checkpoint (block in [collaboration-contract.md](collaboration-contract.md)) before building.

## Field metadata

On every table you will define against, in this order: entity key, foreign-key targets, semantic types, display names, plumbing hidden, descriptions. Complete means a description on every column people read and a semantic type on every column with business meaning. Ambiguous words are banned as column names: a term that names several populations in the business gets a disambiguated name at every use site, `billing_accounts`, `login_accounts`, or `contacts`, never `accounts`. Ids beside labels: [layering-and-naming.md](layering-and-naming.md). The rest: `mb skills get metadata`. No metric is defined before this pass is complete.

## Which kind of definition

| Entity | Stands for | Example |
| --- | --- | --- |
| Model | the curated column set or join people start from | `Orders` over the clean order table |
| Metric | the published number, an aggregate | `Total Revenue` = `Sum([revenue_usd])` |
| Measure | a table-bound aggregation reused inside questions | `Order count` on the order table |
| Segment | the row filter | `Paid accounts` = `plan <> 'plan_free'` |
| Dimension (a typed column) | the group-by | `Plan`, `Month`, `Region` |
| Transform | everything else | joins, row-level maths, business logic |

- A metric formula is an aggregation; a calculated column belongs in a transform and exists before the metric is written.
- A metric contains no join; a number needing two tables is a transform that widens the table first.
- A metric contains no row filter; reusable row selection is a segment the user combines at question time.
- A metric, measure, or segment reaches only the table it is defined on (`mb skills get semantic-layer`, single-table reach), so check reach before promising one.
- A metric is *the* company number; a convenient aggregation is a measure, not a published metric.

| Anti-pattern | Fix |
| --- | --- |
| Metric bundling several aggregations, a join, and a filter | transform plus a plain aggregate |
| Segment that changes what one row means | it is a transform |
| Native SQL question answering what the layer should answer | log the gap in the coverage file, build the definition |
| Everything published to the Library | publish only the canonical set; Library placement is a trust signal |

## One definition per number

Exactly one definition of each headline number exists in the instance. `Paid Revenue` is `Total Revenue` with `Paid accounts` applied, not a second metric. Failure condition: the moment two cards can disagree about a number, the layer has failed.

Compose derived numbers from canonical metrics: `Revenue per Customer` = `[Total Revenue] / [Paying Customers]`; `Net New Revenue` = the sum of the signed movement metrics. When a number needs metrics from two tables: widen the table, align through a shared foreign-key dimension, or accept two charts.

## Decompose the questions

1. Record the questions verbatim in `./.scratch/questions.md`; paraphrasing into metric names loses scope.
2. Name each question's tuple: metric, segment, breakout dimensions, grain.
3. Collapse: tuples differing only in segment or breakout are one metric. "Revenue for plan_basic", "Revenue by plan", and "Quarterly revenue by plan" are one metric, one segment, two breakouts.
4. Write the question-to-build map in `./.scratch`, one row per cluster: `Question cluster | Metric | Segment | Break out by | Dashboard`.
5. Build the metrics, segments, and dimensions, not the questions.
6. Walk every question back into a coverage file in `./.scratch` mapping question to metric, segment, breakout, dashboard. A gap is stated, never filled with a one-off SQL card.

## Pin every word to real data

Before defining `Active customer`, confirm the candidate rule against actual values: the distinct values of the status column, the spread of the last-order date, the row count each candidate catches. Use the entities and vocabulary the organisation already uses; when a word is contested, ask.

## Naming

Name for the person reading a menu six weeks from now, in plain English, the population and window in the name; join keys named identically wherever the same thing appears. Examples: `mb skills get semantic-layer`.

## Thresholds

Segment strictness, plan boundaries, recency windows: each is a default to confirm. Present the candidate values with the row count each catches, recommend one, and record the confirmed value as a named constant so a change is a re-run.

## Document so caveats travel with the number

A headline metric's description carries: grain and time convention (point in time at period end, trailing window); the formula inline where the name is looser than the definition; inclusions and exclusions with the size of the largest exclusion; which events do not move it (refund, credit, status change); whether prior periods can restate and why; which other number it must not be reconciled against one to one; a pointer to the timeline marking known incidents.

A segment's description states what it includes, what it excludes, why, and the business warning attached (a move from `plan_plus` to `plan_basic` is a downgrade, not churn).

Keep a glossary in `./.scratch`, one entry per loosely used term, recording where the available documentation disagrees rather than picking a winner nobody agreed to.

`mb timeline create` and `mb timeline-event create`: one timeline for definition changes (one event per date a definition moved, with direction and size), one for known data incidents (affected entity, signed error). Events render only on time-series questions in the timeline's collection, so file the timeline in the collection holding the affected metric's questions.

Never clean caveats away for a tidy dashboard; known errors, excluded populations, and an unexplained residual stay visible. Data-quality content lives in its own collection, separate from the business collection.

## Verify before handing back

- The definition returns a plausible number: not null, not an error, not an order of magnitude from a count you trust.
- A segment narrows the row count to roughly what profiling predicted when proposing it.
- A breakout by each declared dimension yields more than one group.
- The definition appears on a question built on the intended table; one built on the wrong table or needing a join silently never appears.
- The question-to-build map and coverage file are current, gaps listed.
- Implausible is a bug to fix; plausible but externally unverified is reported as exactly that ([reconciliation.md](reconciliation.md)).
- Only the canonical tables and metrics go to the Library, with the user's confirmation; without the Library, the canonical set is the described objects in the agreed collection.
