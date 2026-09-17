# Product usage events

Any product event stream (table names like `events`, `activity`, `usage`, `logins`, `page_views`, `workspaces`); the router sends you here for activation, engagement, or product retention. Every threshold below is a default proposed from profiling and confirmed at a `[CHECKPOINT]` ([../collaboration-contract.md](../collaboration-contract.md)), held in `cfg_<domain>` ([../layering-and-naming.md](../layering-and-naming.md)).

## Two grains

| Grain | One row per | Carries |
| --- | --- | --- |
| Event | event, append-only, immutable | account, user, event name, timestamp, properties the questions need; `visibility_type: technical` unless a question reads it |
| Account-day rollup | account per day, dense over the spine ([../entities-and-time.md](../entities-and-time.md)) | event count, distinct users, one boolean per milestone event, first and last event timestamp |

Metrics and segments live on the rollup and on the account table; the event table serves detail and re-cuts. Activation, engagement, and retention are columns the rollup or the account table computes, never a metric's row logic.

## Activation, three confirmable defaults

1. Milestone event. Profile: per event name, the share of accounts that ever emit it, split by accounts that later paid versus not: `SELECT event_name, avg(CASE WHEN paid THEN 1 ELSE 0 END) AS paid_share, count(DISTINCT account_id) FROM first_event_per_account GROUP BY 1`. Propose the event with the largest paid-versus-unpaid separation that most accounts can reach.
2. Window from signup. Profile the distribution of days from signup to the first milestone event; pick the knee by the derivation rule in [event-and-registration-data.md](event-and-registration-data.md); default 14 days.
3. Cohort denominator. Accounts signed up in the period, non-test, that have a product account; the account table carries `signup_month`, `activated_at`, `days_to_activation`. Activation rate on the account table: `["share", {}, ["<=", {}, ["field", {}, <days_to_activation-id>], 14]]` with a `signup_month` breakout, the window constant read from `cfg_product`.

## Engagement thresholds

`active` is N events on M distinct days in a trailing window; derive N, M, and the window from the distribution per the derivation rule in [event-and-registration-data.md](event-and-registration-data.md), carry the continuous measures beside the boolean, and report the population each candidate excludes. Presence events (login, page view) profile their low end before counting as engagement.

## Billing account to product account

Activation and revenue meet only on the conformed customer table ([../entities-and-time.md](../entities-and-time.md)): find the crosswalk (an id column naming the other side, a shared external id, a normalised email domain), report the match rate, `[CHECKPOINT]` the key choice, and give every fact table the conformed key as a metadata FK. Never widen the event rollup with billing columns by whichever join is at hand.

## Cases a transform test pins

Per model, the fixture rows and expectations [../transform-tests.md](../transform-tests.md) asks for; the activation window and the engagement N, M, and window come from the `cfg_product` input.

- Activation: one account whose milestone lands inside the window, one on its last day, one the day after, one that never emits it, one whose milestone precedes its signup (a finding row, flagged); `equals` on account, `activated_at`, `days_to_activation`, `is_activated`.
- Account-day rollup: an account with events on two of five spine days; `equals` on account, day, event count, distinct users, the milestone booleans, so gap days are zero rows and not missing rows.
- Engagement: one account exactly at N events on M days, one at N events on fewer days, one just outside the trailing window; `equals` on account, day, `is_active`, the continuous measures beside it.
- Cohort: a signup in a month whose window has not closed by `last_complete_period`; `empty` where such a cohort is counted with `is_complete_period = true`.

## Checks

- Every activated account has a signup timestamp before its milestone event; a violation is a clock or backfill finding, never clipped.
- Cohort denominators are stable when re-run: the count per `signup_month` for complete months matches the last run's count kept in the model's Models row `note` in STATE.md ([../state.md](../state.md)).
- No activation is counted past the last complete period unless flagged: a cohort whose window has not closed carries `is_complete_period = false` ([../modeling-decisions.md](../modeling-decisions.md)) and is excluded from the rate.
