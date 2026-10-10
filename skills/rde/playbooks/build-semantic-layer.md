# Build the semantic layer

Applies: final-layer tables exist with rows. Produces one starting object per table, the definitions with descriptions and checked numbers, and the canonical set published or filed.

Checklist: `1 STATE.md` `2 starting objects` `3.<table> metadata` `4 Questions` `5 conformed dims` `6.<definition> define` `7 describe` `8 verify` `9 publish, owners` `reply`.

Read first: [`semantic-layer-design.md`](../references/semantic-layer-design.md), [`entities-and-time.md`](../references/entities-and-time.md), and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`; field ids: `mb table get <id> --include fields`.

```bash
mb table update <table-id> --body '{"entity_type":"entity/TransactionTable","description":"One row per customer per month.","caveats":"USD only; newest month flagged incomplete.","owner_email":"finance@acme.example"}'
mb field update <field-id> --body '{"semantic_type":"type/FK","fk_target_field_id":<customers.customer_id field id>}'
mb field update <field-id> --body '{"semantic_type":"type/Category","has_field_values":"list"}'
mb search "<the user's wording>" --models metric,measure,segment,dataset
mb measure create --file ./.scratch/measure.json; mb segment create --file ./.scratch/segment.json
jq .dataset_query ./.scratch/metric.json | mb query --file - --dry-run; mb card create --file ./.scratch/metric.json
mb card query <metric-id>
mb library publish --table-ids <ids>
mb card update <metric-id> --body '{"collection_id":<library metrics collection id>}'
```

Bodies (`<column-id>` is that column's field id):

```json
{"name":"Recurring revenue","description":"Recurring revenue, USD.","table_id":<table-id>,
 "definition":{"lib/type":"mbql/query","database":<db-id>,"stages":[{"lib/type":"mbql.stage/mbql","source-table":<table-id>,"aggregation":[["sum",{"name":"mrr_usd"},["field",{},<mrr_usd-id>]]]}]}}
{"name":"Complete periods","description":"Months fully loaded.","table_id":<table-id>,
 "definition":{"lib/type":"mbql/query","database":<db-id>,"stages":[{"lib/type":"mbql.stage/mbql","source-table":<table-id>,"filters":[["=",{},["field",{},<is_complete_period-id>],true]]}]}}
{"name":"Monthly recurring revenue","type":"metric","collection_id":<collection-id>,"display":"line",
 "dataset_query":{"lib/type":"mbql/query","database":<db-id>,"stages":[{"lib/type":"mbql.stage/mbql","source-table":<table-id>,
   "aggregation":[["measure",{},<measure-id>]],"breakout":[["field",{"temporal-unit":"month"},<period_month-id>]]}]},"visualization_settings":{}}
```

The aggregation slot per definition: a sum `["sum",{"name":"mrr_usd"},["field",{},<mrr_usd-id>]]`; `count-where` `["count-where",{"name":"churned"},["=",{},["field",{},<state-id>],"churned"]]`; `share` `["share",{"name":"activation_rate"},["not-null",{},["field",{},<activated_at-id>]]]`; a derived metric `["metric",{},<metric-id>]`. A definitional filter goes in `filters` of the same stage. On a model the stage reads `"source-card": <model-id>` instead of `source-table`.

## 1. STATE.md and tables

Read STATE.md; every Models row a definition needs has `table_id` and rows; a missing one goes back to [`build-clean-tables.md`](build-clean-tables.md).

## 2. One starting object per table

Per `semantic-layer-design.md`: the curated table (Library or not), no model over it; a model only where people start from a join, metrics only. `[DECIDED, reversible]`.

## 3. Metadata chain

Per defining table in `semantic-layer-design.md`'s order, bodies above; gaps left by `build-clean-tables.md` step 6 close here.

## 4. Questions table

Each STATE.md Questions row gets a home table, a time column (the date basis), the definitional filter, breakouts (own or FK), exists or build. Two owners defining one number differently: `[CHECKPOINT]` with both numbers.

## 5. Conformed dimensions

A breakout shared by two home tables lives once on an entity table reached by a metadata foreign key (`entities-and-time.md`), never copied; a metric reads it through `source-field` (`mb skills path mbql`, "Joins and FK traversal").

## 6. Define in ladder order

Measures; metrics over measures by id; derived metrics over metrics; segments; on a model, metrics only. Definitional filters live inside the definition; slicing filters are segments. A metric with a time column carries a monthly breakout and `display: line`, otherwise `scalar`.

## 7. Describe

Trust label first, per the contract; then what it counts and excludes with the largest exclusion's size, restatement, what it must not be compared to, the owner. A segment: what it includes, excludes, why, its warning.

## 8. Verify

The four checks under Verify before handing back in `semantic-layer-design.md`, each result written to the Questions row's `status`; a headline over tolerance goes to [`validate-and-reconcile.md`](validate-and-reconcile.md).

## 9. Publish or file, then owners

Canonical set and cascade guard per `semantic-layer-design.md`, Library. Publishing is irreversible, `[CHECKPOINT]`, never while a decision it reads is open. Metrics enter the Library by filing in its Metrics collection; no Library: a `Definitions` collection, stated. Changing a delivered definition: the flow in `semantic-layer-design.md`; timeline event body in [`validate-and-reconcile.md`](validate-and-reconcile.md). `owner_email` on every final-layer table and transform (ask once, suggesting the user's own or a team alias); every description ends with the owner. A metric's dimensions, the fields people break it out and filter it by (and the only path a data app has to a related table's field), are curated by hand on its **Dimensions** tab, not by the CLI: for each metric whose Questions rows break out by a field of another table reached by foreign key (a course title on an enrollments metric), name those fields in the hand-back and ask the user to add them there (**Available dimensions**, the group named after the foreign key column), in the development Metabase before the export so they sync with the metric.

When STATE.md `remote_sync` is not `none`, sync the canonical set once it is published (with `none`, skip this paragraph and say nothing about syncing): when the Library is not synced already (on an rde instance it is), flag it (`mb git-sync add-collection <library id>`, which carries Data and Metrics), then export, each step confirmed first per [`remote-sync.md`](../references/remote-sync.md). A "not now" is recorded in STATE.md and named in the hand-back; a data app cannot be built on the set until it is synced.

## Done when

Every Questions row resolves to named objects with a verification result or is marked unanswerable with the reason; the canonical set is published or filed; owners set.

## Reply

The five-part hand-back in `collaboration-contract.md`; under part three: the objects by kind with their meaning, the held-out question and its answer, definitions still proposals.
