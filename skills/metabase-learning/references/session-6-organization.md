# Session 6: Data Organization — Reference File

## Key Concepts to Teach

### 1. Collections — Metabase's Folder System
- Collections are folders for organising Questions, Dashboards, and Models
- **Personal Collection**: private to you — like a drafts folder
- **Shared Collections**: visible to others based on permissions
- Collections can be nested (sub-collections)

Suggested structure for the sample DB:
```
Our Analytics/
├── Sales/
│   ├── Sales Overview Dashboard (pinned)
│   ├── Revenue by Category
│   └── Monthly Order Trends
├── Customers/
│   ├── Customer Map
│   └── New Signups by Month
├── Products/
│   ├── Top Rated Products
│   └── Review Analysis
└── Accounts & Billing/
    ├── Account Health Dashboard (pinned)
    ├── Trial Conversion Funnel
    └── Invoice Status
```

### 2. Pinning Items
- Pin important items to the top of a collection so they're visible immediately
- Three-dot menu → Pin → appears as a large preview card
- Example: pin "Sales Overview Dashboard" in the Sales collection so it's the first
  thing the team sees when they open it

### 3. Models — Curated Data Layers
A Model is a saved query that acts as a clean, trusted starting point for new Questions.
Users pick a Model instead of a raw table when starting a new Question.

**Useful Models from the sample DB:**

| Model Name | Based On | What It Does |
|------------|----------|--------------|
| Completed Orders | Orders | Filters out orders with no Total (nulls), renames User_ID → Customer ID |
| Active Accounts | Accounts | Filters to Active_Subscription = true, hides internal columns |
| Reviewed Products | Products + Reviews | Pre-joined view with average rating per product |
| Converted Trials | Accounts | Filters to Trial_Converted = true, shows conversion date |
| Recent Feedback | Feedback | Last 90 days of feedback, joined to Accounts for company name |

Creating a Model: **New → Model** → build it (query builder or SQL) → Save as Model.
The Model then appears alongside tables when users start a new Question.

### 4. Segments — Reusable Filters
A Segment is a saved filter definition users can apply from the filter menu.

**Examples from the sample DB:**

| Segment Name | Table | Definition |
|-------------|-------|------------|
| High-Value Orders | Orders | Total > 150 |
| Discounted Orders | Orders | Discount > 0 |
| California Customers | People | State = 'CA' |
| Business Accounts | Accounts | Plan = 'Business' AND Active_Subscription = true |
| 5-Star Reviews | Reviews | Rating = 5 |

Managed under **grid icon → Admin → Table Metadata → [Table] → Segments** (this section
was formerly called "Data Model"). On Pro/Enterprise, prefer managing segments in **Data
Studio** (Session 8). Once defined, users see "Business Accounts" in the filter dropdown
instead of having to reconstruct the conditions every time.

### 5. Metrics — Reusable Aggregations
A Metric is a saved Summarize definition — ensures everyone uses the same calculation.

**Examples from the sample DB:**

| Metric Name | Table | Definition |
|------------|-------|------------|
| Total Revenue | Orders | Sum of Total |
| Average Order Value | Orders | Average of Total |
| Average Product Rating | Reviews | Average of Rating |
| Active Subscriber Count | Accounts | `CountIf([Active_Subscription] = true)` |

Metrics are now first-class items that live in **collections** (alongside Questions and
Dashboards). Create one via the command palette or **+ New → Metric** (or Browse → Metrics
→ +), pick a data source, and define the aggregation. Filters are expressed with
conditional aggregations like `CountIf` / `SumIf` rather than a separate baked-in filter.
Once defined, users pick "Total Revenue" from the Summarize menu instead of re-creating
`Sum of Total` — and everyone gets the same number.

### 6. The Hierarchy of Trust
```
Raw Tables (anyone queries anything)
  → Models (curated, clean starting points)
    → Segments & Metrics (consistent definitions)
      → Questions (built on reliable foundations)
        → Dashboards (trustworthy, org-wide reports)
```

---

## Active Recall Questions

**Q1.** What's the difference between a Personal Collection and a shared Collection?
> **A:** A Personal Collection is private — only you can see it, good for drafts and experiments. Shared Collections are visible to others based on permissions, and are for team-facing, published content.

**Q2.** A new analyst keeps filtering Accounts to Active_Subscription = true before starting any question. How do you fix this once, for everyone?
> **A:** Create an "Active Accounts" Model based on the Accounts table, with that filter baked in. Now analysts start questions from the Model instead of the raw table — the filter is always there.

**Q3.** What's the difference between a Segment and a Model?
> **A:** A Segment is just a saved *filter* — it defines which rows to include (e.g. "Business Accounts" = Plan = Business AND Active_Subscription = true). A Model is an entire saved *dataset* — a full starting point for new questions, which may include joins, renamed columns, and multiple filters.

**Q4.** Why would a company define "Total Revenue" as a Metric rather than letting analysts create Sum of Total themselves?
> **A:** To ensure consistency. If Total Revenue is defined once as Sum of Orders.Total (not Subtotal, not including tax), everyone uses the same number. It prevents different teams reporting different revenue figures from the same database.

**Q5.** You want the Account Health Dashboard to be the first thing your customer success team sees when they open the Accounts collection. What do you do?
> **A:** Pin the dashboard to the top of the Accounts & Billing collection (three-dot menu → Pin).

---

## Common Gotchas
- Models look like tables in the question picker — there's a small icon to distinguish them.
- Deleting a Model that other Questions depend on will break those Questions.
- Segments are managed in Admin → Table Metadata (or Data Studio); Metrics now live in collections, created via + New → Metric.
- Collection permissions are inherited by sub-collections by default — plan your structure first.
- Pinning doesn't change permissions — pinned items are still subject to the same access rules.
