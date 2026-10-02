# Reconciliation

Read whenever a build produces a number somebody will compare with another, or two numbers in the instance already disagree.

## Pick a baseline at intake

- Ask for the reference at intake: an export at the finest grain available, from an existing report, a file, or a finance figure. Never fabricate one.
- Search the warehouse for baseline-shaped tables before asking (the baseline probe in [profiling-catalog.md](profiling-catalog.md)); present candidates, let the user disqualify.

Disqualify explicitly: entity coverage a small fraction of the build's scope; no actual rows, only forecast or forward-filled ones; an earlier build of the same specification; a grain mismatch bridged by a mapping that is itself unvalidated.

## Validation mode

Declare the mode before comparing; it fixes what a pass rate may mean, and the trust label ([collaboration-contract.md](collaboration-contract.md)) reads from it.

| Mode | When | What a pass rate proves |
| --- | --- | --- |
| `external_baseline` | An independent row-level reference exists | Correctness; a shared upstream error agrees on both sides, so record a shared upstream |
| `source_parity` | The reference is the user's own existing model output, or another number already in the instance | Translation fidelity only; say so wherever the number appears |
| `none` | No baseline | Nothing about correctness; the checks prove self-consistency, and the report says so |

Two numbers in the instance disagreeing ("the dashboard says X, the report says Y") is `source_parity` with the metric as the reference: read both definitions (`mb card get <id> --fields name,dataset_query --json`), compare at the narrowest grain below, attribute the gap to the buckets, and the fix is one definition: the card that re-derived the number is re-pointed at the metric ([semantic-layer-design.md](semantic-layer-design.md)).

## Filter the baseline to the build's scope first

Apply each filter with its reason recorded: categories the build recognises, actual rows, complete periods. Assert any exclusion both sides claim to apply. Rows outside the reference's own scope go in `scope` below, not the error.

## Compare at the narrowest common grain

Compare at the grain the model produces; roll up only after the narrower comparison passes. Join on a declared key both sides carry, full outer, never inner; an aggregate match hides compensating errors. The comparison is a transform so it re-runs after every fix:

```sql
SELECT coalesce(r.k, b.k) AS k, r.value AS reference_value, b.value AS build_value, b.value - r.value AS gap,
       CASE WHEN r.k IS NULL THEN 'only_in_build' WHEN b.k IS NULL THEN 'only_in_reference'
            WHEN abs(b.value - r.value) <= <tolerance> * abs(r.value) THEN 'match' ELSE 'differ' END AS state
FROM <reference> r FULL OUTER JOIN <build> b ON b.k = r.k
```

- Report agreement at several tolerances (defaults to confirm: exact, 1, 5, 10 percent).
- Acceptance is a pair, a row-level hit rate and an aggregate gap cap, both defaults the user confirms; passing one and failing the other is a finding.
- Deliver the row-level file: one row per compared key with both values, gap, state, and context columns; say what was excluded and why.

## Decompose the gap

Attribute every non-`match` row to one bucket with an ordered `CASE`, each disputed threshold a named constant; per bucket report rows, signed and absolute contribution, share of total absolute gap.

| Bucket | Contents |
| --- | --- |
| `scope` | Rows one side covers and the other structurally does not |
| `timing` | Same value, different period |
| `classification` | Same value, different category or dimension |
| `dedup` | Rows one side collapses and the other does not, or one-sided eligibility |
| `unexplained` | Not yet attributed to a rule |

- Report net and gross separately; a near-zero net over a large gross means offsetting buckets, a grain or attribution problem.
- Read the top rows by absolute gap; attribute each bucket to a rule in your build or theirs; compare the classification column too, as a confusion matrix.
- Re-measure after every fix against the same reference and universe; report total absolute gap, hit rate, and each misclassification count before and after, per direction.
- A gap from past periods carrying the entity's current attribute needs a history source ([entities-and-time.md](entities-and-time.md)); a reference covering one segment where the build covers several is scope, not error.

## Declare the ceiling instead of closing it

Before the build runs, list by name everything in the baseline the inputs cannot produce, with reason and effect; a residual attributable to that list is a correct result. Keep a separate list of logic deliberately deferred; never conflate "cannot" with "chose not to". When the remaining gap is dominated by data the source does not carry, say so and stop. Closing a gap with logic not in the specification is the user's decision, never a rule you invent.

## Reconcile by construction without a baseline

- State table: one row per entity, sub-entity, category, and period on the dense spine ([entities-and-time.md](entities-and-time.md)) with the period value, every dimension key, exclusions as flagged columns not `WHERE` clauses.
- Motion table: one row per entity, period, and change type, derived only from the state table, so that `prior_period_value + sum(change rows for the period) = current_period_value`.
- A delta the classifier cannot explain becomes an `unexplained` row; its share is the headline quality measure, and an empty bucket in a messy domain means the plug is not wired.
- Label the identity holding as structural: the arithmetic closes; the figures are not thereby right.

## Snapshot and restatement

Snapshot table: an append incremental transform on the job, run on the first day of each period (the `snap_` shape in [entities-and-time.md](entities-and-time.md)), one row per entity, period, and snapshot date, so past snapshots survive the next run. Restatement table: one row per entity, period, and snapshot date where the value moved, with the delta; nothing shows until two snapshots exist. A restatement that moves a shipped number follows the restatement protocol in [collaboration-contract.md](collaboration-contract.md).

## Standing controls

Defaults shipped with every reconciled number, each an alert on a saved question that returns rows only on failure ([data-quality-checks.md](data-quality-checks.md)): freshness (stale beyond the refresh interval, tighter at period open) and structural integrity (duplicate on the grain, orphan, negative amount, broken identity).

On request, or after a first incident: restatement detection (a closed period moved beyond a small relative threshold, read from the restatement table); residual size (`unexplained` share above a threshold); an independent crosscheck (the same measure from another input path, variance broken down by cause, never swapping the reported number for the preferred one); one assertion per past incident. A crosscheck whose divergence is explained rather than measured is an open question, not a control.
