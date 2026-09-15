# Answer a question

Applies when the user wants a number or a finding rather than a build ("how many", "which", "did it go up"); produces a written answer in plain language with its scope stated, at least three cross-checks behind it, and the durable form the user asked for, if any. The deliverable is the answer, not a chart.

Read first: [`collaboration-contract.md`](../references/collaboration-contract.md), the semantic-checks section of [`data-quality-checks.md`](../references/data-quality-checks.md), the row-ceiling note in [`profiling-catalog.md`](../references/profiling-catalog.md), and `mb skills get core`.

## 1. Scope the question

Settle four things in one short message, your lean stated so the user can just confirm: the population (everyone, or only active, confirmed, paying, non-test); the period and the date column it is measured on; the status filters and exclusions (cancelled, refunded, staff, test rows); the form the answer takes (a number in chat, a written finding, a saved question, a dashboard card, or an official definition).

Check: you can restate the question with population, period, and filters in one sentence, and the user agreed to it and to the form. Two readings that give materially different numbers is a checkpoint (block in [`collaboration-contract.md`](../references/collaboration-contract.md)), not a pick.

## 2. Find what exists, then pick the grain

Search for an existing definition first: `mb search "<term>" --models metric,dataset,segment,measure --json`; an official number is used, never re-derived. Then pick the table whose grain matches the question: one row per order answers "how many orders", and "how many customers" only as a distinct count. Prefer a final-layer table over a raw table; if only raw tables exist and the question needs a join, say so and offer [`build-clean-tables.md`](build-clean-tables.md) first.

Check: you can say "one row per ___" for the table, and what you count is that thing or a distinct count of a column on it.

## 3. Probe small

`count(*)` and a handful of rows first, then the distinct values of every column you will filter or group by. Aggregate in SQL; the row ceiling and the full-extract path are in `profiling-catalog.md`. Check: no column enters a filter or a `GROUP BY` before you have seen its values.

## 4. Compute

Write the query the scoped sentence calls for, run it, keep the exact query beside the number. Group where a breakdown is one clause away. Check: the query implements the sentence from step 1 filter for filter; if not, the sentence changed and the user has not been told.

## 5. Cross-check

Run at least three, plus whatever the semantic checks in `data-quality-checks.md` add for this shape of question:

- A denominator: the total the number is a share of.
- A null check: rows where the filtered or grouped column is null or blank; a large null bucket is often the finding.
- A reconstruction: the same number a second way, summing the breakdown to the total or counting the population off a related table through its key.

Disagreement between paths is reported, not resolved by picking the friendlier one; a cause that is an undecided business rule is a checkpoint. Check: denominator, null count, and second path are written beside the answer.

## 6. Write the answer first

One sentence with the number, its denominator, and its period, in the user's words; then only the caveats that change how it reads: what was excluded, what was null, where the period was cut, what the number is not. Offer the query rather than pasting it. For free-text data, quote several real responses beside the count. Check: the first sentence alone gives a correct impression; the caveats contradict nothing in it.

## 7. Deliver in the form asked for

Build exactly the form step 1 settled and nothing unasked. A question asked more than once gets the recommendation to define it ([`build-semantic-layer.md`](build-semantic-layer.md)).

## Done when

The scoped sentence and the form are confirmed; the answer comes from a table whose grain you can state; the three cross-checks are recorded; the written answer leads with the number in context; the form asked for is built and nothing else.

## Reply

The answer in one sentence with denominator and period; the breakdown as a short table if there is one; the few caveats that change its reading; one line on what it was checked against; the link to the saved form when one was asked for; any scoping decision you made for them.
