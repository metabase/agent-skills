# Sales pipeline

Fires on CRM pipeline data (Salesforce, HubSpot): opportunities or deals, stages, stage and field history, owners. The opportunity row holds only its current state; every "as of" question reads history or snapshots.

## Metrics

- Bookings: Σ amount of opportunities closed won, by close date; new and expansion only, renewals apart.
- Win rate: won / (won + lost) closed in the period, by count; variants by amount and by created-in-period cohort; `dbt_salesforce` reports it by owner and manager.
- Pipeline: Σ amount of open opportunities with a close date in the period; the stages counted are a mapping.
- Coverage: pipeline / remaining quota for the period; 3× is a rule of thumb (confirm with the owner).
- Sales cycle: days from created to closed won; median as a variant.
- Stage conversion: opportunities reaching stage k+1 / reaching stage k, from stage history.
- Velocity: opportunities × win rate × average deal / cycle length (confirm with the owner).

## Sources and grain

- `opportunity`, one row per opportunity, current state: amount, stage, close date, type, owner, `is_won`, `is_closed`, `is_deleted`.
- `opportunity_history`, one row per change to stage, amount, probability, close date, or forecast category: Salesforce's stage history.
- `opportunity_field_history`, one row per change to any tracked field: field, old value, new value (Salesforce).
- `opportunity_line_item`, one row per product on an opportunity.
- `user`, `user_role`, one row per rep and per role: the manager hierarchy.
- HubSpot `deal`, `deal_pipeline_stage`, one row per deal and per stage: stage probability and closed flag on the stage (confirm with the owner).

`dbt_salesforce` builds `salesforce__opportunity_enhanced`, `__owner_performance`, `__manager_performance`, and with history mode `__opportunity_daily_history`, one row per opportunity per day; that daily history is the snapshot a past pipeline reads. Without it, capture starts in the first build session (`references/time-and-entities.md`).

## History

- Pipeline on a past date is the daily history or the stage history replayed to that date, never today's row filtered.
- Close dates slip, amounts change, stages move backwards, closed deals reopen: each is a row in history, not an edit to count once.
- Deleted opportunities carry `is_deleted`; keep them out of every count.

## Questions for the owner

- `win-rate-basis`: by count or amount; closed in period or created cohort? Default: count, closed in period. Probe: the four readings for the last 4 quarters. If wrong: rate off, trend reversed by large deals.
- `amount-field`: which amount: amount, ACV, ARR, TCV? Default: amount. Probe: the candidate fields side by side. If wrong: bookings off by contract length.
- `bookings-types`: which opportunity types are bookings? Default: new and expansion; renewals apart. Probe: bookings by type. If wrong: bookings inflated by renewals.
- `pipeline-stages`: which stages count as pipeline? Default: open stages past qualification. Probe: pipeline by stage. If wrong: coverage overstated.
- `snapshot-cadence`: how often is pipeline snapshotted? Default: daily from history. Probe: history rows per opportunity per week. If wrong: past pipeline unreproducible.
- `crm-currency`: which currency and rate? Default: the corporate currency at dated rates. Probe: amounts by currency. If wrong: FX reads as pipeline change.
- `owner-credit`: who gets credit after an owner change? Default: the owner at close. Probe: opportunities whose owner changed before close. If wrong: rep performance misattributed.

## Traps

- Today's close date and amount on an open opportunity rewrite every past view built from the opportunity table.
- Duplicate opportunities for one deal.
- Bookings in the CRM are not billings or revenue.
- `opportunity_history` covers only its fixed fields; other fields need field-history tracking switched on (Salesforce).

## Invariants

- A closed opportunity is won or lost and has a close date.
- The last stage-history row of each opportunity matches its current stage.
- Won amounts by quarter reconcile to signed contracts or billing within tolerance.
- One row per opportunity per day in the daily history.

## Test cases

- An opportunity whose close date slipped a quarter; `equals` on date, pipeline as of each quarter end.
- A stage moving backwards and a reopened deal; `equals` on opportunity, stage conversion rows.
- An owner change before close; `equals` on opportunity, credited owner.

## For answering

- Win rate is by count over deals closed in the period unless stated; say which.
- Name the amount field behind bookings and pipeline.
- Pipeline on a past date comes from history, not today's opportunity rows.
- Bookings are not revenue.

Sources: Salesforce OpportunityHistory and OpportunityFieldHistory object reference; Fivetran `dbt_salesforce`.
