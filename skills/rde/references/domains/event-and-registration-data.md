# Event and registration data

Fires on event, webinar, survey, and registration sources.

## Metrics

- Registrations: registrants per event in the counted statuses; "registered" and "confirmed" differ.
- Attendance rate: registrants who attended live / registrants; over confirmed registrants as a variant.
- Completion rate: registrants satisfying either completion path / registrants; variants over attendees, live only.
- Average watch time: time in session per attendee, summed over joins; median as a variant, replay time apart.
- Match rate: registrants matched to a customer record / registrants, exact email only or with the domain fallback.

Webinar tools report attended yes or no, join and leave times, and total time in session per registrant, with dial-in and room attendees listed apart (Zoom).

## Grains

Build in this order, each model's grain in its description before it is built:

| Grain | One row per | Carries |
| --- | --- | --- |
| Registrant per event | person per event | registration, attendance, watch behaviour, customer match; the only grain that can be re-cut |
| Event | event | registrations, attendees, completions, rates, average watch time |
| Series | recurring programme or campaign, where one exists | the event metric set |
| Cohort and segment rollups | event type, customer status, plan, or acquisition cohort | siblings over the atomic model, never independent queries |

Question data takes two shapes: a wide per-registrant table (one column per single-answer question) and a long answers table (registrant, question, answer) for multi-select. Read the question catalogue first (single-select, multi-select, free text), and read question labels from it in the query, never typed as literals.

## Completion and thresholds

One boolean satisfied by either path: attended live above a minimum duration, or watched the replay above a duration or percentage.

- Each path's cutoff comes from its own distribution; live and replay never share one. Default combination: union, the satisfying path carried as a column.
- Carry watch duration and percentage beside the boolean so another threshold is a re-run.
- A path whose measure is absent from the source is reported and stops; never a constant in its place.

The derivation rule, for any boolean over a continuous measure (duration behind attended, percentage behind completed, recency behind active):

1. Pull the distribution over the whole population through `q()`, in deciles or fixed bands.
2. Find the natural break: a discontinuity, a knee, an 80/20 boundary.
3. Offer each candidate cutoff with the population it captures; the chosen one is a decision, the derivation in its readings, the value in `cfg_<domain>`.

| Low-end shape | Treatment |
| --- | --- |
| Spike at or near zero duration | bots, accidental clicks, bounces; report its size and ask |
| Very short attendance | count apart; a floor can move the headline more than any other rule, so measure what it removes |
| Mass at the theoretical maximum | a cap, a default, or a saturated counter |
| Join time present, duration missing | a distinct population; null, never zero |

## Matching registrants to customers

Registration forms are self-typed, so the match is a hypothesis (`references/time-and-entities.md`, Conformed entities).

1. Exact match on normalised email (trimmed, lower-cased); report its rate first.
2. Domain match only as a fallback the business accepts, free-mail domains excluded by a maintained list, the match method on every row.
3. Several customer rows per email or domain fan out the join: a stop with the volume, a sample, and the tiebreakers (most recent, earliest, most recently active).
4. Unmatched rows stay, customer columns null, flagged; never inner-join an enrichment.

## Report families

| Family | Shape | Rule |
| --- | --- | --- |
| Roster | who registered, a filtered read of the wide table | state the counted statuses; personal fields only with consent |
| Distribution | shares across a single-select question or attribute | name the denominator; multi-select reads the long table and its shares sum past 100 percent |
| Open-ended digest | what people wrote | quote responses grouped into a few themes, with response and empty counts; counts alone discard the content |

Every report states its scope (window, statuses) and its denominator.

## Questions for the owner

- `counted-statuses`: which registration statuses count? Default: confirmed and attended. Probe: registrants by status. If wrong: registrations over- or under-stated.
- `live-threshold`: minimum live minutes to count as attended? Default: the distribution's break. Probe: attendees per candidate cutoff. If wrong: attendance rate moves most.
- `replay-threshold`: replay duration or percentage that completes? Default: the replay distribution's break. Probe: completions per cutoff. If wrong: completion rate off.
- `completion-paths`: union of live and replay, or live only? Default: union. Probe: completions per path and both. If wrong: completion rate off by the replay share.
- `match-method`: exact email only, or the domain fallback? Default: exact, domain only if accepted. Probe: match rate each way, a sample of domain matches. If wrong: customer attribution wrong.
- `unmatched-pause`: unmatched share that stops the build? Default: 20 percent. Probe: unmatched volume with sample rows. If wrong: a bad join ships silently.

## Traps

- One person joins several times: sum the joins, never count rows as attendees.
- A repeat registration is a duplicate or a real second sign-up; decide from the source's own identifiers.
- Dial-in and room attendees sit apart from named registrants (Zoom).
- A presence event is not engagement: profile the low end before counting attended, opened, or visited.

## Invariants

- One row per registrant per event.
- Attendees ≤ registrants per event; completions ≤ attendees plus replay viewers.
- Every registration falls at or before its event; a row outside is a finding.
- The match rate is re-checked after every enrichment join.

## Test cases

Per model; thresholds are inputs of the fixture, so a re-derived cutoff changes the fixture's constant, not the SQL.

- Registrant grain: a duplicate repeat registration and a real second sign-up; `equals` on the winning rows' registrant and event.
- Completion: one registrant per path, one satisfying both, one neither; `equals` on registrant, `is_completed`, the satisfying path.
- Thresholds: a row exactly at each cutoff and one just under; `equals` on the boolean and its measure.
- Short attendance: zero duration, a join with no duration (null), a row at the maximum; `equals` on the treatment column.
- Event rollup: `empty` where attendees exceed registrants or a registration falls after the event.

## For answering

- State the counted statuses and the denominator (registrants, confirmed, attendees).
- Completion is live or replay above cutoffs the owner chose; name them.
- Customer attribution is a match; give the method and the match rate.
- Multi-select shares sum past 100 percent.

Sources: Zoom webinar attendee report documentation.
