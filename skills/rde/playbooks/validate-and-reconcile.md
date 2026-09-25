# Validate and reconcile

Applies: a built number must be proven against something outside itself, or two numbers disagree. Produces a declared validation mode, a row-level comparison at the narrowest shared grain, a gap with a cause per bucket, a fix or a ceiling per cause, and standing controls.

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 reference, mode` `2 scope` `3 comparison` `4 buckets` `5.<rule> fix` `6 ceiling` `7 controls` `reply`.

Read first: [`reconciliation.md`](../references/reconciliation.md), [`state.md`](../references/state.md), and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`; `q()` is sourced from `./.scratch/probe.sh`.

```bash
mb search "<term>" --models table,card,metric --db-id $DB
mb card get <id> --fields name,dataset_query                # each side of a disagreement
mb setting get uploads-settings | jq .value.db_id           # must equal $DB
mb upload csv --file ./data/finance_mrr.csv --collection <id>
# the comparison transform: the create body in build-clean-tables.md, SQL from the full-outer-join shape in reconciliation.md
q "SELECT state, bucket, count(*) AS n, sum(gap) AS net, sum(abs(gap)) AS gross FROM <out_schema>.cmp_<number> GROUP BY 1, 2"   # state and bucket columns per reconciliation.md
mb card query <cmp-card-id> --export-format csv > ./.scratch/cmp.csv   # rows past the ceiling
mb card create --file ./.scratch/check.json; mb alert create --file ./.scratch/alert.json
mb timeline create --body '{"name":"Definition changes","collection_id":<analytics collection id>}'
mb timeline-event create --body '{"name":"Churn gap 1 to 2 months","description":"D7 answered; June to August restated down 3.1%.","timestamp":"2026-09-15T00:00:00Z","timezone":"UTC","time_matters":false,"timeline_id":<id>}'
```

Bodies:

```json
{"name":"DQ: customer_month failures","display":"table","collection_id":<dq collection id>,"visualization_settings":{},
 "dataset_query":{"lib/type":"mbql/query","database":3,"stages":[{"lib/type":"mbql.stage/native","native":"<the structural checks as one query, one row per failing check>"}]}}
{"payload":{"card_id":410,"send_condition":"has_result","send_once":false},
 "subscriptions":[{"cron_schedule":"0 0 7 * * ? *"}],
 "handlers":[{"channel_type":"channel/email","recipients":[{"type":"notification-recipient/raw-value","details":{"value":"data@acme.example"}}]}]}
```

## 1. Land the reference, declare the mode

Search before asking; ask for the reference at the finest grain, keyed by something both sides carry. Land it with `upload csv` only when the uploads database is the build's; otherwise the user's loader. Two numbers disagreeing inside the instance: read both queries, the metric is the reference (`source_parity`, `reconciliation.md`). Never fabricate a figure. The mode comes from the table in `reconciliation.md`; with no reference a pass rate proves nothing. Mode, reference rows, grain, pull date into STATE.md Decisions.

## 2. Scope the reference to the build

Each filter with its reason: the categories the build recognizes, no forecast rows, complete periods, the exclusions both sides claim. Coverage differences are reported, not fixed. The comparison universe is one sentence every figure is quoted against.

## 3. Reconcile at the narrowest shared grain

The comparison is its own transform (or a model in the company's tool) with the full-outer-join shape in `reconciliation.md`, on a declared key, at the grain the model produces; roll up only after the row level passes.

## 4. Decompose the gap

Bucket every non-match row with the ordered `CASE` in `reconciliation.md`, a column of the comparison transform: rows, net, gross, share per bucket; agreement at several tolerance bands; the top rows by absolute gap read one by one; dimensions compared, not only the measure. Each bucket gets a cause, fixable or not, or stays unattributed. Tolerances and boundaries are `[DECIDED, reversible]`. Bucket counts sum to the compared rows; every headline count is computed, never remembered.

## 5. Fix one rule at a time

Each fix changes one rule and is re-measured against the same reference under the same universe, before and after per direction. The row that exposed the rule becomes a fixture row and an expectation on the model's transform test before the SQL changes (`build-clean-tables.md` step 8; [`transform-tests.md`](../references/transform-tests.md)), so the bucket cannot reopen silently. Closing a gap with logic not in the plan is a `[CHECKPOINT]`; a headline that moved gets a timeline event and the contract's restatement protocol.

## 6. Declare the ceiling

Per `reconciliation.md`: each item the sources cannot carry with its reason and effect; the residual; stop.

## 7. Standing controls

Freshness and structural checks by default, the rest on request (`reconciliation.md`). Each is a check card returning rows only on failure plus a `has_result` alert (channel first: `mb setting get 'email-configured?'`; test with `mb alert send <id>` to yourself; more in `mb skills path notification`, Read "Alerts"), or a scheduled transform-job (`mb skills path transform`, Read "Transform jobs (schedules)"); a snapshot is an append transform on the job (`entities-and-time.md`). Each control names a threshold and an owner.

Finished example, the verdict and gap table:

```
Reconciled to finance's MRR sheet, August 2026: build 412,300 vs reference 398,100, net +3.6%, gross 16,900, over 1,212 customers.
| bucket | rows | net | gross | share | cause | fixable |
| match | 1,148 | +310 | 1,020 | 6% | rounding | no |
| scope | 19 | +9,400 | 9,400 | 56% | reseller accounts only in build; finance nets them out | yes (D9) |
| classification | 41 | +4,600 | 6,100 | 36% | refunds as negative lines | yes (D3) |
| unexplained | 4 | -110 | 380 | 2% | manual adjustments only in reference | no |
```

## Done when

Every bucket has a cause or an explicit non-attribution; every fix is re-measured; the residual is named with its causes; the controls run unattended.

## Reply

The five-part hand-back in `collaboration-contract.md`; under part three: the verdict in one sentence (how close, which grain, which universe), the gap table, what moved per fix, the ceiling in plain language.
