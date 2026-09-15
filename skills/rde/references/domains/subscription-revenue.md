# Subscription revenue

Any recurring-money source (billing, subscriptions, memberships, dues, pledges, recurring gifts); the router sends you here for run rate, churn, or retention. Every rule is a default the revenue owner confirms at a `[CHECKPOINT]` ([../collaboration-contract.md](../collaboration-contract.md)), held in `cfg_<domain>` ([../layering-and-naming.md](../layering-and-naming.md)), never inside a `WHERE`. Tiebreakers, header versus line, the attribute ladder, the flagged incomplete period: [../modeling-decisions.md](../modeling-decisions.md). The dense spine, the conformed customer, retention rates: [../entities-and-time.md](../entities-and-time.md).

## Without invoices

Memberships, dues, pledges, and recurring gifts carry an amount and a period but no invoice lines: apply Inclusion defaults, Stop rule (lapse or cancellation), Corrections (refunded gifts), ARR and the customer rollup (annual giving), Retention states on a donor-period spine, and Semantic checks; skip Recognition basis, Amortisation, Cadence resolution, and True-ups, unless a pledge is paid in instalments across periods, then amortise over the pledge term.

## Probes

Generic shapes, row ceiling, dialect note: [../profiling-catalog.md](../profiling-catalog.md).

| Probe | SQL shape | Decides |
| --- | --- | --- |
| Line-source coverage | `SELECT 'lines' AS src, count(DISTINCT invoice_id) FROM invoice_lines UNION ALL SELECT 'charges', count(DISTINCT invoice_id) FROM charges`, against `count(*) FROM invoices` | which child table supplies line detail |
| Catalogue inventory by materiality | `SELECT p.id, p.name, p.unit_amount, sum(l.amount) AS amount, sum(l.amount) / sum(sum(l.amount)) OVER () AS share FROM prices p LEFT JOIN invoice_lines l ON l.price_id = p.id AND l.created_at >= <trailing_start> GROUP BY 1, 2, 3 ORDER BY amount DESC` | the taxonomy map, exact where material |
| Cadence signal candidates | `SELECT recurring_unit, recurring_count, count(*) FROM prices GROUP BY 1, 2` and `SELECT period_end - period_start AS days, count(*) FROM invoice_lines GROUP BY 1 ORDER BY 1` | the cadence classifier's signal and bands |
| Basis and currency comparison | `SELECT currency, sum(subtotal), sum(total), sum(amount_paid), sum(total - amount_paid) AS uncollected FROM invoices GROUP BY 1` | the measure column; whether to normalise |

## Recognition basis

- List-price MRR (contracted), forward from the subscription: `unit_price * quantity` per month (annual / 12, weekly * 52 / 12), metered and one-time prices zero.
- Invoice-recognised MRR (what a month carries), backward from billing: invoice amount spread over the months of its service period.

Ask which is meant; carrying both, name them apart (`list_mrr_usd`, `mrr_usd`).

## Inclusion defaults

- Amount column: total after discounts; profile its gap to cash collected and to the subtotal.
- Coupons included; tax and applied credit balance excluded; refunds: no default, finance policy.
- One-off and manual invoices, one-time charges and services: excluded.
- Floor basis at zero once confirmed to hide no reversal that should net.
- Invoice statuses: issued including uncollected; state the reason.

## Amortisation

`recognised_basis / cycle_months` in each of month 0 through `cycle_months - 1`, anchored on service period start, not invoice creation. Emit months with no invoice: one annual invoice is twelve rows. One row per subscription-month, tiebreaker declared.

## Cadence resolution

Per invoice, at worst per subscription, never per customer; the attribute ladder with these rungs:

1. Dominant cadence of the invoice's lines, from the immutable price or plan record each points at.
2. Service-period days bucketed into bands; widen a band when the histogram clusters in a gap.
3. Subscription header cadence (mutable; lags a plan change by a period).
4. Literal default; any traffic here is a finding.

A mid-cycle change invoice carries proration lines at the old cadence; use the subscription's main plan. Normalise before bucketing, unit and count from the price record: `months = <count> * (CASE <unit> WHEN 'day' THEN 1.0/30 WHEN 'week' THEN 7.0/30 WHEN 'month' THEN 1 WHEN 'year' THEN 12 END)`.

## True-ups

- A true-up is identified by the reason the document was raised, never a line proration flag.
- Short cycle: a mid-cycle amendment is removed from recognition by default.
- Multi-period cycle: spread over the remaining term, `remaining = greatest(cycle_months - elapsed_periods, 0)`, `adjustment / greatest(remaining, 1)` per period; negative adjustments not attached to a renewal included.
- A shorter-cycle invoice taking over a subscription stops the long-cycle spread from the month it covers, by a not-exists over later shorter-cycle invoices, never a dedup tiebreaker.

## Stop rule

`WHERE cancelled_at IS NULL OR revenue_month < date_trunc('month', cancelled_at)`. `[CHECKPOINT]`: which timestamp means service stopped (notice, scheduled end, actual end; profile how often they differ) and whether the ending month is recognised.

## Corrections

Corrections (reversals, replacements, manual) often carry ids absent from the catalog: profile them (sample description, line count, signed amount, trailing window); a non-trivial total is a `[CHECKPOINT]`. Classify each group by intent in `treatment` (`exclude`, `offset_invoice`, `assign_family:<f>`) and `basis_treatment` (`leave_in_total`, `subtract_from_basis`). Text matching proposes, never decides. Flooring at zero and netting a reversal differ; finance chooses.

## ARR and the customer rollup

Default `ARR = MRR * 12`, point in time at period end, never a trailing sum or projection (`ending_arr_usd`); assert `annualised = monthly * 12`. Roll up `sum(mrr)`, `sum(arr)` per customer-month over the spine ([../entities-and-time.md](../entities-and-time.md)), `coalesce(mrr, 0)` in gaps, carrying active subscription count, dominant plan and rank, `is_active`, the dominant product by value for a multi-product customer (a default). Never reconcile recurring revenue one to one against accounting revenue; a chart showing both says so.

## Retention states

State and motion tables: reconcile by construction ([../reconciliation.md](../reconciliation.md)); the states below are its change types; the rates over them (net and gross revenue retention, logo retention) follow [../entities-and-time.md](../entities-and-time.md). Window functions over the spine, not a self-join: `lag(mrr)` per customer by month, running `sum(is_active)` to tell first activation from a return. First match wins:

1. Measure zero, prior positive: `churned`.
2. Measure zero: `inactive`.
3. Prior zero, never active: `new`.
4. Prior zero, active before: `reactivation`.
5. Rank rose (both known): `upgrade`.
6. Rank fell (both known): `downgrade`.
7. Measure rose beyond epsilon: `expansion`.
8. Measure fell beyond epsilon: `contraction`.
9. Otherwise: `retained`.

- Epsilon on every comparison; carry the signed delta; emit the synthetic zero row after the last active month when it precedes the cap.
- Plan rank: an integer column on the plan dimension, no ties; propose it with each plan's revenue.
- Gap threshold (the lapse that becomes churn plus reactivation): default one month, a named constant; `lead(mrr) = 0` confirms a `churned` month; record whether a pending cancellation counts.
- Plan-shift pairs are moves, not churn (into a category outside scope: `churned`; out of it: `new`): declare and flag them, keep them out of churn counts; cancel-then-create upgrades and overlapping subscriptions in a migration are the same false pair, flagged, never silently corrected.

## Semantic checks

- Per invoice, recognised equals total minus declared exclusions, within a stated tolerance.
- `sum(recognised) / sum(invoice_total)` per resolved cadence matches that cadence's expected ratio.
- Every recurrence unit and count pair in the catalog maps to a named cycle, or the build fails.
- One state per customer-month.
- Flag a customer-month moving beyond a multiple of the prior month (default 3x), largest first.
- Count the never-active population (never-billed trials, zero-total creation invoices); never drop it.
