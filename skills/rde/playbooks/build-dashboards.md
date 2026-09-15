# Build dashboards

Applies: the semantic layer exists and the user wants something to look at. Produces a content plan, a draft reviewed on screen, cards composing definitions by id, a plausibility pass, delivery per audience. No definitions yet: say so and offer [`build-semantic-layer.md`](build-semantic-layer.md).

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 STATE.md` `2 content plan` `3 draft` `4.<card> build` `5 page: text, filters, layout` `6 plausibility` `7 delivery` `8 final collection` `reply`.

Read first: [`dashboard-content-design.md`](../references/dashboard-content-design.md), [`state.md`](../references/state.md), and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`; ids from STATE.md Questions.

```bash
jq .dataset_query ./.scratch/card.json | mb query --file - --dry-run; mb card create --file ./.scratch/card.json
mb card query <card-id> --fields status,data.rows                  # equals STATE.md's verified number
mb dashboard create --file ./.scratch/dash.json
mb dashboard cards <dash-id>                                       # a row's id is the dashboard_card_id; card_id is the card
mb setting get 'email-configured?' | jq .value                     # false: stop
mb subscription create --file ./.scratch/sub.json
mb dashboard update <dash-id> --body '{"collection_id":<final collection id>}'
```

Bodies (metric 301, segment 12, `period_month` 1717):

```json
{"name":"MRR by month, paying accounts","display":"line","collection_id":<drafts>,"visualization_settings":{},
 "dataset_query":{"lib/type":"mbql/query","database":3,"stages":[{"lib/type":"mbql.stage/mbql","source-table":909,
   "aggregation":[["metric",{},301]],"filters":[["segment",{},12]],"breakout":[["field",{"temporal-unit":"month"},1717]]}]}}
{"name":"MRR","display":"smartscalar","collection_id":<drafts>,"dataset_query":{"... the same query ..."},
 "visualization_settings":{"scalar.comparisons":[{"id":"c1","type":"previousPeriod"},{"id":"c2","type":"staticNumber","value":100000,"label":"Target"}]}}
{"name":"CEO weekly","collection_id":<drafts>,
 "parameters":[{"id":"period","name":"Period","slug":"period","type":"date/month-year"}],
 "dashcards":[
  {"id":-1,"card_id":null,"col":0,"row":0,"size_x":24,"size_y":2,"visualization_settings":{"virtual_card":{"display":"text"},"text":"Data through August 2026; September flagged incomplete. Refreshed daily 03:00 UTC, a day behind billing. MRR: Reconciled to finance on 2026-09-12, within 1%. Churn: Draft, provisional decisions: D7."}},
  {"id":-2,"card_id":302,"col":0,"row":2,"size_x":6,"size_y":3,"parameter_mappings":[{"parameter_id":"period","card_id":302,"target":["dimension",["field",1717,null]]}]}]}
{"name":"CEO weekly","dashboard_id":<dash-id>,"cards":[{"id":302,"dashboard_card_id":87,"include_csv":false,"include_xls":false}],
 "channels":[{"channel_type":"email","schedule_type":"weekly","schedule_hour":8,"schedule_day":"mon","recipients":[{"email":"ceo@acme.example"}]}]}
```

A measure sits in the same slot as `["measure",{},<id>]`; on a model the stage reads `"source-card": <model-id>` instead of `source-table`; a number this shape cannot express is a gap: log it in STATE.md Questions and define it first.

## 1. STATE.md

Read it; every Questions row this page uses carries a metric or measure id and a verification result.

## 2. Content plan

Per audience and cadence, shaped like the finished plan in `dashboard-content-design.md`: the decision the page serves; per card the question, definition, segment, breakout, display; per KPI the comparison, target (ask, never invent), drill, alert; the subscription; what is left off and why. Card choices are `[DECIDED, reversible]`; more than one audience or cadence where the split is the user's call is a `[CHECKPOINT]`.

## 3. Draft, then review on screen

Per `dashboard-content-design.md`, Draft, then review on screen: build in `Drafts`, hand back the link, the card list, and the omissions.

## 4. Cards

One card per plan entry, naming the metric, measure, or segment by id, adding only a breakout and a display; dry-run before create. The card's headline equals the number verified in STATE.md; a mismatch means the card added a filter. Read the card back; set `graph.dimensions` and `graph.metrics` (output column names) only when the auto-pick is wrong: `mb skills path visualization`, "Minimum-viable settings per chart family".

## 5. The page

A text card at the top: data through, refresh (the job's schedule, never a hope), lag, the trust label per headline; a `Definitions` text card at the foot with the first sentence of each headline's description. Filters per `dashboard-content-design.md`: one date filter per date basis, mapped to the metric's time column on every card sharing it. Layout: `mb skills path dashboard`, Read "Layout: the grid is 24 columns"; drills and cross-filters from "Choose the interaction" when the plan calls for them.

## 6. Plausibility pass

Per `dashboard-content-design.md`; chase every implausible number; never ship it with a caveat; dropdowns populated (`mb db rescan-values $DB` if stale).

## 7. Delivery per audience

Readers who do not open Metabase: a subscription on the cadence (channel configured; mail to real people is irreversible, `[CHECKPOINT]` on recipients). Prose readers: a document embedding the cards (`mb skills path document`, Read "Embedding an existing card"). Numbers not to miss: an alert (body in [`validate-and-reconcile.md`](validate-and-reconcile.md)).

## 8. Final collection

Move the dashboard after the pass; record it in the STATE.md Questions rows.

## Done when

Every card traces to a Questions row and composes a definition by id; text card, date filters, and definitions card are on the page; the plausibility pass is clean; every audience in the plan has its delivery; omissions written down.

## Reply

The five-part hand-back in `collaboration-contract.md`; under part three: the cards in reading order by the question each answers, what was left off and why, each KPI's comparison and target.
