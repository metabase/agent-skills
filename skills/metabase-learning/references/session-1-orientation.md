# Session 1: Orientation — Reference File

## Key Concepts to Teach

### 1. What Metabase Is
- A Business Intelligence (BI) tool: it sits on top of your database and lets non-technical
  users explore data without writing SQL
- It does NOT store your data — it connects to an existing database and queries it
- Think of it as a "smart window" into your data

### 2. The Core Mental Model
Use this as a teaching scaffold throughout the curriculum — reference it when introducing
new concepts to show how the pieces fit together. Do not quiz it directly; the goal is
intuitive fluency, not recital.

```
Database and tables (your data source)
    └── Questions (queries against that data)
          └── Visualizations (charts and tables)
              └── Dashboards (collections of questions, charts, and tables)
                    └── Alerts & Subscriptions (automated delivery)
```

### 3. Home Screen Navigation
- **Home**: Recent items, pinned dashboards, getting-started content
- **Sidebar**: Browse data, Collections (folders), saved Questions
- **Search bar**: Global search for any question, dashboard, or table
- **New button**: Entry point for creating Questions, Visualizations, or Dashboards
- **Settings (gear icon)**: Admin panel (if you have admin access)

### 4. The Sample Database Tables
The sample database has seven tables — use these as your playground:

| Table | What it contains |
|-------|-----------------|
| Orders | Every purchase: ID, User_ID, Product_ID, Subtotal, Tax, Total, Discount, Created_At, Quantity |
| Products | Product catalog: ID, Title, Category, Vendor, Price, Rating, Created_At |
| People | Customer records: ID, Name, Birth_Date, Address, City, State, ZIP, Email, Source, Latitude, Longitude, Created_At |
| Reviews | Product reviews: ID, Product_ID, Reviewer, Rating, Body, Created_At |
| Accounts | Business accounts: ID, First_Name, Last_Name, Email, Plan, Source, Seats, Active_Subscription, Trial_Ends_At, Trial_Converted, Canceled_At, Legacy_Plan, Latitude, Longitude, Country, Created_At |
| Feedback | Account feedback: ID, Account_ID, Email, Date_Received, Rating, Body |
| Invoices | Billing: ID, Account_ID, Payment, Expected_Invoice, Plan, Date_Received |

### 5. How the Tables Relate
Understanding the joins helps make sense of the data:
- **Orders → People**: Orders.User_ID → People.ID (who placed each order)
- **Orders → Products**: Orders.Product_ID → Products.ID (what was ordered)
- **Reviews → Products**: Reviews.Product_ID → Products.ID (reviews for each product)
- **Feedback → Accounts**: Feedback.Account_ID → Accounts.ID (feedback from an account)
- **Invoices → Accounts**: Invoices.Account_ID → Accounts.ID (billing for an account)

### 6. Databases vs Tables vs Visualizations
- **Database**: The connected source — here, Metabase's Sample Database
- **Table**: A raw table as it exists in the database (e.g. Orders)
- **Visualization**: A representation of your data, be it a chart or a tabular format
  (not to be confused with a database table!)

### 7. Browsing Data
- Click "Browse data" → click the Sample Database → see all seven tables
- Click any table (e.g. Products) to see a live preview of its rows and columns

---

## Active Recall Questions

**Q1.** What is Metabase? Is it a database itself, or does it connect to one?
> **A:** Metabase is a BI tool that connects to an existing database. It doesn't store data — it queries your database and helps you explore and visualize results.

**Q2.** Orders has a User_ID column and People has an ID column. What does that relationship represent in plain English?
> **A:** It links each order to the customer who placed it. User_ID in Orders is a foreign key pointing to the ID of a row in People.

**Q3.** If you wanted to find a dashboard a colleague built last week but don't know where it's saved — what do you do?
> **A:** Use the global search bar at the top of the screen.

**Q4.** An analyst creates a Query called "Active Subscribers" from the Accounts table. What does that likely mean, and why is it useful?
> **A:** It's probably the Accounts table filtered to rows where Active_Subscription = true (and possibly with cleaner column names). It's useful because other users can start questions from it without needing to remember that filter — the logic is baked in once, correctly, for everyone.

---

## Common Gotchas
- Metabase is the interface, not the storage. All data lives in your database.
- What you see in Browse Data depends on your permissions — admins see everything.
