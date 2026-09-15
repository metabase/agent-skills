# Reconciliation

Read this whenever a build produces a number somebody will compare with another.

## Pick a baseline at intake

- Ask for the reference at intake: an export at the finest grain available, from an existing report, a file, or a finance figure. Never fabricate one.
- Search the warehouse for baseline-shaped tables before asking whether one exists ([profiling-catalog.md](profiling-catalog.md)); present candidates, let the user disqualify.
- Record per candidate: origin, producer, grain, period and entity coverage, pull date, the key both sides carry.

Disqualification tests, applied explicitly:

1. Entity coverage is a small fraction of the build's scope: a different book of business.
2. No actual rows to compare, only forecast or forward-filled ones.
3. An earlier build of the same specification: a build compared to itself proves nothing.
4. Grain mismatch bridged by a mapping that is itself unvalidated.

## Validation mode

Declare the mode before comparing; it fixes what a pass rate may mean.

| Mode | When | What a pass rate proves |
| --- | --- | --- |
| `external_baseline` | An independent row-level reference exists | Correctness; if it shares the build's upstream, record that a shared upstream error agrees on both sides |
| `source_parity` | The reference is the user's own existing model output | Translation fidelity only; say so wherever the number appears |
| `none` | No baseline | Nothing about correctness; the checks prove self-consistency, and the report says so |

A figure computed outside the warehouse (a document, a tracker, an accounting system) is a crosscheck, never a system of record: mark a fill from it as flagged, not merged; quantify what it covers; the decision to depend on it is the user's governance call. A mirrored copy inside the warehouse gets the same treatment plus a recorded canonical variant and a freshness date per file.

## Filter the baseline to the build's scope first

Apply each filter with its reason recorded: categories the build recognises, actual rows, complete periods. Assert any exclusion both sides claim to apply. Rows outside the reference's own scope go in the `scope` bucket below, not the error.

## Compare at the narrowest common grain

- Compare at the grain the model produces; roll up only after the narrower comparison passes.
- Join on a declared key both sides carry, full outer, never inner. An aggregate match hides compensating errors.

| State | Meaning |
| --- | --- |
| `match` | Both present, within tolerance |
| `differ` | Both present, beyond tolerance |
| `only_in_reference` | The reference has the row, the build does not |
| `only_in_build` | The build has the row, the reference does not |

- Report agreement at several tolerances (defaults to confirm: exact, 1, 5, 10 percent).
- State acceptance as a pair, a row-level hit rate and an aggregate gap cap, both defaults the user confirms; passing one and failing the other is a finding.
- Deliver the row-level file: one row per compared key with reference value, build value, signed gap, absolute gap, percentage difference, state, and context columns for a domain expert. Say what was excluded and why.

## Decompose the gap

Per bucket: row count, signed and absolute contribution, share of total absolute gap.

| Bucket | Contents |
| --- | --- |
| `scope` | Rows one side covers and the other structurally does not |
| `timing` | Same value, different period |
| `classification` | Same value, different category or dimension |
| `dedup` | Rows one side collapses and the other does not, or one-sided eligibility |
| `unexplained` | Not yet attributed to a rule |

- Report net and gross separately; never let the net stand alone. A near-zero net over a large gross means offsetting buckets, a grain or attribution problem. State the universe the figure covers.
- Sort by absolute gap and read the top rows; list top entities by absolute gap with bucket and period; attribute each bucket to a rule in your build or theirs.
- Compare the dimensions too: agreement on the classification column, with a confusion matrix of mismatches.
- Re-measure after every fix against the same reference and universe; keep a trajectory table of total absolute gap, hit rate, and each named misclassification count. A classifier change reports before and after counts per direction of misclassification.

| Root cause | Fixable from the source? |
| --- | --- |
| Every period tagged with the entity's current attribute | No, needs a history source |
| Eligibility or dedup rules the reference applies and the build does not | Partly, once stated |
| A driver sourced from a system the warehouse does not hold | No |
| Reference covers one segment, build covers several | Out of scope, not an error |

## Declare the ceiling instead of closing it

- Before the build runs, list by name everything in the baseline the inputs cannot produce, with reason and effect. A residual attributable to that list is a correct result, not a failure.
- Keep a separate list of logic deliberately deferred; never conflate "cannot" with "chose not to".
- When the remaining gap is dominated by data the source does not carry, say so and stop.
- Closing a gap with logic not in the specification is a checkpoint (block in [collaboration-contract.md](collaboration-contract.md)), never a rule you invent.

## Reconcile by construction without a baseline

- State table: one row per entity, sub-entity, category, and period with the period value, any annualised figure, every dimension key, exclusions as tagged columns not `WHERE` clauses, and a lineage column naming the computation path.
- Motion table: one row per entity, period, and change type, derived only from the state table, never from source, so that `prior_period_value + sum(change rows for the period) = current_period_value`.
- A delta the classifier cannot explain becomes an `unexplained` row. Its share is the headline quality measure; an empty bucket in a messy domain means the plug is not wired.
- Classification lives in one ordered function; each disputed threshold is a named constant.
- Label the identity holding as structural: the arithmetic closes; the figures are not thereby right.

## Snapshot and restatement

Run both as a scheduled transform-job (`mb skills get transform`):

- Snapshot table: on the first day of each period, the state table as reported, kept permanently; daily for a short window if volume permits.
- Restatement table: one row per entity, period, and snapshot date where the value moved, with the delta. The goal is visibility, not zero; nothing shows until two snapshots exist.

## Standing controls

Ship these with the model, each with a status so unbuilt ones are visible. Mechanisms: an alert on a saved question (`mb skills get notification`) or a scheduled transform-job (`mb skills get transform`). Every threshold is a default the user confirms.

| Control | Threshold | Mechanism |
| --- | --- | --- |
| Freshness | Stale beyond the normal refresh interval, tighter at period open | Saved-question alert |
| Restatement detection | Any closed period moved by more than a small relative threshold | Transform-job writes the restatement table; alert on it |
| Residual size | `unexplained` share of gross movement above a threshold | Saved-question alert |
| Self-consistency | Reconciliation identity not exactly zero | Saved-question alert |
| Structural integrity | Any duplicate on the grain, orphan, broken invariant, or negative amount | Saved-question alert |
| Independent crosscheck | The same measure from another input path diverges; variance broken down by likely cause; never swap the reported number for the preferred one | Transform-job plus alert |
| Incident assertions | One assertion per past incident; every new incident adds one | Saved-question alert |

A crosscheck whose divergence is explained rather than measured is an open question, not a control; record it unresolved.
