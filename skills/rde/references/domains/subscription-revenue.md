# Subscription revenue

Any billing system; the router sends you here for run rate, churn, or retention. Every rule is a default the revenue owner confirms at a checkpoint ([../collaboration-contract.md](../collaboration-contract.md)), never settled inside a `WHERE`; tiebreakers, header versus line, the attribute ladder, and the period cap: [../modeling-decisions.md](../modeling-decisions.md).

## Probes for this domain

| Probe | Returns | Decides |
| --- | --- | --- |
| Line-source coverage | parents covered per candidate child table | Which child table supplies line detail |
| Catalogue inventory | id, name, unit amount, active, children, trailing volume, share | The taxonomy map, exact where material |
| Cadence signal candidates | distribution per recurrence column; service-period day histogram | The cadence classifier's signal and bands |
| Basis and currency comparison | sum per amount column, discount and uncollected shares, totals per currency | Which column is the measure; whether to normalise |

## Recognition basis

- List-price MRR (contracted), forward from the subscription: `unit_price * quantity` per month (annual / 12, weekly * 52 / 12, daily * 365 / 12), metered and one-time prices zero.
- Invoice-recognised MRR (what a month carries), backward from billing: invoice amount spread over the months of its service period.

Ask which the business means; if both are carried, name them distinctly (`list_mrr_usd`, `mrr_usd`) in the model description.

## Inclusion defaults

- Amount column: total after discounts; profile its gap to cash collected and to the pre-discount subtotal.
- Coupons: included. Tax: excluded. Applied credit balance: excluded. Refunds: no default; finance policy.
- Non-subscription, one-off, and manual invoices, one-time charges and services: excluded; the forward part of a long-cycle true-up added back separately.
- Floor basis at zero: yes, once the floor is confirmed to hide no reversal that should net.
- Invoice statuses: issued including uncollected; state the reason.

## Amortisation

`recognised_basis / cycle_months` in each of month 0 through `cycle_months - 1`, anchored on service period start, not invoice creation, unless told otherwise. Emit rows for months with no invoice: one annual invoice is twelve rows. One row per subscription-month, tiebreaker declared.

## Cadence resolution

Per invoice, at worst per subscription, never per customer; the attribute ladder in `modeling-decisions.md` with these rungs:

1. Dominant cadence of the invoice's lines, from the immutable price or plan record each points at.
2. Service-period days bucketed into bands; widen a band when the histogram clusters in a gap.
3. Subscription header cadence (mutable; lags a plan change by a period).
4. Literal default; any traffic here is a finding.

An invoice raised for a mid-cycle change carries proration lines at the old cadence; use the subscription's main plan. Normalise before bucketing, unit and count read off the price record: `months = <count> * (CASE <unit> WHEN 'day' THEN 1.0/30 WHEN 'week' THEN 7.0/30 WHEN 'month' THEN 1 WHEN 'year' THEN 12 END)`. Symptom of a wrong cadence or missing gap-month spread: a twelve-fold spike then zeros, plus false churn.

## True-ups and prorations

- A true-up is identified by the reason the document was raised, never a line proration flag (per-seat charges can be proration lines).
- Short cycle: a mid-cycle amendment is removed from recognition by default.
- Multi-period cycle: spread over the remaining term, `remaining = greatest(cycle_months - elapsed_periods, 0)`, `adjustment / greatest(remaining, 1)` per period, negative adjustments not attached to a renewal included.
- A shorter-cycle invoice taking over a subscription stops the long-cycle spread from the month it covers, via a not-exists over later shorter-cycle invoices, never a dedup tiebreaker.

## Stop rule

`WHERE cancelled_at IS NULL OR revenue_month < date_trunc('month', cancelled_at)`. Checkpoints: which timestamp means service stopped (notice, scheduled end, actual end; profile how often they differ by month) and whether the ending month is recognised (inclusive or exclusive).

## Corrections

Corrections (reversals, replacements, manual) often carry ids absent from the catalog: profile them (sample description, line count, signed amount over a trailing window); a non-trivial total is a checkpoint. Classify each group by intent in two fields: `treatment` (`exclude`, `offset_invoice`, `assign_family:<f>`) and `basis_treatment` (`leave_in_total`, `subtract_from_basis`); with an invoice-level basis a correction stays in the total until `subtract_from_basis`. Text matching proposes a group, never decides it. Flooring at zero and netting a reversal are different policies; finance chooses.

## ARR and the customer rollup

Default `ARR = MRR * 12`, point in time at period end, never a trailing sum or projection, in a column named for it (`ending_arr_usd`); assert `annualised = monthly * 12`. Roll up `sum(mrr)`, `sum(arr)` per customer-month; a multi-product customer carries its dominant product by value, recorded as an assumption. Never reconcile recurring revenue one to one against accounting revenue; a chart showing both says so.

## Dense customer-period spine

Bounds and the cap: `modeling-decisions.md`; here the cap's first term is the latest month with a single-period recognition. Left-join with `coalesce(mrr, 0)`. Carry: monthly and annualised measures (zero in gaps), active subscription count, dominant plan and rank, `is_active`.

## Retention states

State and motion tables: Reconcile by construction in [../reconciliation.md](../reconciliation.md); the states below are its change types. Window functions over the spine, not a self-join: `lag(mrr)` per customer by month, running `sum(is_active)` to tell first activation from a return. First match wins; reordering is a checkpoint:

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
- Plan rank is an integer column on the plan dimension, no ties, compared only when both known; propose the ranking with each product's revenue.
- Gap threshold, the lapse that becomes churn plus reactivation: default one month, a named constant. `churned` is the single-month event; `lead(mrr) = 0` records confirmation; record whether pending cancellation counts.
- Plan-shift pairs are moves, not churn (into a category outside recognition scope: `churned`; out of it: `new`): declare the pairs, flag them, keep them out of churn counts; cancel-then-create upgrades and overlapping subscriptions during a migration are the same false pair, flagged, never silently corrected.

## Retention rates

- Net revenue retention: current revenue of the base-period customer set / that set's base-period revenue.
- Gross revenue retention: same denominator; numerator `least(current, base)` per customer before summing.
- Logo retention: share of the base-period customer set still active.

Customer grain. Fix the basis (year over year or month over month), expose the other, record which the headline uses; product-level retention uses the product held at period start; year over year needs two full years of history.

## Semantic checks

- Per invoice, recognised equals total minus declared exclusions, within a stated tolerance.
- `sum(recognised) / sum(invoice_total)` per resolved cadence matches that cadence's expected ratio.
- Every recurrence unit and count pair in the catalog maps to a named cycle, or the build fails.
- One state per customer-month.
- Flag a customer-month moving beyond a multiple of the prior month (default 3x); inspect the largest first.
- Count and report the never-active population (never-billed trials, zero-total creation invoices); never drop it.
