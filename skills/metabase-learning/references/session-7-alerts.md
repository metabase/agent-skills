# Session 7: Alerts & Subscriptions — Reference File

## Key Concepts to Teach

### 1. The Two Automation Features

| Feature | Attached To | Trigger | Delivery |
|---------|-------------|---------|----------|
| **Alert** | A Question | A condition (threshold) | Email, Slack, or webhook *when* it fires |
| **Dashboard Subscription** | A Dashboard | A schedule (time-based) | Email or Slack *on a schedule* |

Simple rule: **Alerts = "notify me *if* something happens"**. **Subscriptions = "send me this *when* the clock says so."**

### 2. Alerts — Condition-Based Notifications

**Alert types (three):**
- **When a question returns a result**: fires when a Question that normally returns nothing suddenly returns rows
- **When a time series crosses a goal line**: fires when a trend chart crosses a goal line you've set
- **When a progress bar reaches its goal**: fires when a progress-bar question hits (or drops below) its goal

**Sample DB examples:**

| Goal | Question to alert on | Condition |
|------|----------------------|-----------|
| Know when a product drops below 3 stars | Average of Reviews.Rating grouped by Product | When result goes below goal line set at 3.0 |
| Know when daily orders drop below 50 | Count of Orders for today | When result goes below goal line at 50 |
| Know when a trial account cancels | Accounts where Canceled_At is today | When results have rows |
| Know when a payment is overdue | Invoices where Date_Received < today AND Payment is null | When results have rows |
| Know when feedback score drops | Average of Feedback.Rating for this week | When result goes below 3.5 |

**Setting up an alert:**
1. Open a saved Question
2. Click the **three-dots (…) menu** (top-right) → **Create an alert**
3. Choose alert type and condition
4. Set check frequency: by-the-minute, hourly, daily, weekly, monthly, or a custom cron schedule
5. Set delivery: email, Slack, or a webhook, and the recipients
6. Save

**Important**: Alerts only fire when a condition is *newly* met — not on every check.
If daily orders stay below 50 for a week, you get one email, not seven.

### 3. Dashboard Subscriptions — Scheduled Delivery

**Sample DB examples:**

| Dashboard | Subscription | Schedule |
|-----------|-------------|----------|
| Sales Overview | Email to sales team | Monday 8am — weekly revenue recap |
| Account Health | Slack to #customer-success | Daily 9am — trial and churn monitoring |
| Invoice Status | Email to finance | 1st of each month — billing review |
| Customer Map | Email to marketing | Monthly — geographic distribution update |

**Setting up a subscription:**
1. Open a dashboard
2. Click the **paper plane icon** (subscriptions, top-right)
3. Choose Email or Slack
4. Set recipients and schedule
5. Optionally bake in filter values (e.g. always send last 7 days)
6. Save

Email subscriptions send a screenshot of each card + optional data attachment.
Slack subscriptions send chart images directly to a channel.

### 4. Requirements
- **Email**: admin must configure SMTP (Admin → Settings → Email)
- **Slack**: admin must install the Metabase Slack app (Admin → Settings → Slack)

---

## Active Recall Questions

**Q1.** What's the core difference between an Alert and a Dashboard Subscription?
> **A:** An Alert fires based on a *condition* being met (e.g. a metric crosses a threshold). A Subscription fires on a *schedule* regardless of what the data shows.

**Q2.** You want to be notified the moment any invoice in the Invoices table is overdue (Date_Received in the past and Payment is null). Which feature, and what type of condition?
> **A:** An Alert on a Question that returns overdue invoices. Use "when a question returns a result" — normally the question returns nothing, and you want to know the instant a row appears.

**Q3.** Your CEO wants the Sales Overview Dashboard every Monday at 7am. Walk through the setup.
> **A:** Open the Sales Overview Dashboard → click the subscriptions icon (paper plane) → choose Email → add the CEO's email → set schedule to weekly, Monday, 7:00am → Save.

**Q4.** You set up an alert: "when Feedback.Rating average drops below 3.5." It fires on Tuesday. The score stays below 3.5 for the rest of the week. How many alert emails do you receive?
> **A:** One — Metabase alerts fire when the condition is *newly* met, not on every check cycle.

**Q5.** What must an admin configure before email alerts will work?
> **A:** SMTP settings — the outbound email server configuration under Admin → Settings → Email.

---

## Common Gotchas
- "When a question returns a result" only fires when the Question goes from 0 rows → some rows.
  If the overdue invoices query always returns rows, the alert never fires again after the first time.
- Dashboard subscriptions send a *snapshot* — a screenshot of the data at send time, not a live link.
- Slack subscriptions require the Metabase Slack app (not just a webhook URL).
- Checking alerts hourly on a complex JOIN query (e.g. Orders + People + Products) can
  strain the database — be deliberate about frequency.
- Users can only subscribe Metabase-registered users to subscriptions by default.
