# Session 4: SQL Questions — Reference File

## Key Concepts to Teach

### 1. When to Use SQL vs Query Builder

| Use Query Builder | Use SQL Editor |
|---------------------|----------------|
| Simple filters, aggregations, group-bys | Multi-table JOINs (e.g. Orders + People + Products) |
| Most everyday questions | Window functions (running totals, rank, lag) |
| Non-technical users | Subqueries and CTEs |
| Rapid exploration | Exact control over column names and logic |

Rule of thumb: if you're fighting the Query Builder, switch to SQL.

### 2. Opening the SQL Editor
- **+ New → SQL query** — opens the native editor directly
- Or: **New → Question → (switch to) SQL query** — toggle in the top-right of the question picker
- Or: open a query builder question → click "View the SQL" → switch to native mode

### 3. Writing Queries Against the Sample Database

Basic examples:

```sql
-- All orders over $100 with the customer's name
SELECT o.id, p.name, o.total, o.created_at
FROM orders o
JOIN people p ON o.user_id = p.id
WHERE o.total > 100
ORDER BY o.created_at DESC;

-- Average product rating by category
SELECT pr.category, AVG(r.rating) AS avg_rating, COUNT(r.id) AS review_count
FROM reviews r
JOIN products pr ON r.product_id = pr.id
GROUP BY pr.category
ORDER BY avg_rating DESC;

-- Monthly revenue for 2024
SELECT DATE_TRUNC('month', created_at) AS month, SUM(total) AS revenue
FROM orders
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
GROUP BY 1
ORDER BY 1;

-- Accounts that converted from trial (not possible in Notebook without a Model)
SELECT id, first_name, last_name, plan, trial_ends_at, created_at
FROM accounts
WHERE trial_converted = true
  AND active_subscription = true;
```

### 4. Template Variables — The Most Powerful SQL Feature
Template variables turn hard-coded SQL into an interactive, filterable question.

**Syntax**: `{{variable_name}}` — wrap in double curly braces.

```sql
-- Filter orders by status dynamically
SELECT id, user_id, total, created_at
FROM orders
WHERE created_at >= {{start_date}}
  AND total > {{min_total}};
```

Metabase generates filter widgets automatically — users pick a date and enter a number
without touching the SQL.

**Variable types:**
- `Text` — free text input: `WHERE products.category = {{category}}`
- `Number` — numeric input: `WHERE orders.total > {{min_total}}`
- `Date` — date picker: `WHERE orders.created_at >= {{start_date}}`
- `Field filter` — smart widget: Metabase detects the column type and renders the
  right UI automatically. Best option when you know which column you're filtering.

### 5. Optional Clauses with Double Brackets
```sql
SELECT id, user_id, total, discount, created_at
FROM orders
WHERE 1=1
  [[AND created_at >= {{start_date}}]]
  [[AND discount > {{min_discount}}]]
  [[AND total > {{min_total}}]];
```
If a user leaves a filter blank, that clause is skipped entirely.
This lets one SQL question serve as a flexible, multi-filter explorer.

### 6. Referencing Saved Questions
```sql
-- Reference a saved "High Value Orders" question as a subquery
SELECT u.state, COUNT(*) AS high_value_count
FROM {{#42}} AS hvo  -- 42 is the saved question's ID
JOIN people u ON hvo.user_id = u.id
GROUP BY u.state;
```

### 7. Saving and Using SQL Questions
- Saved exactly like Notebook questions — appear in search, add to dashboards
- SQL questions support template variables as dashboard filter inputs

---

## Active Recall Questions

**Q1.** Write a SQL query to find the top 5 products by total revenue, using the Orders and Products tables.
> **A:**
> ```sql
> SELECT p.title, SUM(o.total) AS revenue
> FROM orders o
> JOIN products p ON o.product_id = p.id
> GROUP BY p.title
> ORDER BY revenue DESC
> LIMIT 5;
> ```

**Q2.** You want users to filter the Orders table by state (via the People table) without editing SQL. What do you add?
> **A:** A template variable, e.g. `WHERE p.state = {{customer_state}}` after joining People. This creates a text input widget automatically.

**Q3.** What's the difference between `{{var}}` and `[[AND col = {{var}}]]`?
> **A:** A regular variable is always included in the query — leaving it blank may error. An optional variable in double brackets means that entire clause is skipped if the user leaves the field empty.

**Q4.** You want to compare monthly revenue to the previous month (month-over-month). Can the Query Builder do this? What SQL feature handles it?
> **A:** Yes — the Query Builder can do this with the `Offset()` function in the Summarize step, e.g. `Offset(Sum([Total]), -1)` to grab the previous period's value (Metabase translates it to a `LAG`/`LEAD` window function under the hood). SQL is still the better choice when you need more control over the window logic — the equivalent query is:
> ```sql
> SELECT month, revenue,
>        LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
> FROM (
>   SELECT DATE_TRUNC('month', created_at) AS month, SUM(total) AS revenue
>   FROM orders GROUP BY 1
> ) monthly;
> ```
> Caveat: `Offset()` references the previous *row*, not the previous *calendar period* — if your data is missing a month, that gap shifts the comparison, so make sure every period has a row.

**Q5.** Can a SQL question be added to a dashboard the same way as a Notebook question?
> **A:** Yes — once saved, SQL questions behave identically. They can be added to dashboards, used with dashboard filters (via template variables), and scheduled for alerts.

---

## Common Gotchas
- The SQL dialect depends on your database. The sample DB is H2/PostgreSQL-like.
- Text template variables pass raw strings — you may need quotes: `WHERE category = '{{category}}'`
- Field filters only work well when Metabase knows the column's semantic type (set in Admin).
- "View the SQL" on a Notebook question is read-only. Switching to SQL mode is one-way —
  you lose the Notebook view.
- `{{#question_id}}` references only work if you have permission to view that question.
