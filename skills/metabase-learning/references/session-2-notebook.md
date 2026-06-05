# Session 2: The Query Builder — Reference File

## Key Concepts to Teach

### 1. What a "Question" Is
- A Question is a saved query + visualisation
- Every chart or table you see in Metabase started as a Question
- Two ways to create one: **Query Builder** (visual) or **SQL Editor** (Session 4)

### 2. Starting a Question
- Click **New → Question**
- Choose a data source: a Table, Model, or saved Question
- Example: pick **Orders** as your starting table — you now have all 9 columns to work with

### 3. The Query Builder Stages (in order)
```
Data source → Filter → Summarize → Group by → Sort → Limit
```
Not all stages are required. You can stop after any step.

### 4. Filters — Which Rows to Include
Filters narrow *rows* before any calculation happens.

Examples using the sample tables:

| Goal | Filter to add |
|------|--------------|
| Only 2024 orders | Orders → Created_At → This year (or custom date range) |
| Only discounted orders | Orders → Discount → greater than → 0 |
| Only products in the "Gadget" category | Products → Category → is → Gadget |
| Only customers from California | People → State → is → CA |
| Only accounts on the "Business" plan | Accounts → Plan → is → Business |
| Only 5-star reviews | Reviews → Rating → equal to → 5 |

Multiple filters = AND logic by default.

### 5. Summarize — Collapsing Rows into Numbers
Summarize calculates an aggregate across all rows (or per group).

Examples:

| Goal | Summarize |
|------|-----------|
| Total revenue | Sum of Orders.Total |
| Average order value | Average of Orders.Total |
| Number of orders | Count of rows (on Orders) |
| Average product rating | Average of Products.Rating |
| Number of accounts | Count of rows (on Accounts) |
| Total discount given | Sum of Orders.Discount |

Without a Group By, Summarize returns a **single number**.

### 6. Group By — Breaking Results into Categories
Pair with Summarize to get one number per category.

Examples:

| Goal | Summarize + Group By |
|------|----------------------|
| Total revenue by product category | Sum of Total, grouped by Products.Category |
| Order count by month | Count of rows, grouped by Created_At → Month |
| Average rating by product | Average of Reviews.Rating, grouped by Reviews.Product_ID |
| Revenue by customer state | Sum of Total, grouped by People.State |
| Accounts by plan type | Count of rows, grouped by Accounts.Plan |
| Monthly new signups | Count of rows on People, grouped by Created_At → Month |

### 7. Saving a Question
- Click **Save** → name it → choose a Collection
- Saved questions appear in search and can be added to dashboards

---

## Active Recall Questions

**Q1.** You want to see only orders placed in 2024 where the discount was greater than zero. Which stage do you use, and how many conditions do you add?
> **A:** Filter stage. Two conditions: "Created_At is in 2024" AND "Discount > 0".

**Q2.** What's the difference between Summarize and Group By? Use the Orders table in your answer.
> **A:** Summarize calculates an aggregate — e.g. "Sum of Total" on Orders collapses all rows into one revenue number. Group By splits that number into categories — e.g. grouped by Category (via Products) gives you revenue per category. You always need Summarize first; Group By only makes sense alongside it.

**Q3.** If you Summarize with "Count of rows" on the Orders table but add no Group By, what is the result?
> **A:** A single number — the total count of all orders (after any filters you've applied).

**Q4.** You want to see total revenue by month for 2024. Walk through the exact query builder steps using the Orders table.
> **A:** (1) Pick Orders as data source. (2) Filter: Created_At is in 2024. (3) Summarize: Sum of Total. (4) Group By: Created_At → Month.

**Q5.** You want to find which US state has the most customers. What table do you start from, and what are your Summarize and Group By settings?
> **A:** Start from People. Summarize: Count of rows. Group By: State. Sort descending by count to see the top state first.

---

## Common Gotchas
- Filter = which rows. Summarize = what calculation. These are the most confused pair.
- Group By without a Summarize makes no sense — always pair them.
- When grouping by a date, always pick a time unit (Month, Week, Year) — grouping by raw
  Created_At creates one row per timestamp, which is almost never what you want.
- "Done" in the Summarize panel closes it but doesn't save the Question.
