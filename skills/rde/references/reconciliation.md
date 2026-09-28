# Reconciliation

The method behind `playbooks/reconcile.md`.

## Validation modes

Declared before comparing; the trust label reads from it.

| Mode | When | A pass proves |
| --- | --- | --- |
| `external_baseline` | a reference outside the build: a finance export, a source-system report, a table marked `data_authority: authoritative` | agreement with it for the scope and period compared, within the acceptance pair; a shared upstream error agrees on both sides, so name any shared upstream |
| `source_parity` | the build against its own raw source, or one definition against another in the instance | nothing lost or duplicated, or faithful translation; nothing about whether the definition is right |
| `none` | no reference | self-consistency only, said so |

Two numbers in the instance disagreeing is `source_parity` with the metric as reference: read both queries (`mb card get <id> --fields name,dataset_query`), compare at the finest grain, bucket the gap; the fix is one definition, the re-deriving card re-pointed at the metric.

## Baselines and disqualifiers

Search for baseline-shaped and `authoritative` tables before asking; then ask once for a reference at its finest grain, keyed by something both sides carry. Never fabricate one. With two owners holding different references, which is canonical is theirs.

Not a baseline: computed from this build or an earlier build of the same spec; another definition (billed vs recognised, bookings vs revenue) with no bridge; a period open at export or restated since; an unconvertible currency or FX basis; coverage a small fraction of the scope; forecast or forward-filled rows; grains bridged by an unvalidated mapping; totals only. Name the disqualifier and fall back to `source_parity`.

## Scope the reference

Read what it counts first: population (statuses, test and internal accounts, entities, subsidiaries), date column and cut-off, timezone, currency, net of refunds, credits, tax. Match the build to it in the comparison query, never by editing the definition; each filter carries its reason; rows outside the reference's scope land in `scope`, not error. One sentence states the comparison universe every figure is quoted against.

## The acceptance pair

A row hit rate (reference rows matched within tolerance) and a cap on the aggregate gap (net gap over the reference total), set with the owner before the first measurement and never moved after. High hit rate with a large net gap: a missing population. Small net gap with a low hit rate: offsetting errors. Report agreement at several bands (defaults to confirm: exact, 1, 5, 10 percent).

## The roll-forward identity first

Before any external comparison and after every fix: opening + movements = closing per entity and period (opening MRR + new + expansion + reactivation − contraction − churn = closing MRR; opening balance + credits − debits = closing). A query returning rows only where it breaks; any row is a build bug, fixed before the reference is looked at again.

## Compare at the finest shared grain

The finest grain both sides carry (invoice line, invoice, customer-month), the key named the same on both sides. Full outer join, never inner, never totals alone. The comparison is a transform, `cmp_<number>`, `data_layer: internal`, so it re-runs after every fix:

```sql
SELECT coalesce(r.k, b.k) AS k, r.value AS reference_value, b.value AS build_value, b.value - r.value AS gap,
  CASE WHEN r.k IS NULL THEN 'only_in_build' WHEN b.k IS NULL THEN 'only_in_reference'
       WHEN abs(b.value - r.value) <= <tolerance> * abs(r.value) THEN 'match' ELSE 'differ' END AS state,
  CASE WHEN <outside the reference's scope> THEN 'scope' WHEN <same row, other period> THEN 'timing'
       WHEN <same row, other amount or category> THEN 'classification' WHEN <duplicate on one side> THEN 'dedup'
       WHEN abs(coalesce(b.value, 0) - coalesce(r.value, 0)) > <tolerance> * abs(coalesce(r.value, 0)) THEN 'unexplained' END AS bucket
FROM <reference> r FULL OUTER JOIN <build at the same grain> b ON b.k = r.k
```

Summary: `SELECT c.state, c.bucket, count(*) AS n, sum(c.gap) AS net, sum(abs(c.gap)) AS gross FROM <out_schema>.cmp_<number> c GROUP BY 1, 2`. Roll up only after the row level passes. The row-level file, on request: a native question over the comparison table, `mb card query <card-id> --export-format csv`.

## Decompose the gap

Every non-match in exactly one bucket by the ordered `CASE`, disputed thresholds named constants; per bucket rows, net, gross, share of total absolute gap; buckets sum to the total.

| Bucket | Contents |
| --- | --- |
| `scope` | a row only one side's population holds |
| `timing` | the same row in another period (date basis, cut-off, timezone, late row) |
| `classification` | the same row with another amount or category (discounts, tax, refunds, FX, proration) |
| `dedup` | a duplicate on one side, or one-sided eligibility |
| `unexplained` | what is left, with sample rows |

Near-zero net over a large gross means offsetting buckets (a grain or attribution problem). Read the top rows by absolute gap one by one; compare classification columns as a confusion matrix, not only the measure. A gap from past periods carrying current attributes needs history (`references/time-and-entities.md`). Every headline count is computed from the comparison table, never remembered.

## Fix one rule, re-measure

One rule per fix, through `playbooks/change.md`; the row that exposed it becomes a test case first. Re-run under the same reference and universe and compare buckets per direction: the fix closes its bucket and moves no other (moving another is a bug). Closing a gap with logic the definition does not hold is the owner's call; never tune a rule only to hit the reference.

## The ceiling

What remains, in two parts with sizes: what the sources cannot close (data not held, history before the horizon, manual adjustments only in the reference) and what was chosen not to close (an owner's rule that differs). Never conflate them; when the first dominates, say so and stop.

## Reconcile by construction, without a baseline

- State table: one row per entity, sub-entity, category, period on the dense spine, exclusions as flagged columns, not `WHERE` clauses.
- Movements table derived only from the state table, so the roll-forward holds; a delta the classifier cannot explain is an `unexplained` movement whose share is the headline quality measure (an empty bucket in a messy domain means the plug is not wired).
- Say what the identity proves: the arithmetic closes; the figures are not thereby right.

## Snapshots and restatement

Snapshot: an append incremental transform on the job, run the first day of each period, one row per entity, period, snapshot date. Restatement table: rows where a value moved between snapshots, with the delta (empty until two snapshots exist). A restatement that moves a shipped number follows `playbooks/change.md` §5.

## Standing controls

With every reconciled number, as branches of the domain's check card and its alert (`references/quality-checks.md`, The standing check): freshness, structural integrity, the roll-forward identity, and the aggregate gap against a refreshed reference when one arrives on a cadence. On request or after an incident: restatement detection (a closed period moved beyond a small threshold), the unexplained share above a threshold, an independent crosscheck (the same measure by another path, variance by cause, never swapping the reported number for the preferred one), one assertion per past incident. A divergence explained rather than measured is an open question, not a control. Each control names a threshold and an owner.
