# Build dashboards

Applies when the final-layer tables and the semantic layer exist and the user wants something to look at; produces a content plan (which question becomes which card on which dashboard), the cards and dashboards, and a plausibility pass over every number. This playbook owns what goes on the page; the bundled skills own how a chart, the grid, filters, and interactivity are authored.

Read first: [`dashboard-content-design.md`](../references/dashboard-content-design.md), [`collaboration-contract.md`](../references/collaboration-contract.md), `mb skills get dashboard`, and `mb skills get visualization`.

## 1. Discover what exists and confirm the inputs

Run `mb dashboard list --json`, `mb collection tree --json`, and `mb search --models dashboard,card --limit 50 --json`. Record existing dashboards, naming, and collection layout; a dashboard that already answers the question is extended, not duplicated, and new ones follow the same placement.

Confirm the final-layer tables are deployed (`mb table list --db-id <db-id> --json`) and the definitions from [`build-semantic-layer.md`](build-semantic-layer.md) exist. State and goal disagreeing ("chart this" over raw tables): say so and offer the earlier stage. No semantic layer yet: a dashboard is possible, but every card then carries its own version of each number; name that trade-off and let the user choose.

Check: every number you intend to chart has one definition behind it, or the user has accepted that it will not.

## 2. Name the audience, then plan the content

One dashboard per audience and cadence, per `dashboard-content-design.md`. Per dashboard write, before building: who reads it, the question it answers on opening, and the ordered card list in the order `dashboard-content-design.md` sets. Per card: the question it answers, the metric or measure, the segment, the dimension, the intended display. Leave off what `dashboard-content-design.md` says not to chart, and write down what you left off and why.

Check: every card traces to a question somebody asked; the plan ends with fewer cards than it started with.

## 3. Checkpoint the plan

Present the card list per dashboard, in order, in plain language, with the omissions, using the checkpoint block in [`collaboration-contract.md`](../references/collaboration-contract.md). Wait.

## 4. Build the cards

One card per approved entry, composed from the semantic layer (metric or measure, plus segment, plus breakout), never re-deriving a number. Display and settings per `mb skills get visualization`. File the cards in an ordinary collection matching the layout found in step 1.

Check: each card returns rows on its own, and its headline value equals what the same definition returned in semantic-layer verification. A mismatch means the card added a filter; find it before laying anything out.

## 5. Layout and wiring

Load `mb skills get dashboard --max-bytes 0` and follow it. Place the cards in the plan's order; choose filters by the filter rule in `dashboard-content-design.md`.

## 6. Plausibility pass

Run the plausibility pass in `dashboard-content-design.md` and chase every implausible number rather than shipping it with a caveat. A plausible number never checked against an outside reference is said to be exactly that; proving it is [`validate-and-reconcile.md`](validate-and-reconcile.md).

## Done when

Every dashboard has a named audience and an approved card list; every card traces to a question and composes an existing definition; the filter rule in `dashboard-content-design.md` holds; the plausibility pass is clean; what was left off the page is written down.

## Reply

One sentence per dashboard on what it answers, with the link. The cards in reading order, each by the question it answers, not its chart type. What you left off and why. Any number that is plausible but unreconciled. The open decisions, and an offer to reconcile the headline numbers next.
