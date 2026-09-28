# Retention and cohorts

Retention, NRR, GRR, cohort tables, activation: one shape with four parameters, per customer, over complete periods, with a fixed cohort denominator.

## One shape, four parameters

Of the entities that started in a cohort, how much is still present k periods later, over the cohort's size at the start. Fix four parameters first, each a decision (headline ones get glossary entries): the entity (customer or account); the cohort (first paid period, signup date; monthly by default); the activity that counts as present (MRR above zero, a qualifying event, a gift); the measure (entities for logo retention, money for NRR and GRR). Numbers differing in any parameter are different metrics, named apart. Fix the basis (month over month, or year over year, needing two complete years), expose the other, and say which in the description.

## The entity is the customer

Per customer or account, never per subscription: cross-sell, plan changes, and re-subscriptions otherwise read as churn plus new. Roll subscriptions up to the customer per period through the conformed key; a customer with two subscriptions is present while either is. Where billing and product accounts differ, the crosswalk decides whose retention it is, and the unmatched are reported. A shift of plan, tier, product, or fund, or a cancel-then-create pair in a migration, is a move, flagged, never churn plus new.

## Logo retention

The cohort's customers present in period k over its size in period 0. A returning customer is present again when it returns; whether a short lapse is churn at all is the grace window (owner's call, default 30 days). Logo churn for a period: customers present at its start and absent at its end, over those present at its start; new customers never enter the denominator.

```sql
SELECT b.month AS base_month, count(DISTINCT b.customer_id) AS base_n, count(DISTINCT f.customer_id) AS retained_n
FROM <out_schema>.customer_months b
LEFT JOIN <out_schema>.customer_months f ON f.customer_id = b.customer_id AND f.month = <b.month + k periods> AND f.is_active
WHERE b.is_active AND b.is_complete_period AND <the follow period is complete>
GROUP BY 1
```

## NRR and GRR

- NRR: end-of-window MRR from customers with MRR at its start, over their starting MRR; includes expansion, contraction, churn; excludes new customers; reactivated ones count only if in the starting base.
- GRR: the same base, each customer capped at its starting MRR (`least(end_mrr, start_mrr)`); at most 100% and at most NRR.
- Board: trailing twelve months (customers with MRR twelve months ago, their MRR today). Operations: monthly, the base at each month's start. Never compound monthly rates into an annual one unless the owner chooses it; say which.
- Owner questions: monthly, trailing twelve, or compounded; usage revenue in or out; FX at constant rates or not.

## States per entity-period

On the dense spine (`references/time-and-entities.md`), window functions only (`lag(is_active)`, running `sum(is_active)`), first match wins, one state per entity-period asserted: active now and never before, `new`; active now, not last period, active earlier, `reactivation`; inactive now, active last period, past the grace window, `churned`; inactive now, `inactive`; otherwise `retained`. Money movements on top (expansion, contraction) are in `references/domains/subscription-revenue.md`.

## The cohort table

Rows are cohorts (first present period), columns the offset k, each cell the retained measure over the cohort's base at k = 0, the denominator fixed at start and never recomputed. Built on the entity-month spine from each entity's first activity. Show each cohort's size beside its row (small cohorts swing). Averages across cohorts are size-weighted and use, per offset, only cohorts old enough to have it complete.

## Activation

The share of a signup cohort reaching the activation event within N days of signup: cohort by signup period, denominator fixed at signup, cohorts younger than N days left out (never shown as low). Event and N are the owner's; changing either is a new metric. Deriving them: `references/domains/product-usage-events.md`.

## N-day and unbounded

N-day: present on day N (or its bucket). Unbounded: present on day N or later; never below N-day, never rising with N. Name which: N-day fits engagement, unbounded fits "still around"; monthly revenue retention is neither (presence per calendar period).

## Complete periods only

A cell exists once its period is complete (the watermark-derived boundary); the triangle's incomplete edge is blank, never zero; a partial period is never compared with a full one.

## Checks

Logo retention at k = 0 is 100% for every cohort; each cohort's size equals the entities whose first present period it is; GRR ≤ 100% and ≤ NRR; unbounded retention never rises with k; customer-level MRR summed per period equals the MRR metric; cohort sizes for complete periods do not change between runs.
