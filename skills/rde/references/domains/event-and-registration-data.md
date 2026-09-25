# Event and registration data

Any event, webinar, survey, or registration source: grains, the completion rule, threshold derivation, matching registrants to customer records, and the three report families; the router sends you here when the source is registration, attendance, or survey data. Every threshold and match rule is a default to profile, propose with evidence, and confirm at a `[CHECKPOINT]` ([../collaboration-contract.md](../collaboration-contract.md)).

## Grains

Build in this order, each model declaring its grain ([../layering-and-naming.md](../layering-and-naming.md)):

| Grain | One row per | Carries |
| --- | --- | --- |
| Registrant per event | person per event | registration, attendance, watch behaviour, customer match; the only grain that can be re-cut later |
| Event | event | registrations, attendees, completions, conversion rates, average watch duration, rolled up on the row |
| Series | recurring programme or campaign, where the source has one | the event metric set |
| Cohort and segment rollups | event type, customer status, plan, or acquisition cohort ([../entities-and-time.md](../entities-and-time.md) for the base set, follow set, and rate) | the same metric set sliced one way; siblings over the atomic model, never independent queries |

Two shapes for question data: a wide per-registrant table (one column per single-answer question) and a long answers table (one row per registrant, question, answer) for multi-select. Read the question catalog first: which questions exist and whether each is single-select, multi-select, or free text.

## The completion rule has two paths

One boolean satisfied by either path: attended live above a minimum duration, or watched the replay above a duration or percentage threshold.

- Define each path's rule on its own distribution; live and replay never share a cutoff.
- State the combination explicitly (default: union) and carry the satisfying path as a column.
- Carry the continuous measures (watch duration, watch percentage) beside the boolean so a different threshold is a re-run.
- If a path's measure is absent from the source, report the absence and stop; never substitute a constant.

## Derive every threshold from the distribution

1. Name the continuous measure behind the requested boolean: watch duration or percentage behind "completed", attendance duration behind "attended", recency behind "active".
2. Pull its distribution over the whole population, bucketed finely enough to see shape (deciles or fixed-width bands).
3. Find the natural break: a discontinuity, a knee, or an 80/20 boundary.
4. Present the distribution, the proposed cutoff, and the population each candidate captures; wait for confirmation.
5. Record the derivation beside the decision, and hold the value as a named constant.

## Short-attendance edge cases

A presence event is not an engagement event. Profile the low end before treating attended, opened, visited, or logged in as a fact:

| Shape | Treatment |
| --- | --- |
| Spike at or near zero duration | bots, accidental clicks, bounces, or instrumentation; report its size and ask whether it counts |
| Very short attendance and immediate drop-off | count them separately; a minimum-duration floor can move the headline more than any other rule, so measure what it removes before proposing it |
| Mass at the theoretical maximum | a cap, default, or saturated counter; check from that side too |
| Missing duration with a join timestamp present | a distinct population; null, never zero |

## Matching registrants to customer records

Registration forms are self-typed, so the match is a hypothesis; the general conformed-entity procedure is in [../entities-and-time.md](../entities-and-time.md), and these are its email rules.

1. Exact match first on normalised email (trimmed, lower-cased); report the exact-match rate before proposing anything else.
2. Domain match only as a fallback where exact fails and the business accepts company-level attribution; exclude consumer and free-mail domains with a maintained list, and carry the match method on every row.
3. Duplicates on the customer side (several rows per email or domain) fan out the join: `[CHECKPOINT]` with the volume, a sample, and the candidate tiebreakers (most recently created, earliest created, most recently active) for the owner to pick.
4. Unmatched rows stay, flagged as not an existing customer with customer columns null; never inner-join an enrichment, never drop or carry forward.
5. Re-check the match rate after every enrichment join against a threshold agreed up front (default: pause when the unmatched share exceeds 20 percent) and show the unmatched volume with sample rows.

The atomic model carries the match method and a matched boolean.

## The three report families

| Family | Shape | Rule |
| --- | --- | --- |
| Roster | who registered: name, company, role, status; a filtered, ordered read of the wide table | state which statuses count; "registered" and "confirmed" differ |
| Distribution | how the group splits on a single-select question or attribute, as shares | name the denominator; multi-select goes to the long table, grouped by question then answer, and the reply says shares sum past 100 percent |
| Open-ended digest | what people wrote in free text | quote the actual responses grouped into a few themes, with response count and empty count; counts alone discard the content |

Every report states its scope (all-time or a window, everyone or only confirmed) and its denominator.

## Cases a transform test pins

Per model, the fixture rows and expectations [../transform-tests.md](../transform-tests.md) asks for; the thresholds come from the `cfg_<domain>` input, so a re-derived cutoff is a change to the fixture's constant, not to the SQL.

- Registrant grain: one repeat registration that is a duplicate and one that is a real second sign-up, by the source's own identifiers; `equals` on registrant, event, `is_selected`.
- Completion: one registrant per path (live above the minimum, replay above the threshold), one satisfying both, one satisfying neither; `equals` on registrant, `is_completed`, the satisfying-path column.
- Thresholds: one row exactly at each cutoff and one just under it; `equals` on the boolean, the continuous measure carried beside it.
- Short attendance: a zero-duration row, a row with a join timestamp and no duration (null, never zero), a row at the theoretical maximum; `equals` on the treatment column.
- Event rollup: `empty` where attendees exceed registrants, where completions exceed attendees plus replay viewers, or where a registration falls after the event.

## Checks

- One row per registrant per event, asserted; a repeat registration is a duplicate to resolve or a real second sign-up, decided from the source's own identifiers.
- Attendees never exceed registrants per event; completions never exceed attendees plus replay viewers.
- Every event's registration window closes at or before the event; a row outside it is a finding.
- A raw source table with zero rows falls under the zero-row rule in [../collaboration-contract.md](../collaboration-contract.md).
- Report the population each threshold excludes beside the number it produces.
