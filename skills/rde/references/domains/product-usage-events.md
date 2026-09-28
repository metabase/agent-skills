# Product usage events

Fires on product event streams (`events`, `activity`, `usage`, `logins`, `page_views`, `tracks`, `identifies`, `workspaces`). Thresholds are proposed from profiling.

## Metrics

- DAU, WAU, MAU: distinct users with a qualifying event in the day, 7, or 28/30 days ending on the date; calendar week and month as a variant.
- Stickiness: average DAU over the period / MAU; variants DAU / MAU on one date, WAU / MAU for weekly products.
- Activation rate: signups in the cohort reaching the milestone within the window / cohort, the window counted from signup, never from the first event.
- N-day and unbounded retention: `references/methods/retention-and-cohorts.md`. Bracket retention: cohort users active within a custom range of days / cohort (Amplitude).

## Grains

| Grain | One row per | Carries |
| --- | --- | --- |
| Event | event, append-only, deduplicated | account, user, event name, timestamp, the properties questions need; `data_layer: internal` unless a question reads it |
| Account-day rollup | account per day, dense over the spine | event count, distinct users, one boolean per milestone, first and last event timestamp |

Metrics and segments live on the rollup and the account table; activation, engagement, and retention are columns there, computed in the transform, never a metric's row logic.

## Activation and engagement

1. Milestone: per event name, the share of accounts that ever emit it, split by later paid against not: `SELECT f.event_name, avg(CASE WHEN f.paid THEN 1 ELSE 0 END) AS paid_share, count(DISTINCT f.account_id) AS accounts FROM <first event per account and name> f GROUP BY 1`. Propose the largest separation most accounts can reach.
2. Window from signup: the days-to-milestone distribution, the knee found by the derivation rule in `references/domains/event-and-registration-data.md`; default 14 days.
3. Denominator: non-test accounts signed up in the period with a product account. The account table carries `signup_month`, `activated_at`, `days_to_activation`, `is_activated`; the activation metric is then a `share` over that flag with a `signup_month` breakout, the window read from `cfg_product` in the transform.

Active is N events on M distinct days in a trailing window, each derived from the distribution, the continuous measures carried beside the boolean. Presence and passive events (login, page view, background ping, email open) have their low end profiled before they count.

## Identity and arrival

- Pre-login events carry `anonymous_id`; an identify call links it to `user_id` (Segment). Stitch through the identify map before counting users; unstitched rows count once per anonymous id and are reported apart.
- Ids compare case-insensitively (Segment); shared devices and reused anonymous ids merge people wrongly: count users per anonymous id.
- Deduplicate on the message id; retries and replays duplicate events (confirm with the owner).
- Events arrive late and client clocks drift: date by the event timestamp, bound the lateness from `received_at − timestamp`, and hold the last days open until that bound passes (it is the lateness in the watermark, `references/time-and-entities.md`).

## Billing account to product account

Activation and revenue meet only on the conformed customer table (`references/time-and-entities.md`, Conformed entities; the key is asked). Never widen the rollup with billing columns by whichever join is at hand.

## Questions for the owner

- `active-events`: which events make a user active? Default: product actions, passive events out. Probe: share of users whose only events are passive. If wrong: active counts inflated by pings and logins.
- `active-window`: rolling or calendar windows? Default: rolling 28 days. Probe: MAU both ways for the last 3 months. If wrong: month lengths move MAU.
- `user-or-account`: count users or accounts? Default: users; accounts for B2B plans. Probe: the users-per-account distribution. If wrong: stickiness and retention on the wrong unit.
- `internal-users`: internal, test, and bot users excluded? Default: excluded by email domain and flag. Probe: events from internal domains and bot agents. If wrong: engagement overstated.
- `timezone`: which timezone defines a day? Default: the account's reporting timezone. Probe: DAU in UTC against local. If wrong: day boundaries shift DAU.
- `activation-milestone`: which event and window mean activated? Default: the separating event, 14 days. Probe: paid-versus-unpaid separation per event. If wrong: activation tracks nothing that predicts revenue.
- `event-lateness`: how late can events arrive? Default: the p99 of arrival delay. Probe: the arrival-delay histogram. If wrong: recent days undercounted, then restated.

## Traps

- Renamed or re-instrumented events split one behaviour across names; check first and last seen per event name.
- A tracking outage reads as churn; check event volume per day for gaps before reading retention.
- Unbounded retention for recent cohorts looks low because later days have not happened.
- Joining events to the current plan rewrites history; join by validity window.

## Invariants

- DAU ≤ WAU ≤ MAU on every date; unbounded retention ≥ N-day retention for every cohort and day.
- Every activated account has a signup before its milestone; a violation is a clock or backfill finding, never clipped.
- Cohort sizes for complete months never change between runs (the previous run's sizes kept in the build list's note).
- A cohort whose window has not closed carries `is_complete_period` false and is out of the rate.
- One row per event id after deduplication.

## Test cases

Per model; the activation window and the engagement N, M, and window are inputs of the fixture.

- Activation: a milestone inside the window, one on its last day, one the day after, one never, one before signup (flagged); `equals` on account, `activated_at`, `days_to_activation`, `is_activated`.
- Rollup: events on two of five spine days; `equals` on account, day, event count, distinct users, milestone booleans, so gap days are zero rows.
- Engagement: exactly N events on M days, N on fewer days, one just outside the window; `equals` on account, day, `is_active`.
- Identity: anonymous events before an identify, one anonymous id reused by two users; `equals` on event, stitched user.
- Cohort: a signup whose window has not closed by the last complete period; `empty` where it counts as complete.

## For answering

- Name the active definition: which events, which window (rolling or calendar), users or accounts.
- Stickiness is DAU / MAU; say which average.
- N-day and unbounded retention differ; name which, and that recent cohorts are incomplete.
- Activation is within a window from signup; name the milestone and the window.

Sources: Amplitude retention analysis documentation; Segment identify best practices.
