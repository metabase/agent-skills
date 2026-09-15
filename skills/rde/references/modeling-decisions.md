# Modeling decisions

Read when a model meets duplicate rows, a disputed attribute, or a period grouping; entity conformance, history, the spine, and retention are in [entities-and-time.md](entities-and-time.md).

## Which row wins

Declare in the model header and in STATE.md's Decisions table ([state.md](state.md)) before writing SQL: the collision grain, the key duplicates reduce to (`[customer_id, period_month]`), and the tiebreaker list in order (`is_partial ASC, period_end_at DESC, loaded_at DESC`). Never resolve a collision with `SELECT DISTINCT` or a bare `GROUP BY`.

| Family | Right when | Wrong when |
|---|---|---|
| Latest by time (`loaded_at DESC`, `updated_at DESC`, `period_end_at DESC`) | Later rows supersede earlier ones: a re-synced record, a status that only advances | A later row is a fragment of the same event (a trailing correction): recency picks the less complete row |
| Preferred by attribute (`is_partial ASC` then `amount DESC`, or a ranked category then a measure) | One row is structurally more authoritative: complete over fragment, settled over pending | The replacement is legitimately smaller (a downgrade): "largest wins" keeps the stale figure |

Where the data contains the case that breaks the chosen family, write an explicit rule for it (stop carrying a value forward when a reducing record exists) and record the family, the breaking case, and its count.

Prefilter before ranking: a group of only fragments keeps all; one non-fragment is resolved; several narrow to the qualifying ones (a positive amount), then rank and keep rank 1. Flag losers with `is_selected`; never delete them.

```sql
SELECT t.*, row_number() OVER (PARTITION BY customer_id, period_month ORDER BY is_partial ASC, amount_usd DESC, loaded_at DESC) = 1 AS is_selected
FROM int_acme_candidate t;
```

One column of the winner: `first_value(...) OVER (PARTITION BY ... ORDER BY ...)`, never a self-join or a warehouse-specific maximum-by function.

Latest load wins on a loader that appends versions is mechanical once duplicates and parity are measured ([staging-rules.md](staging-rules.md)). Every other collision is a reversible decision under [collaboration-contract.md](collaboration-contract.md): report the volume (groups over one row, rows, share), show two or three groups with the differing columns, name the rule taken and what the alternative changes to the headline. Check every enrichment join's right-hand side for uniqueness first; a many-sided right hand is never resolved alone.

When the source keeps history, do not reduce to one row per key; resolve as of the moment that matters: half-open window, null end on the open interval (never a far-future date), overlap per key checked before the join, match rate after. When it keeps none, build it ([entities-and-time.md](entities-and-time.md)).

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

The test; a non-zero count is a decision before choosing: `SELECT count(*) FROM int_acme_line_item li JOIN stg_acme_price p ON p.price_id = li.price_id JOIN stg_acme_agreement a ON a.agreement_id = li.agreement_id WHERE p.recurring_interval <> a.copied_interval`.

Where no single column answers every row, write `coalesce(signal_1, signal_2, default_value)`, rungs ordered by specificity to the row: its own immutable reference, its own observable property (period length, item count), the parent's current value, a stated default. Each rung returns null when it cannot answer.

- A heuristic sits behind anything that states the answer directly, never in front.
- Encode a heuristic as bounded ranges with gaps, read off the profiled distribution (`BETWEEN low_a AND high_a` class a, `BETWEEN low_b AND high_b` class b, else null), never as nearest match.
- The rung order is a decision: propose it with rows resolved per rung and rows falling through to the default; never copy a ladder from another build.
- Emit `<attribute>_source` naming the rung that fired.
- When changing a rung, count each misclassification direction separately before and after; a lower total that grows the opposite error is no improvement.
- Clamp a physically bounded measure, `greatest(x, 0)`, and report the rows changed; a large count means the derivation is wrong. Write negative filters null-safe: `(email IS NULL OR NOT (email LIKE '%@example.com'))`.

Every classification with business meaning is decided per [collaboration-contract.md](collaboration-contract.md), never settled inside a `WHERE`.

## The flagged incomplete period

Emit the incomplete trailing period and mark it. Every model that materializes periods carries `is_complete_period` (boolean, `period <= last_complete_period`), read from the one named constant `last_complete_period` in `cfg_<domain>` ([layering-and-naming.md](layering-and-naming.md)); no model hardcodes the date.

- Point-in-time state (a balance, an active count, an ending run rate) is valid in the partial row and is the source of every "current" headline.
- Rollups, rates, and period-over-period comparisons read complete periods only: filter `is_complete_period` before grouping.
- Publish a `Complete periods` segment (`mb segment create`, filter `is_complete_period` is true) on every periodic table in the final layer, so a question excludes the partial period with one click; its description names the partial period.
- Assert in the first model that materializes periods that exactly one period per entity has `is_complete_period = false` and that it is the newest: the `period_flag` check in [data-quality-checks.md](data-quality-checks.md).
- The spine's upper bound and `cap_period`: [entities-and-time.md](entities-and-time.md).

Detect the last complete period from the source, never the calendar alone:

| Detector | Query | Partial when |
|---|---|---|
| Maximum source date | `SELECT max(event_at) FROM stg_acme_order;` | The result lands before the end of its period |
| Volume floor | `SELECT date_trunc('month', event_at) AS p, count(*) AS n, count(DISTINCT customer_id) AS entities FROM stg_acme_order GROUP BY 1 ORDER BY 1 DESC LIMIT 13;` | Newest period's rows or entities below a floor of the trailing average; default 80 percent, a default to confirm |

The volume floor applies only when the trailing periods are steady: no period in the trailing twelve below half the average. For a lumpy source use the maximum-source-date detector and the loader's freshness alone, and say so. Record beside the decision: newest period's counts, trailing average, ratio, days the maximum source date lags.

A stale loader is a build failure, not churn. Fail the build when `current_date - cast(max(event_at) AS date)` exceeds a threshold set from the load's cadence, tightened around the period boundary, held as a named constant. On failure stop and say the data has not arrived and this is a pipeline problem; never build downstream on it, never move `last_complete_period` back silently.

Every hand-back with a periodic model says in plain words which period is last complete and why: "Numbers run through March in every rate and trend; the April row is on the table, flagged incomplete, and only the current-state headlines read it." The same sentence goes in the model's description.
