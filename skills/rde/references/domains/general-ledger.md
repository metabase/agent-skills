# General ledger

Fires on accounting-system data (NetSuite, QuickBooks, Xero): journal lines, chart of accounts, periods, subsidiaries, currencies. The GL line is the atomic fact: one account, one period, one amount, debit or credit. Every report is a sum of lines; nothing is recomputed from source documents once the GL exists.

## Metrics

- Trial balance: Σ debits − Σ credits per account to a period end, per subsidiary and book.
- Income statement: activity of revenue and expense accounts within the period, by department, class, location (`dbt_netsuite`).
- Balance sheet: cumulative balance of asset, liability, and equity accounts to the period end; retained earnings and net income computed, not posted (`dbt_netsuite`).
- Net income: revenue − expenses for the period; closes into retained earnings at year end.
- Gross margin: (revenue − COGS) / revenue; the COGS accounts are a mapping.
- Cash flow: indirect method from net income and balance changes (`dbt_quickbooks` default); direct method from cash accounts.

## Sources and grain

- NetSuite: `transactionaccountingline` (posting line per book), `transactionline`, `transaction`; around them `account`, `accountingperiod`, `subsidiary`, `consolidatedexchangerate`, `fiscalcalendar`; `dbt_netsuite` builds `netsuite2__transaction_details`, `__income_statement`, `__balance_sheet`.
- QuickBooks: no GL table; `quickbooks__general_ledger` rebuilds double entry from invoices, bills, payments, deposits, purchases, and journal entries; around them `account` classification; `__general_ledger_by_period`, `__profit_and_loss`, `__balance_sheet`, `__cash_flow_statement`, `__ap_ar_enhanced`.
- Xero: `journal`, `journal_line` are the posted GL; around them `account`, `invoice`, `bank_transaction`, `manual_journal` (confirm with the owner).

## Signs, periods, and currencies

- Store `debit − credit` per line. Assets and expenses carry debit balances; liabilities, equity, and revenue credit balances. Flip revenue, liability, and equity only for display (confirm with the owner).
- A period is the posting period, not the transaction date: backdated entries and adjustment periods land where the ledger put them.
- Fiscal years need not start in January; read `fiscalcalendar` or the company's fiscal start (`dbt_netsuite`), and use it as the calendar (`references/time-and-entities.md`, Calendars).
- Retained earnings and current-year net income are virtual in the source; the balance sheet computes them (`dbt_netsuite`).
- Consolidation converts each subsidiary to the parent currency with the consolidated rates and computes the cumulative translation adjustment (`dbt_netsuite`): income at the period-average rate, balance sheet at the period-end rate, equity at historical rates.
- Non-primary accounting books add rows per book (`dbt_netsuite` multi-book); never sum across books.
- Home-currency transactions need no conversion; `dbt_quickbooks` skips them by a variable.

## Questions for the owner

- `gl-period`: posting period or transaction date? Default: posting period. Probe: lines whose transaction date falls in another period. If wrong: backdated entries in the wrong month.
- `fiscal-calendar`: fiscal year start, and 4-4-5 or calendar months? Default: the system's fiscal calendar. Probe: period start and end dates per year. If wrong: quarters and years misaligned.
- `reporting-currency`: reporting currency and rate type? Default: parent currency, consolidated rates. Probe: totals under each rate type. If wrong: FX differences read as performance.
- `consolidation`: consolidated or per subsidiary; eliminations included? Default: per subsidiary plus an eliminated consolidation. Probe: intercompany account balances. If wrong: intercompany revenue double-counted.
- `accounting-book`: which book? Default: primary. Probe: row counts per book. If wrong: two books summed.
- `gl-basis`: accrual or cash? Default: accrual. Probe: the cash-basis report from the source. If wrong: revenue and expense timing moves.
- `line-mapping`: which accounts make each P&L line? Default: account type plus the company's mapping. Probe: balances of unmapped accounts. If wrong: lines misclassified.
- `posting-only`: non-posting and unapproved transactions in? Default: out (posting lines only). Probe: amounts on non-posting lines. If wrong: orders and estimates counted as activity.

## Traps

- Sales orders, purchase orders, and estimates sit in NetSuite's transaction table and never post.
- Entries posted into closed or reopened periods restate history: snapshot each closed period's totals.
- Voided and deleted entries; account reclassifications re-map history.
- A balance sheet from period activity alone misses opening balances and retained earnings.
- Transaction-currency and base-currency amounts side by side on one line.

## Invariants

- Every journal balances: Σ debits = Σ credits.
- The trial balance nets to zero per period, subsidiary, and book.
- Assets = liabilities + equity, including current-year net income.
- Net income equals the change in retained earnings across the year-end close.
- Closed-period totals match their snapshot.
- The rebuilt GL ties to the source system's trial balance report.

## Test cases

- A two-line journal and a three-line one; `empty` where Σ `debit − credit` per journal differs from zero.
- A backdated entry; `equals` on line, posting period.
- A foreign subsidiary's month; `equals` on account, period, converted amount, the translation adjustment.
- The last period of a fiscal year and the first of the next; `equals` on retained earnings.

## For answering

- Amounts are in the reporting currency at the rate type the owner chose; say which.
- Periods are posting periods on the fiscal calendar, not transaction dates.
- Revenue and liabilities show positive by display convention; the ledger stores debit minus credit.
- Say whether a figure is consolidated, with eliminations, or per subsidiary.

Sources: Fivetran `dbt_netsuite`, `dbt_quickbooks`.
