# Session 5: Dashboards — Reference File

## Key Concepts to Teach

### 1. What a Dashboard Is
- A collection of saved Questions displayed together on one screen
- Each Question becomes a "card" on the dashboard
- Dashboards are read-only for viewers — they run questions and show results
- They are the primary deliverable you share with stakeholders

### 2. Creating a Dashboard
- **New → Dashboard** → name it → choose a Collection
- Click **Add a question** to search for saved Questions to add
- Questions must be saved before they can be added

### 3. Example Dashboards You Could Build with the Sample DB

**Sales Overview Dashboard:**
- Card 1: Total Revenue (Single number — Sum of Orders.Total)
- Card 2: Orders This Month (Single number — Count of Orders filtered to this month)
- Card 3: Revenue by Month (Line chart — Sum of Total grouped by Created_At → Month)
- Card 4: Revenue by Category (Bar chart — Sum of Total grouped by Products.Category)
- Card 5: Top 10 Products by Revenue (Table)

**Customer Insights Dashboard:**
- Card 1: Total Customers (Count of People)
- Card 2: New Customers by Month (Line chart — Count of People grouped by Created_At → Month)
- Card 3: Customers by State (Map — Count of People grouped by State)
- Card 4: Average Order Value by Source (Bar chart — Avg of Orders.Total grouped by People.Source)

**Account Health Dashboard (B2B):**
- Card 1: Active Subscribers (Count of Accounts where Active_Subscription = true)
- Card 2: Accounts by Plan (Pie — Count grouped by Accounts.Plan)
- Card 3: Trial Conversion Rate (Count where Trial_Converted = true / total trials)
- Card 4: Recent Feedback (Table of Feedback sorted by Date_Received desc)
- Card 5: Invoices Due (Table of Invoices where Payment is null or pending)

### 4. The Dashboard Grid
- Cards snap to a grid — drag the bottom-right corner to resize
- Drag from the card header to reposition
- Best practice: KPI single-number cards across the top, charts in the middle, detail
  tables at the bottom

### 5. Text and Heading Cards
- **Heading card**: bold title line — e.g. "── Revenue ──" between sections
- **Text card**: full Markdown — use to explain what a chart shows, link to a related
  dashboard, or add context ("Revenue includes refunds; net revenue is on the Finance dashboard")

### 6. Dashboard Filters — The Key Power Feature
A single filter widget that controls multiple cards simultaneously.

**Example: Date Range filter on a Sales Dashboard**
- Add filter type: Date Range
- Wire it to:
  - Orders.Created_At on the Revenue by Month card
  - Orders.Created_At on the Total Revenue card
  - Orders.Created_At on the Top Products card
- Now a viewer can set "Last 30 days" and all three cards update at once

**Example: Plan filter on an Account Health Dashboard**
- Add filter type: Text / Category
- Wire it to Accounts.Plan
- Viewer selects "Business" → all account cards filter to Business accounts only

**Critical rule**: A card only responds to a filter if you explicitly wire it up.
Unwired cards show unfiltered data regardless of what the filter is set to.

### 7. Auto-refresh and Sharing
- **Auto-refresh**: clock icon → 1, 5, 10, 15, 30, 60 min intervals — useful for live ops displays
- **Public link**: anyone can view without logging in (admin must enable this feature)
- **Embed**: iframe embed for internal tools or external websites
- **Subscriptions**: covered in Session 7

---

## Active Recall Questions

**Q1.** Before adding a question to a dashboard, what must you do first?
> **A:** Save the question. Unsaved questions cannot be added to dashboards.

**Q2.** You build a Sales Dashboard with a Date Range filter. You wire it to the Revenue chart and the Orders table card, but not to the Top Products card. A user sets the filter to "Last 7 days." What does each card show?
> **A:** Revenue chart and Orders table filter to the last 7 days. The Top Products card is unwired — it still shows all-time data, unaffected by the filter.

**Q3.** Describe how you'd build an Account Health Dashboard that lets a viewer filter everything by Plan (Basic, Business, Premium).
> **A:** (1) Build and save questions for each metric, all using the Accounts table or related tables. (2) Create the dashboard and add all cards. (3) Add a Text/Category filter. (4) Wire it to the Plan column on every relevant card. Now one filter click updates the whole view.

**Q4.** What's the difference between a text card and a heading card?
> **A:** A heading card is a simple bold title. A text card supports full Markdown — paragraphs, bullet points, links, and richer formatting for adding context around charts.

**Q5.** Your ops team wants a dashboard showing live order volume on a TV screen in the office. What do you set up?
> **A:** Enable Auto-refresh on the dashboard — set it to every 1–5 minutes so the displayed data stays current without anyone manually refreshing.

---

## Common Gotchas
- Most common mistake: adding a filter but forgetting to *wire* it to cards. The widget appears
  but does nothing until connected.
- SQL question cards support filters only if the SQL uses a matching template variable.
- Public links expose all dashboard data — confirm with your admin before sharing externally.
- Auto-refresh sends a fresh query per card on every cycle — heavy dashboards can strain the DB.
- Editing a saved Question updates it everywhere it's used, including all dashboards.
