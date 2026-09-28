# Answer a question

Applies when the user wants a number or a finding, not a build. Produces a short answer read at a glance: the number with its period, tagged Official or Ad hoc, one scope sentence, the checks in one clause, the next breakdown pre-empted, an offer to save.

Read first: nothing more; the domain note's For answering when one fires.

Order: 1 resolve and find, 2 scope, 3 probe, 4 compute, 5 check, 6 write, 7 deliver.

## 1. Resolve and find

Most governed source first: a verified question (`mb search "<words>" --verified`), a metric, a measure, a saved card, MBQL on a final or published table, raw SQL. A metric or measure makes it Official, anything else Ad hoc. Read the definition's description and its table's description and caveats (grain, scope, required filters). Match the grain: one row per order answers "how many orders"; "how many customers" only as a distinct count. Nothing modeled covers it: SQL on raw tables through `q()`, stated Ad hoc and unverified. Nothing here can answer it: say so and name the definition that should exist.

## 2. Scope silently, state the scope

The reading a reasonable colleague would mean (population, period and its date column, exclusions, every `required filters:` line) as one sentence beside the number. Two plausible readings: give both numbers with the assumption; ask first only when they differ materially (relative to the number and past an absolute floor), with both numbers in hand.

## 3. Probe small

`count(*)` and the distinct values of every column you will filter or group by; every literal read from the data (`mb field values <id>`), never guessed. Ceilings and extracts: `references/profiling.md`.

## 4. Compute through the definition

Aggregate the definition by id with the question's filters and breakout, so chat equals the dashboard:

```json
{"lib/type": "mbql/query", "database": <db-id>, "stages": [{"lib/type": "mbql.stage/mbql", "source-table": <table-id>,
  "aggregation": [["metric", {}, <metric-id>]],
  "filters": [["segment", {}, <segment-id>], ["time-interval", {}, ["field", {}, <time-field-id>], "last", "month"]],
  "breakout": [["field", {}, <breakout-field-id>]]}]}
```

A measure takes the slot as `["measure", {}, <id>]`; definition references run with `--skip-validate` (`SKILL.md`, mb conventions). Group where the next breakdown is one clause away. No rows means replan; a result at the ceiling means more rows may exist.

## 5. Three checks

A denominator (the total it is a share of); a null bucket (rows where a filtered or grouped column is null or blank, often the finding); a reconstruction (the breakdown sums to the total, or the population counted off a related table). Agreement is one clause; disagreement is reported, never resolved by picking the friendlier number; an undecided business rule behind it is a question to the user.

## 6. Write it

The number in the user's words with period, denominator for a share, and tag; the scope sentence; the checks in a clause; the next breakdown; only caveats that change the reading. Names with links, never ids; personal data aggregated or masked; offer the query rather than pasting it. Free text: quote real responses grouped by theme, with counts.

```
Official. 1,284 orders in August 2026, placed August 1–31 by order date, test orders excluded.
Checked: channel breakdown sums to the total; no orders without a channel.
By channel: web 902, marketplace 311, phone 71.
Save this as a question, or split it by region?
```

## 7. Deliver in the form asked for

A number in chat needs nothing else; offer to save it (`mb card create`). An Ad hoc number asked a second time, or computed a second way, earns one offer to define it (`playbooks/semantic.md`), never repeated once declined. A written finding is a document (`document` skill).

## Done when

The number comes from a definition or a table whose grain you can state; the scope sentence sits beside it; the three checks ran; the form asked for is delivered and nothing else.
