# Session 3: Visualizations — Reference File

## Key Concepts to Teach

### 1. Visualizations Are Attached to Questions
- Every Question has a visualisation type
- The same data can be displayed as a table, bar chart, line chart, etc.
- Metabase auto-selects a type — you can always override it

### 2. Switching Visualisation Types
- After running a Question, click the **chart icon** in the bottom-left of the results area
- A panel shows all available types
- Not all types work for all data shapes (e.g. a map requires a geographic column)

### 3. Chart Type Guide with Sample Data Examples

| Chart Type | Best For | Sample DB Example |
|------------|----------|-------------------|
| **Table** | Row-level data, looking up records | All Orders with Discount > 0, showing ID, Total, Created_At |
| **Bar chart** | Comparing categories | Total revenue (Sum of Total) grouped by Products.Category |
| **Line chart** | Trends over time | Count of Orders grouped by Created_At → Month |
| **Area chart** | Volume/cumulative feel over time | Monthly new People signups (Created_At → Month) |
| **Pie / Donut** | Part-to-whole, few categories (≤5) | Count of Accounts grouped by Plan (Basic, Business, Premium) |
| **Row chart** | Bar chart rotated; long category names | Average Rating grouped by Products.Vendor |
| **Scatter plot** | Relationship between two numeric columns | Products.Price vs Products.Rating |
| **Map** | Geographic data | Count of People grouped by State (pin map) or People plotted by Latitude/Longitude |
| **Single number** | One KPI value | Total revenue: Sum of Orders.Total |
| **Gauge** | KPI with a target threshold | Average Reviews.Rating vs a 4.0 target |
| **Funnel** | Sequential stages with drop-off | Accounts by stage: Trial → Converted → Active |
| **Pivot table** | Cross-tabulation of two dimensions | Sum of Orders.Total by Category × Month |

### 4. Configuring a Chart (Settings panel)
Click **Settings** in the bottom-left after picking a chart type:

- **Axes**: which column goes on X vs Y; axis labels; min/max scale
  - Example: on a revenue-by-month line chart, set Y-axis min to 0 so dips aren't exaggerated
- **Series**: which columns to plot; colors; display names
  - Example: rename "Sum of Total" to "Revenue" in the chart legend
- **Display**: stacking (for bar/area), line style, data point labels
  - Example: stack a bar chart of Orders by Category to show each vendor's contribution
- **Goal line**: draw a horizontal target line
  - Example: draw a line at 4.0 on an average Reviews.Rating chart to show the quality target
- **Trend line**: adds a statistical regression line
  - Example: add a trend line to monthly revenue to see whether growth is accelerating

### 5. Downloading / Exporting
- Click the **download icon** (bottom-right of results)
- CSV / XLSX: raw data (e.g. export all Orders from 2024 for finance)
- PNG: the rendered chart image (e.g. screenshot of the revenue bar chart for a slide)
- Admins can restrict download permissions per group

---

## Active Recall Questions

**Q1.** You've run a Question: Count of Orders grouped by Created_At → Month. What chart type does Metabase likely auto-select, and is that the right choice?
> **A:** A line chart — and yes, that's correct. A line chart is ideal for showing a count trend over time.

**Q2.** You want to show total revenue broken down by product category. Which chart type and why?
> **A:** A bar chart. Each bar represents a category (Gadget, Widget, Gizmo, etc.) and its height represents Sum of Orders.Total. Bar charts are best for comparing discrete categories.

**Q3.** Your Accounts table has a Plan column with values Basic, Business, and Premium. You want to show the proportion of accounts on each plan. What chart type, and what's the gotcha?
> **A:** Pie or Donut — but only because there are ≤ 5 categories. If Plan had 8+ values, a bar chart would be clearer. Pie charts become unreadable with many slices.

**Q4.** What's a Goal Line and how would you use it on an average Reviews.Rating chart?
> **A:** A Goal Line is a horizontal line drawn at a specific value. On a Reviews.Rating chart, you'd set it at 4.0 to visually show whether product quality is above or below your target — any bar below the line needs attention.

**Q5.** The People table has Latitude and Longitude columns. What visualisation type does this unlock, and what would a useful question look like?
> **A:** A pin Map — you can plot each customer's location geographically. A useful question: show all People records as dots on a map to visualise where your customers are concentrated.

---

## Common Gotchas
- Metabase auto-picks a chart type but it's often not the best — always check it.
- Pie charts are overused. More than 5 slices → use a bar chart.
- The Settings panel changes per chart type — explore it fresh each time you switch types.
- PNG downloads export the *chart*. Use CSV/XLSX to get the raw data (e.g. for Orders).
- Area charts are not cumulative by default — they just shade under the line.
