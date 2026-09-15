# Modeling decisions

Read when a model meets duplicates, history, a disputed attribute, or a period grouping.

## Which row wins

Declare in the model header and the decision ledger before writing SQL: the collision grain, the key duplicates reduce to (`[customer_id, period_month]`), and the collision order, the tiebreaker list (`is_partial ASC, period_end_at DESC, loaded_at DESC`). Never resolve a collision with `SELECT DISTINCT` or a bare `GROUP BY`.

| Family | Right when | Wrong when |
|---|---|---|
| Latest by time (`loaded_at DESC`, `updated_at DESC`, `period_end_at DESC`) | Later rows supersede earlier ones: a re-synced record, a status that only advances | A later row is a fragment of the same event (a trailing correction): recency picks the less complete row |
| Preferred by attribute (`is_partial ASC` then `amount DESC`, or a ranked category then a measure) | One row is structurally more authoritative: complete over fragment, settled over pending | The replacement is legitimately smaller (a downgrade): "largest wins" keeps the stale figure |

Neither family applies silently. Where the data contains the case that breaks the chosen family, write an explicit rule for it (stop carrying a value forward when a reducing record exists). Checkpoint: the family, the breaking case, its count.

Prefilter before ranking, as part of the rule: a group of only fragments keeps all; one non-fragment is resolved; several narrow to the qualifying ones (a positive amount), then rank and keep rank 1. Flag losers with `is_selected`; never delete them.

```sql
SELECT t.*, row_number() OVER (PARTITION BY customer_id, period_month ORDER BY is_partial ASC, amount_usd DESC, loaded_at DESC) = 1 AS is_selected
FROM int_acme_candidate t;
```

- One column of the winner: `first_value(...) OVER (PARTITION BY ... ORDER BY ...)`, never a self-join or a warehouse-specific maximum-by function.
- Two-level preference in one pass: rank on `category_rank * 1000000000 + amount_usd`, the rank held in a lookup column, not a `CASE` copied across models; comment the multiplier.

Latest load wins on a loader that appends versions is mechanical once duplicates and parity are measured; every other collision is a checkpoint (block in [collaboration-contract.md](collaboration-contract.md)): report the volume (groups over one row, rows, share), show two or three groups with the differing columns, offer at least two candidate rules and what each changes. Check every enrichment join's right-hand side for uniqueness first; a many-sided right hand is never resolved alone. Once agreed: record it, apply it once, state resulting counts in the hand-back.

When the source keeps history, do not reduce to one row per key; resolve as of the moment that matters: half-open window, null end on the open interval (never a far-future date), overlap per key checked before the join, match rate after. Report a history table in the hand-back.

```sql
FROM mart_acme_fct_order f
LEFT JOIN int_acme_plan_history h ON h.customer_id = f.customer_id AND f.ordered_at >= h.valid_from_at AND (h.valid_to_at IS NULL OR f.ordered_at < h.valid_to_at)
```

## Which column is authoritative

| Prefer | Over | Rule |
|---|---|---|
| The line item | The document header | A header is mutated in place; line items state what was true when issued |
| The immutable reference (the price or plan record the line points at) | A denormalized copy on a mutable parent | Every copy is suspect until tested |
| The dominant child, weighted by value | The first, last, or most common child | `first_value` per document ordered by `amount_usd DESC`; tag and exclude add-on lines first; ties on a composed rank |
| A validity-window join | Tagging history with the entity's current attribute | Current state is wrong for every period before the attribute last changed |

The test; a non-zero count is a checkpoint before choosing: `SELECT count(*) FROM int_acme_line_item li JOIN stg_acme_price p ON p.price_id = li.price_id JOIN stg_acme_agreement a ON a.agreement_id = li.agreement_id WHERE p.recurring_interval <> a.copied_interval`.

Where no single column answers every row, write `coalesce(signal_1, signal_2, default_value)`, rungs ordered by specificity to the row: its own immutable reference, its own observable property (period length, item count), the parent's current value, a stated default. Each rung returns null when it cannot answer.

- A heuristic sits behind anything that states the answer directly, never in front.
- Encode a heuristic as bounded ranges with gaps, read off the profiled distribution (`BETWEEN low_a AND high_a` class a, `BETWEEN low_b AND high_b` class b, else null), never as nearest match.
- The rung order is a checkpoint: propose it with rows resolved per rung and rows falling through to the default; never copy a ladder from another build.
- Emit `<attribute>_source` naming the rung that fired.
- When changing a rung, count each misclassification direction separately before and after; a lower total that grows the opposite error is no improvement.

Two guards at the point of derivation: clamp a physically bounded measure, `greatest(x, 0)`, and report the rows changed (a large count means the derivation is wrong); write negative filters null-safe, `(email IS NULL OR NOT (email LIKE '%@example.com'))`.

Every classification with business meaning (free text onto a scale, which statuses count, correction versus new event) is on the always-stop list ([collaboration-contract.md](collaboration-contract.md)).

When the source keeps no history and no change log: state the ceiling on what the model can answer; quantify the exposure (entities whose attribute could have changed, share of the measure they carry); offer the two ways forward: current-state labelling documented on the model, or capturing history from now on.

## The last complete period

Exclude the incomplete trailing period end to end: no model emits a row past the declared last complete period. Assert it in the first model that materializes periods: `max(period_month)` past the last complete period fails.

Detect it with both detectors, never the calendar alone:

| Detector | Query | Partial when |
|---|---|---|
| Maximum source date | `SELECT max(event_at) FROM stg_acme_order;` | The result lands before the end of its period |
| Volume floor | `SELECT date_trunc('month', event_at), count(*), count(DISTINCT customer_id) FROM stg_acme_order GROUP BY 1 ORDER BY 1 DESC LIMIT 13;` | Newest period's rows or entities below a floor of the trailing average; default 80 percent, confirmed as a checkpoint |

Record beside the decision: newest period's counts, trailing average, ratio, days the maximum source date lags.

A stale loader is a build failure, not churn. Fail the build when `current_date - cast(max(event_at) AS date)` exceeds a threshold set from the load's cadence, tightened around the period boundary, a named constant in one place. On failure stop and say the data has not arrived and this is a pipeline problem; never build downstream on it, never shorten the horizon silently.

The cap on a periodic model is `cap_period = min(<latest period the model can legitimately produce>, <last complete period>)`: the first term removes rows forward-looking logic dates past today, the second the partial period; both apply. Define it once, named; every model reads it:

- Dense spine: each entity's upper bound is `min(<entity's own last relevant period> + 1, cap_period)`, never the maximum date present.
- Rollup: filter `period <= cap_period` before grouping.
- Period-over-period: only periods at or below the cap.

Every hand-back with a periodic model says in plain words which period is last complete and why ("Numbers run through March; April is partly loaded and left out everywhere"); the same fact goes in the model's description and header. When the stop is a stale load, say that, and what has to happen for the newest period to appear.
