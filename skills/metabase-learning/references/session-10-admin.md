# Session 10: Admin Basics — Reference File

## Key Concepts to Teach

### 1. Who Needs to Know Admin Basics?
Even non-admins benefit from understanding this layer — it explains:
- Why some columns have friendly names (e.g. "Customer" instead of "User_ID")
- Why some tables are hidden or restricted
- Why filter dropdowns in some columns are smart and in others are blank text boxes
- How to communicate clearly with your admin when requesting changes

### 2. Connecting a Database
**Admin → Databases → Add database**

For the sample DB, Metabase ships with an H2 database pre-connected.
For a real connection, you'd provide: database type, host, port, database name,
username, password (read-only recommended), and SSL settings.

**Sync vs Scan:**
- **Sync**: updates Metabase's list of tables and columns (runs hourly by default)
  Example: if someone adds a `Refunds` table to the database, sync picks it up
- **Scan**: samples column values to power filter suggestions (runs daily)
  Example: scanning Accounts.Plan finds "Free", "Pro", "Enterprise" — enabling a
  dropdown filter instead of a blank text box

### 3. Table Metadata — Making Data User-Friendly
**Admin → Table Metadata → [Database] → [Table]** (this section was formerly called "Data
Model"; on Pro/Enterprise the same editing also lives in Data Studio → Data structure)

This is where raw column names get transformed into something usable.

**Examples from the sample DB:**

| Table | Raw column | What admin changes it to | Why |
|-------|-----------|--------------------------|-----|
| Orders | User_ID | "Customer" | Clearer for non-technical users |
| Orders | Created_At | "Order Date" | More natural language |
| Accounts | Active_Subscription | "Active?" | Shorter, obvious |
| People | Created_At | "Joined" | Domain-appropriate |
| Invoices | Expected_Invoice | "Invoice Amount" | Removes jargon |

**Field types** tell Metabase how to render and filter a column:

| Column | Field type to set | Effect |
|--------|-------------------|--------|
| People.Email | Email | Renders as a clickable mailto link |
| Products.Rating | Score | Enables star-rating display |
| People.Latitude + Longitude | Latitude / Longitude | Enables pin map visualisations |
| Accounts.Country | Country | Enables filled map by country |
| Orders.Total | Currency | Adds $ formatting throughout |
| Accounts.Plan | Category | Generates a dropdown filter |

**Hiding columns**: mark internal columns as "Hidden" so they don't clutter the UI.
Example: hide Orders.Tax if finance is the only team that needs it.

### 4. People & Groups
**Admin → People**

- **People**: add, disable, and manage individual users
- **Groups**: permissions are applied to groups, not individuals. Examples:
  - `Sales Team` — access to Sales collection + Orders/Products/People data
  - `Finance` — access to Invoices, Accounts; can view but not query raw Orders
  - `Customer Success` — access to Accounts, Feedback, Reviews
  - `Administrators` — full access

Every user automatically belongs to **All Users** — this is the permission floor.

### 5. Permissions
**Admin → Permissions**

**Collection permissions (per group):**
- **Curate**: can add, edit, move content
- **View**: read-only
- **No access**: collection is hidden entirely

**Data permissions** are now split into two separate settings per group × database (set per
table with "Granular"):

- **View data** — whether a group can see the data at all. Options: *Can view*, *Granular*
  (set per table), *Row and column security*, *Impersonated* (Pro/Enterprise), *Blocked*.
- **Create queries** — whether a group can build their own questions on that data. Options:
  *Query builder and native* (SQL), *Query builder only*, *Granular*, *No*.

So the old "No self-service" idea (view dashboards but don't build questions) is now
expressed as **View data: Can view** + **Create queries: No**. There are also separate
permission types for **Download results**, **Manage table metadata**, **Manage database**,
and **Transforms**.

**Example permission setup for the sample DB** (shown as *View data / Create queries*):

| Group | Orders | Products | People | Accounts | Invoices | Feedback |
|-------|--------|----------|--------|----------|----------|----------|
| Sales Team | Can view / Query builder | Can view / Query builder | Can view / Query builder | Can view / No | Blocked / — | Can view / No |
| Finance | Can view / Query builder | Can view / No | Can view / No | Can view / Query builder | Can view / Query builder | Can view / No |
| Customer Success | Can view / No | Can view / No | Can view / No | Can view / Query builder | Can view / No | Can view / Query builder |

### 6. Caching
**Admin → Performance** (caching settings moved here from the old Admin → Settings → Caching)

- Stores query results for a set time; cached questions load instantly
- Trade-off: speed vs data freshness
- Example: the "Revenue by Month" chart on the Sales Overview Dashboard changes slowly —
  caching it for 24 hours is fine. A "Live Orders Today" card should never be cached.

---

## Active Recall Questions

**Q1.** What's the difference between a Sync and a Scan in Metabase?
> **A:** A Sync updates Metabase's knowledge of which tables and columns exist in the database (structural). A Scan samples column values to power smart filter dropdowns (content). Example: Sync would detect a new Refunds table; Scan would find the values in Accounts.Plan to build a dropdown.

**Q2.** A non-technical user complains that the Orders table shows "User_ID" instead of "Customer." Where do you fix this, and what do you change?
> **A:** Admin → Table Metadata → Sample Database → Orders → find the User_ID column → edit its Display Name to "Customer". This change appears across Metabase without touching the database.

**Q3.** The Finance team should see Invoices data but shouldn't be able to build their own questions from raw Orders data — only view dashboards powered by it. What permission setting applies?
> **A:** Set the Finance group's Orders permission to **View data: Can view** + **Create queries: No** (the modern equivalent of the old "No self-service"). They see dashboards using Orders data, but the table doesn't appear when they try to build a new Question.

**Q4.** You add a new analyst to Metabase without adding them to any custom group. What permissions do they have?
> **A:** The permissions of the **All Users** group — which every Metabase user belongs to automatically. This is the permission floor.

**Q5.** The Account Health Dashboard has 6 cards, several involving JOINs across Accounts, Feedback, and Invoices. It's slow. What can you do, and what's the trade-off?
> **A:** Enable caching for the dashboard or individual Questions. The trade-off: cards load instantly but may show data that's hours old depending on the cache duration. Acceptable for a daily review; not for a live ops screen.

---

## Common Gotchas
- Always use a read-only database user for the Metabase connection — it can't modify data.
- Hiding a column in Admin → Table Metadata only hides it from the UI, not from raw SQL queries.
- Permissions are additive across groups, but All Users is the floor — you can't give a group
  *less* than All Users without restricting All Users first.
- After connecting a new database, metadata is incomplete until the first sync and scan finish.
- Setting People.Latitude and People.Longitude field types to Latitude/Longitude is what
  unlocks the pin map visualisation — without this, the map option won't appear.
