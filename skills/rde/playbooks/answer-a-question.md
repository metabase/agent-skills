# Answer a question

Applies: the user wants a number or a finding, not a build ("how many", "which", "did it go up"). Produces the answer with its scope stated beside it, tagged `Official` or `Ad hoc`, three checks behind it, the next breakdown pre-empted, and an offer to save it.

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 scope` `2 find the definition` `3 probe` `4 compute` `5 three checks` `6 write` `7 deliver` `reply`.

Read first: [`state.md`](../references/state.md) and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`; `q()` is sourced from `./.scratch/probe.sh`.

```bash
mb search "<the user's words>" --models metric,measure,segment,dataset --db-id $DB
mb card get <id> --fields name,description,dataset_query          # what the definition already excludes
q "SELECT count(*) AS n FROM <schema.table>"
q "SELECT <column>, count(*) AS n FROM <schema.table> GROUP BY 1 ORDER BY 2 DESC LIMIT 50"
cat > ./.scratch/a.json <<'JSON'
{"lib/type":"mbql/query","database":3,"stages":[{"lib/type":"mbql.stage/mbql","source-table":909,
  "aggregation":[["metric",{},305]],
  "filters":[["time-interval",{},["field",{},1717],"last","month"]],
  "breakout":[["field",{},1719]]}]}
JSON
mb query --file ./.scratch/a.json --dry-run; mb query --file ./.scratch/a.json --fields status,data.rows
q "SELECT sum(n) FROM (<the breakdown query>) b"                  # reconstruction: breakdown sums to the total
mb card create --file ./.scratch/saved.json                       # the offer to save, when accepted
```

A measure is `["measure",{},<id>]` in the same slot; a segment is `["segment",{},<id>]` in `filters`.

## 1. Scope silently, state the scope in the answer

Pick the reading a reasonable colleague would mean: the population, the period and its date column, the exclusions. Write it as one sentence; it appears verbatim beside the number. The pick is `[DECIDED, reversible]`. Ask before computing only when two readings differ materially, and then with both numbers in hand.

## 2. Find what exists

STATE.md Questions first, then `mb search`. A metric or measure found makes the answer `Official`; none makes it `Ad hoc`. Then the table whose grain matches: one row per order answers "how many orders", and "how many customers" only as a distinct count. Prefer a final-layer table; raw tables needing a join: say so and offer [`build-clean-tables.md`](build-clean-tables.md).

## 3. Probe small

`count(*)` and the distinct values of every column you will filter or group by, before either enters the query. The row ceiling and the extract path: `profiling-catalog.md`.

## 4. Compute through the definition

Where step 2 found a metric or measure, aggregate it by id with the question's filters and breakout, so the chat answer equals the dashboard's. Native SQL is for questions no definition covers, and using it there is a gap logged in STATE.md Questions. Group where the next breakdown is one clause away.

## 5. Three checks, inline

A denominator: the total the number is a share of. A null bucket: rows where the filtered or grouped column is null or blank; a large one is often the finding. A reconstruction: the breakdown summed equals the total, or the population counted off a related table through its key. Disagreement is reported, never resolved by picking the friendlier number; a cause that is an undecided business rule is a `[CHECKPOINT]`.

## 6. Write the answer first

One sentence with the number, its denominator, and its period, in the user's words, tagged; then the scope sentence; then the breakdown they will ask for next; then only the caveats that change the reading. Personal data per the contract. Offer the query rather than pasting it.

## 7. Deliver in the form asked for

A number in chat needs nothing else. Offer to save it as a question or, if it will be asked again, to define it in [`build-semantic-layer.md`](build-semantic-layer.md). A written finding is a document: `mb skills path document`, Read "Body shape (create / update)".

Finished example, an answer:

```
Ad hoc. 41 customers churned in August 2026 out of 1,212 paying at the start of the month (3.4%).
Scope: paying accounts, churn dated by service end, trials and internal accounts excluded.
By plan: plan_basic 29, plan_plus 9, plan_pro 3.
Checked: 41 + 1,171 retained = 1,212; 0 rows with a null plan; 41 again by counting subscriptions whose end fell in August.
Caveat: 6 of the 41 reactivated in September and move to "paused" once D7 is answered.
Save this as a question, or define churn officially?
```

## Done when

The scope sentence sits beside the number; the answer comes from a definition or from a table whose grain you can state; the three checks are recorded; the form asked for is built and nothing else.

## Reply

The five-part hand-back in `collaboration-contract.md`, collapsed to the answer above when nothing else changed; under part three: the scoping choices made for them and what each check returned.
