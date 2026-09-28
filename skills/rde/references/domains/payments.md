# Payments

Fires on payment-processor data (Stripe-like): charges, payment intents, refunds, disputes, fees, balance transactions, payouts. The balance transaction is the ledger: every movement of the account's balance has one, linked to its object through `source_id`, classified by `reporting_category` rather than `type` (Stripe).

## Metrics

- Gross volume: Σ captured amount of succeeded charges, in presentment or settlement currency.
- Net volume: gross − refunds − disputes; some subtract fees too, so always ask.
- Fees: Σ balance transaction `fee`: processing only, or with Stripe software fees (`stripe_fee`).
- Net settled: Σ balance transaction `net` (Stripe).
- Refund rate: refunded amount / gross; by count as a variant.
- Dispute rate: disputes / charges by count; by amount as a variant (confirm with the owner).
- Success rate: succeeded payment intents / attempted intents; per charge counts every retry.
- Payout: Σ `net` of the balance transactions an automatic payout carries (Stripe payout reconciliation).

## Objects and grain

- `payment_intent`, one row per purchase attempt flow: holds several charges when attempts fail.
- `charge`, one row per attempt: `amount`, `amount_refunded`, `captured`, `status`, `currency` as the customer paid.
- `refund`, `dispute`, one row each: positive amounts on their own objects.
- `balance_transaction`, one row per balance movement: `amount`, `fee`, `net`, `currency` (settlement), `exchange_rate`, `available_on`, `status`.
- `payout`, one row per transfer to the bank: `arrival_date`; an automatic payout lists its balance transactions.
- `transfer`, `application_fee`, one row per Connect movement: platform flows.

Fivetran's `dbt_stripe` builds `stripe__balance_transactions`, `stripe__activity_itemized_2`, `stripe__balance_change_from_activity_itemized_3`, `stripe__payout_itemized_3`, and `stripe__ending_balance_reconciliation_itemized_4`; reuse their grains where they exist.

## Signs, dates, and currencies

- `net = amount − fee`; `fee` is positive. Refunds, payouts, and dispute withdrawals are negative on the balance transaction and positive on their own objects.
- A partial capture is a charge balance transaction for the full authorisation plus a refund one for the uncaptured part (Stripe).
- A dispute posts as an `adjustment` whose source is the dispute; winning it posts a reversal. Dispute fees sit apart.
- A delayed method (ACH, direct debit) posts `payment` pending, then `payment_failure_refund` if it fails.
- Three dates: `created` (the sale), `available_on` (funds usable), payout `arrival_date` (the bank). The payout report groups by expected arrival, not the bank's posting date (Stripe).
- `charge.amount` is in the customer's currency; the balance transaction is in the settlement currency with `exchange_rate`.
- Amounts are integers in minor units; zero-decimal currencies (JPY) and three-decimal ones (KWD) divide differently (confirm with the owner).
- Instant payouts carry no transaction list; they reconcile against the balance, not per transaction (Stripe).

## Questions for the owner

- `volume-currency`: presentment or settlement currency? Default: settlement, from the balance transaction. Probe: gross both ways by currency. If wrong: FX mixed into volume.
- `net-of-fees`: does net volume subtract fees? Default: no; gross, refunds, disputes, and fees shown apart. Probe: fees against gross by month. If wrong: net volume off by the fee rate.
- `payments-date`: which date places a payment in a period? Default: `created` for sales, `available_on` for cash. Probe: month totals under each date. If wrong: month-end totals shift.
- `refund-dating`: refunds and disputes in their own month or the charge's? Default: their own month, as the ledger does. Probe: refunds by own month against by charge month. If wrong: past months restated.
- `connect-flows`: platform and connected-account flows in? Default: out. Probe: volume by `connected_account_id`. If wrong: volume double-counted across accounts.
- `success-unit`: success rate per intent or per charge? Default: per intent. Probe: both rates for the last 3 months. If wrong: retries depress the rate.
- `lost-dispute`: is a lost dispute a refund? Default: a separate line. Probe: lost dispute amount by month. If wrong: refund rate misstated.

## Traps

- Counting charges and payment intents together double-counts a purchase.
- `refunded` on a charge is true only when fully refunded; read `amount_refunded` (confirm with the owner).
- Test mode (`livemode` false) and soft deletes (`_fivetran_deleted`) in the same tables.
- Legacy Stripe fees and old Connect fee refunds appear as `adjustment`, not `stripe_fee`.
- The processor's volume is not revenue: tax, tips, and platform pass-through are inside it.

## Invariants

- `net = amount − fee` on every balance transaction.
- Σ `net` per `automatic_payout_id` equals minus the payout's own balance transaction amount.
- Start balance + activity − payouts = end balance, per currency.
- `charge.amount_refunded` = Σ succeeded refunds of the charge.
- Every succeeded, captured charge has exactly one charge balance transaction.

## Test cases

- A partial capture; `equals` on charge, gross, refunded, net.
- A dispute lost and one won; `equals` on dispute, the adjustment rows, the reversal.
- A charge in a foreign currency; `equals` on charge, presentment amount, settlement amount.
- A payout with a refund inside it; `equals` on payout, Σ net.

## For answering

- Say whether a volume is gross or net, and whether net subtracts fees.
- Name the date (sale, funds available, payout arrival) and the currency (settlement or customer).
- Refunds and disputes sit in the month they happen unless the owner chose otherwise.
- Processor volume is not revenue.

Sources: Stripe balance transaction types and payout reconciliation reports; Fivetran `dbt_stripe`.
