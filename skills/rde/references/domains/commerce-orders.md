# Commerce orders

Fires on commerce order data (Shopify-like): orders, line items, refunds, returns, discounts, shipping, tax, fulfilments. The order line is the atomic sale; refunds, returns, and adjustments are their own dated events against it, never edits to it.

## Metrics

- Gross sales: selling price × ordered quantity, before discounts, returns, tax, shipping, fees (Shopify).
- Discounts: line discount + the line's share of cart-level discounts, negative (Shopify).
- Returns (sales reversals): value of returned goods, negative, dated when the refund is processed (Shopify).
- Net sales: gross − discounts − returns; shipping and tax out (Shopify).
- Total sales: net + tax + shipping + duties + fees (Shopify).
- GMV: no standard; often total sales before returns; always ask.
- Gross profit: net sales − COGS at sale-time cost.
- AOV: net sales / orders; total sales / orders as a variant.
- Return rate: returns / gross sales; by units as a variant.

## Objects and grain

- `order`, one row per order: `created_at`, `cancelled_at`, `financial_status`, `taxes_included`, `test`, shop and presentment currency.
- `order_line`, one row per line: price, quantity, variant, line discount allocations.
- `refund`, `order_line_refund`, one row per refund and per refunded line: `restock_type`; several refunds per order.
- `order_adjustment`, one row per refund adjustment: refunded shipping and refund discrepancies.
- `discount_allocation`, `shipping_line`, `tax_line`, one row each: cart discounts spread over lines.
- `transaction`, one row per payment movement: the payments view of refunds.
- `fulfillment`, one row per shipment: the shipped date, distinct from the order date.

`dbt_shopify` builds `shopify__orders`, `shopify__order_lines`, `shopify__refunds`, `shopify__refund_lines`, `shopify__daily_shop`, `shopify__customer_cohorts`; reuse their grains where they exist.

## Dates and money

- Every amount is dated by its event: sales when ordered; returns, tax, and shipping reversals when the refund is processed (Shopify). Restating an old order's month for a later refund is a choice the owner makes.
- Refunding and restocking on separate dates shows the same amount twice in some reports (Shopify).
- Sales reports carry returns; payment reports carry refunds; the two differ (Shopify).
- Gift cards are not sales when sold; the redemption is the sale (Shopify).
- Test orders are out of sales reports and in exports (Shopify).
- `taxes_included` prices carry VAT inside the price; strip it before gross sales.

## Questions for the owner

- `sales-date`: refunds in their own month or the order's? Default: their own month. Probe: returns by own month against by order month. If wrong: past months restated.
- `excluded-orders`: cancelled, test, draft, POS orders? Default: test and draft out; cancellations reversed on their date; POS in. Probe: orders and sales by source and status. If wrong: sales over- or under-stated.
- `tax-inclusive`: are prices tax-inclusive? Default: read `taxes_included` per order. Probe: orders by `taxes_included`. If wrong: net sales carry VAT.
- `shop-currency`: shop or presentment currency? Default: shop currency. Probe: sales both ways by currency. If wrong: FX mixed into sales.
- `gmv-definition`: what does GMV include? Default: total sales before returns. Probe: GMV under each reading. If wrong: the headline differs by tax, shipping, returns.
- `net-sales-scope`: shipping and duties in net sales? Default: out. Probe: shipping share of total sales. If wrong: net sales inflated.
- `cogs-cost`: which cost for COGS? Default: cost at sale time, from cost snapshots. Probe: current against snapshot cost for past months. If wrong: gross profit rewritten when costs change.
- `refund-no-return`: refunds without a return, and exchanges? Default: a refund without a return reduces net sales; an exchange is a return and a sale. Probe: refunds with no returned units. If wrong: returns and units misstated.

## Traps

- The variant cost on the product is today's cost, not the cost when sold: past gross profit needs snapshots.
- Cart discounts double-count when added at the order and again at the lines.
- Order edits change an order after the fact; exports show them, sales reports may not (Shopify).
- The shop's timezone defines the day.
- Refunded shipping lives in `order_adjustment`, not the refund lines.

## Invariants

- Order total = subtotal + shipping + tax − discounts, within a rounding tolerance.
- Refunded quantity ≤ ordered quantity per line.
- Σ line amounts = the order subtotal.
- Daily net sales tie to the source's finance report.
- One row per order line; no negative line net.

## Test cases

- An order with a cart discount over two lines; `equals` on line, allocated discount.
- An order refunded next month with shipping refunded; `equals` on month, returns, shipping reversal.
- A tax-inclusive order; `equals` on line, gross sales, tax.
- A gift card sold then redeemed; `equals` on date, net sales.

## For answering

- Name the sales figure: gross, net (gross − discounts − returns), or total (with tax and shipping).
- Returns sit in the month they are processed unless the owner chose the order month.
- GMV has no standard definition; state the one used.
- Amounts are in the shop currency unless stated.

Sources: Shopify finance report and sales discrepancies documentation; Fivetran `dbt_shopify`.
