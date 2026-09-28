# Subscription revenue

Fires on recurring money of any kind: billing and subscriptions, memberships, dues, pledges, recurring gifts. Without invoice lines (memberships, dues, pledges, recurring gifts) keep inclusion, the stop rule as lapse or cancellation, refunds as corrections, and the movements on a donor-period spine; skip spreading and cadence unless a pledge is paid in instalments, then spread over its term.

## Metrics

- List MRR: price × quantity normalised to a month (annual / 12, weekly × 52 / 12, each / `interval_count`); `dbt_stripe` calls it "contracted MRR".
- Contracted MRR: list MRR less recurring discounts over `active` and `past_due` subscriptions; tax, trials, free, and metered out (Stripe); `dbt_stripe` calls it "billed MRR".
- Invoice-based MRR: (line amount − tax) spread over the line's own service period (ChartMogul; `dbt_zuora`).
- Roll-forward: start + new + expansion + reactivation − contraction − churn ± FX = end (Stripe).
- ARR: MRR × 12 at period end (Stripe), never a trailing sum of revenue; contract ARR from signed contracts is a variant to confirm.
- NRR, GRR, logo retention: `references/methods/retention-and-cohorts.md`. Stripe's churn rate is churned in 30 days / (start + new).
- Bookings, billings, revenue, cash: signed value, invoiced, recognised ratably (ASC 606), collected; billings ≈ revenue + Δ deferred (confirm with the owner).
- Deferred revenue: billed, not earned. RPO = deferred + contracted unbilled; cRPO the next 12 months (PwC; The SaaS CFO).

Carrying more than one basis, name them apart (`list_mrr_usd`, `mrr_usd`).

## Probes

| Probe | Shape | Decides |
| --- | --- | --- |
| Line-source coverage | `SELECT 'lines' AS src, count(DISTINCT l.invoice_id) FROM <invoice_lines> l UNION ALL SELECT 'charges', count(DISTINCT c.invoice_id) FROM <charges> c`, against the invoice count | which child table supplies line detail |
| Catalogue by materiality | `SELECT p.id, p.name, sum(l.amount) AS amount, sum(l.amount) / sum(sum(l.amount)) OVER () AS share FROM <prices> p LEFT JOIN <invoice_lines> l ON l.price_id = p.id AND l.created_at >= <trailing start> GROUP BY 1, 2 ORDER BY 3 DESC` | the plan map, exact where material |
| Cadence signals | `SELECT p.recurring_interval, p.interval_count, count(*) FROM <prices> p GROUP BY 1, 2` and the service-period length histogram of full-period lines | the cadence rungs and bands |
| Basis and currency | `SELECT i.currency, sum(i.subtotal), sum(i.total), sum(i.amount_paid), sum(i.total - i.amount_paid) AS uncollected FROM <invoices> i GROUP BY 1` | the measure column; whether to normalise currency |
| Date agreement | the date-agreement probe over request, scheduled end, and actual end | the churn date |

## Inclusion and spreading

- Out: tax (Stripe, ChartMogul), one-time and manual charges, services, applied credit balance (a way to pay, not a price).
- Recurring discounts come off, permanent ones always (Stripe); one-time and time-limited coupons are a setting, and subtracting them makes expansion when they expire.
- Refunds: no default (Stripe ignores one-off refunds; ChartMogul deducts them for Stripe data only).
- Open and `past_due` invoices count; `void` and `uncollectible` never; Stripe drops `unpaid`.
- Spread each line over the months of its own service period (24 for a two-year prepay, 3 for a quarter), anchored on the service start, never the invoice date; emit months with no invoice, one row per subscription-month.
- Floor the basis at zero only once it hides no reversal that must net.

## Cadence and true-ups

Per invoice, at worst per subscription, never per customer; `cadence_source` names the rung:

1. The line's price or plan record: interval × `interval_count` in months, normalised as `<count> * CASE <unit> WHEN 'day' THEN 1.0/30 WHEN 'week' THEN 7.0/30 WHEN 'month' THEN 1 WHEN 'year' THEN 12 END`.
2. Service-period days in bands, from full-period lines only; a proration line's length says nothing about the cycle.
3. The subscription header's cadence (mutable; lags a plan change by a period).
4. A literal default; any traffic here is a finding.

- A true-up is known by why the document was raised, never a proration flag. Short cycle: a mid-cycle amendment is removed; multi-period: spread over the remaining term, `adjustment / greatest(cycle_months - elapsed, 1)` per period.
- A shorter-cycle invoice taking over stops the long spread from its month, by a not-exists over later shorter-cycle invoices, never a dedup tiebreaker.
- Reversals, replacements, and manual documents often carry ids absent from the catalogue: profile them (description sample, line count, signed amount, trailing window), then classify each group in `treatment` (exclude, offset, assign to a family) and `basis_treatment`; text matching proposes, never decides.

## Stop rule and movements

Three timestamps: request (`canceled_at`), scheduled end (`cancel_at`, `current_period_end`), actual end (`ended_at`); the date-agreement probe shows how often they differ. Default: MRR stops at the end of paid service (ChartMogul); Stripe stops it when `cancel_at_period_end` is set. Shape: `WHERE s.ended_at IS NULL OR m.revenue_month < date_trunc('month', s.ended_at)` under whichever timestamp the owner chose, and whether the ending month is recognised is part of the same question.

Movements per customer on the change in MRR, window functions over the spine, first match wins:

1. Zero, prior positive, lapse past the grace window: churned.
2. Zero: inactive.
3. Positive, never active: new.
4. Positive, prior zero, active before: reactivation.
5. Rose beyond epsilon: expansion (an added subscription included).
6. Fell beyond epsilon, still positive: contraction (a non-last subscription cancelled included).
7. Otherwise retained; a plan change with no MRR change is neutral.

- Grace window: default 30 days, a named constant; a lapse inside it keeps the prior MRR flagged `in_grace`; a paid past-due invoice removes the churn (ChartMogul).
- FX: movements at a fixed rate; the currency delta is its own row.
- Upgrade and downgrade by plan rank are a company extension, only when asked: an integer rank without ties, proposed with each plan's revenue; rank and MRR moving opposite ways is flagged.
- Plan-shift pairs and cancel-then-create migrations are moves, flagged, never churn plus new. Carry the signed delta on every movement row, and the synthetic zero row after the last active month when it falls before the cap.

## Retention and the bridge

- Per customer (billing customer or parent account), never per subscription: cross-sell is otherwise churn plus new (SaaS Capital).
- Never tie MRR row by row to accounting revenue; keep an aggregate bridge: one-offs, services, usage, daily against monthly spreading, FX, credits, churn timing. A chart showing both says so.

## Questions for the owner

- `mrr-basis`: list, contracted, or invoice-based? Default: contracted. Probe: the three bases for the last 3 months. If wrong: off by the discount share or the billing lag.
- `mrr-discounts`: one-time and limited coupons off? Default: recurring off, one-time kept. Probe: coupon value by duration type. If wrong: phantom expansion at coupon expiry.
- `churn-date`: which timestamp stops MRR? Default: end of paid service. Probe: date agreement over the three timestamps. If wrong: churn moves up to a cycle.
- `delinquency`: do past-due and unpaid count? Default: `past_due` in; `unpaid`, `void`, `uncollectible` out. Probe: MRR by status. If wrong: the active base is misstated.
- `grace-window`: how long a lapse before churn? Default: 30 days. Probe: the lapse-length histogram between paid periods. If wrong: churn and reactivation inflated or hidden.
- `retention-entity`: customer or parent account? Default: billing customer. Probe: customers per parent; subscriptions per customer. If wrong: NRR and logos shift on cross-sell.
- `usage-in-mrr`: usage and overage in MRR? Default: out, reported apart. Probe: usage share of recurring billing. If wrong: NRR volatile, GRR 1–8 points lower.
- `fx-rate`: rate for movements? Default: fixed rate, FX its own line. Probe: MRR at spot against fixed. If wrong: currency reads as expansion.
- `trials-free`: trials and free plans counted? Default: out. Probe: subscriptions at zero or in trial. If wrong: new MRR and counts inflated.
- `refunds-in-mrr`: refunds deducted? Default: none; ask. Probe: refunds by month against MRR. If wrong: MRR drifts from revenue.

## Traps

- Current subscription state overwrites history: past months come from invoice lines or snapshots.
- Proration lines, `interval_count`, several subscriptions per customer, mid-month starts, backdated subscriptions, credit notes restating invoices.
- Minor units; soft deletes (`_fivetran_deleted`); test mode (`livemode` false).
- `dbt_recurly` buckets a charge by its creation month without spreading: wrong for annual plans.

## Invariants

- The roll-forward closes each month; one state per customer-month.
- New only on a customer's first positive month; reactivation only after a churn.
- Per invoice, the spread sums to total minus declared exclusions within tolerance; `sum(recognised) / sum(invoice_total)` per resolved cadence matches that cadence's expected ratio.
- Every recurrence unit and count maps to a named cycle, or the build fails.
- MRR ≥ 0; ARR = 12 × period-end MRR; GRR ≤ 100% and ≤ NRR.
- The MRR-to-revenue bridge closes within tolerance per month.
- Flag a customer-month beyond 3× its prior month, largest first; count the never-active population (never-billed trials, zero-total creation invoices), never drop it.

## Test cases

Per model; thresholds (the grace window, the cadence bands) are inputs of the fixture.

- Spreading: an annual invoice from mid-month, a two-year prepay, a monthly one; `equals` on subscription, month, amount.
- Cadence: one invoice per rung, a proration line whose days fit another band; `equals` on invoice, cadence, `cadence_source`.
- True-ups: a short-cycle amendment, a multi-period one, a shorter cycle taking over; `equals` on subscription, month, amount.
- Stop rule: cancelled mid-period, ending at period end; `empty` after the chosen timestamp.
- Corrections: one document per `treatment`; `equals` on document, `treatment`, `basis_treatment`, recognised amount.
- Movements: one customer per state, a lapse inside and past the grace window, an FX-only change, a zero-delta plan change; `equals` on customer, month, state, signed delta; a second test under the alternative window.

## For answering

- Name the MRR basis (list, contracted, invoice-based) and whether discounts come off.
- MRR stops at the churn date the owner chose; say which.
- ARR is period-end MRR × 12, never a trailing sum of revenue.
- NRR and GRR are per-customer cohorts; name the window.
- MRR is not accounting revenue; a chart showing both says so.

Sources: Stripe billing analytics and MRR docs; ChartMogul MRR, movements, churn recognition, past-due handling; SaaS Capital on retention pitfalls; saasmetricsboard.com on NRR; Fivetran `dbt_stripe`, `dbt_zuora`, `dbt_recurly`; PwC ASC 606 disclosures; The SaaS CFO on RPO.
