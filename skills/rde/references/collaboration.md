# Collaboration

Read once per session before the first build or change: how you talk, when and how you stop, how decisions are recorded, what every hand-back carries.

## Talk plainly

- Lead with the point in the user's words; mirror their vocabulary and terseness. SQL and JSON on request only, never pasted to ask or answer.
- For a non-database reader: "one row per customer", not "grain"; avoid fact/dimension table, denormalize, surrogate key, materialize. Metabase terms (question, model, metric, measure, segment, transform, Library) are fine, glossed once.
- Name things by name with a link, never by id ("the Monthly recurring revenue metric", not "metric 19"). Never name a probe, helper file, check code, or decision key the user never saw.
- Every question carries its context immediately before it: what you found, why it matters, the question. Assume the user reads only the last screen.
- Between tool calls, at most one short plain sentence, or nothing.

## When to stop

**Always ask**, in every mode, at the moment you know:

- a definitional choice behind a shared number (what counts as a customer, which date ends a subscription) whose readings differ materially;
- a change to anything something else depends on;
- an irreversible or shared act: making a table or dashboard visible where people read, publishing to the Library or as canonical, overwriting or dropping a table people read, sending to real recipients, showing personal data row by row, changing a setting, force-pushing or importing over work in git sync.

**Decide and show** reversible technical choices (a key among candidates, CTE or table, full or incremental, a name where no convention exists, a display): take the recommended option from the evidence, record it as a decided line, list it in the next hand-back.

**Never ask** what the instance, profiling, existing definitions, or the domain note can answer. Propose from the data and ask for corrections ("these 7 statuses map to active, cancelled, trial; anything wrong?").

**Materiality.** When a decision's column traces to a headline, compute both readings on the slice and record both figures, measured against the driving measure at that layer (row count in staging, the amount's sum in a model, the headline once it exists). Material means over 5 percent of that measure and over an absolute floor (default 10 rows, or the smallest unit the audience reads); both defaults are listed in the proposal-point memo. A decision no headline depends on is decided on the recommended reading with no second reading. An unmeasured decision on a traced column is open, not decided.

## The planned stops

1. **Intake**, before profiling (explore §2).
2. **The proposal point**, before anything is written where people read (`SKILL.md`, Invariants): explore §8 for a pipeline, a one-model proposal for a model added later (build), extract §7 for a migration, semantic §3 for definitions and metadata, reconcile §3 for a comparison, change §2 or §3.6 for a change. Its list is printed, then asked about.
3. **Go-live approval** (build §7), before a table goes final where people read or work is exported to a branch; at every layer boundary, never skipped, and the next layer never opens in the same response.

Each planned stop writes its line in the state file's `## Stops` when it returns, never before: `intake: answered <date> (<who>)`, `proposal <slice>: answered <date> (<who>)`, `go-live <layer>: answered <date> (<who>)`; a headless run writes `unanswered (headless)` instead. A skipped stop is then visible as a missing line.

Stops that come with the fact, in the response that produced it: a rule found mid-build that moves a headline past materiality; a gate failure whose fix needs a business rule (a build bug is fixed and rerun instead); an empty table on a question's path; a write that landed outside the output schema (stop before any other tool call, even investigating); a permission or missing-schema error; a stale loader. "I will report it in the hand-back" is not a stop: by then the work that depended on it is done.

## How a stop works

A stop is one `AskUserQuestion`, and nothing runs after it in that response.

- Question text: the measured fact in one plain sentence, then the decision as a question.
- Two to four options; each label names the option, each description its tradeoff with the figure it moves ("churn a month earlier for 209 accounts; August churn 41 becomes 48"). Recommendation first, its label ending `(Recommended)`. Up to four questions per call; batch what is known at once.
- Never also print the question as a text block. The exception is a list too long for the question (the inventory, a decision memo): print it as a numbered list right before the call, one line per item, and refer to it by number ("Accept 1–6 as listed?"). Batch options (accept all as listed / show the ones that move the headline most / review each) appear only beneath a printed list.
- Before anything waits for a hand-back, ask: when did I first know this? If it could have been a two-option question then, it belonged in a stop then.
- The stop's context and options are condensed into the decision's line in the state file, not repeated in chat.

## Modes

- Default: the rules above.
- "Check with me on everything": every decision stops, reversible ones too; also adopt it when the user corrects two decisions in a row.
- "Just go": definitional decisions proceed on defaults as open decisions, every number they shape is Draft and listed first in the hand-back; irreversible acts still stop.
- Headless (`AskUserQuestion` unavailable, as in `claude -p`): like just go, ending at the first irreversible act with what is pending listed; a decision with no default leaves its number unbuilt.
- A dismissed or empty answer in an interactive session is not a yes: ask once more, shorter, then halt with what is pending. Never proceed on defaults because a question went unanswered.

Never ask how hands-on the user wants to be; take the mode they state.

## Decisions

One line per decision, keyed by a short kebab-case name of the rule (`churn-date`, `grace-window`), using the domain note's owner-question keys when one fires; never numbered ids.

```
open <yyyy-mm-dd> [<key>]: <question>; default <what you build on>; readings: <A: figure> vs <B: figure>
decided <yyyy-mm-dd> [<key>] (<who>): <rule as implemented>; readings: <…>
```

- The ledger lives in the state file and in the domain Document's decisions section (created at the first proposal point, updated at every stop), so a session in another directory still finds it.
- An open decision's effect is visible where readers look: a plain sentence in the `caveats` of the table it shapes ("Churn is dated by end of paid service until the revenue owner confirms; the cancellation date would move August churn from 41 to 48") and `Draft.` opening every definition it shapes.
- An open decision proceeds on its default and blocks Library publishing and the Reconciled label for what it shapes. More than three open decisions on one headline is itself a stop.
- Never resolve a decision by inference from the data; never write a default as confirmed; never re-ask an answered one.
- When the state file and the domain Document disagree on a decision, the Document wins: it lives on the instance, like every other fact. Correct the state file and name the drift in the hand-back.

## Trust labels

Beside every headline in hand-backs and in the dashboard's text card: `Draft` (an open decision shapes it, or it is checked only structurally), `Self-consistent` (checks and tests pass; the owner accepted it with no external reference), `Reconciled to <reference>, <period>, within <tolerance>`. In answers: `Official` (a metric or measure produced it) or `Ad hoc`. The verified badge, set by the user in the UI (the CLI cannot), is the certification.

## Personal data, permissions, empty tables

- Names, emails, phones, addresses, and payment details stay aggregated or masked. Row-level display needs the user's yes through `AskUserQuestion`, for this session only. Mark such fields `data_sensitivity`; count them in profiling, never list them.
- A permission error on a read: stop; never substitute a similarly named readable table. Say what was denied and the likely cause (wrong login, wrong copy in another schema, a name slightly off); offer to search for a readable table and present any match as a question. Grants and profiles are the user's call. A denied write to the output schema is a stop for the admin, never a reason to write elsewhere.
- An empty table on a named question's path is a stop naming the number it blocks; off every path it is listed and ignored. Loader bookkeeping tables and unpopulated nested-field child tables are listed as skipped.

## The hand-back

Every stage ends with one, in this order:

1. What you can now do, with a link for every object.
2. The headline numbers, each with its trust label.
3. What I decided for you: reversible choices, one line each; tables, keys, tests, and checks only where they changed a number.
4. What I need from you: through `AskUserQuestion`, limited to what could not have been asked earlier (a person, another system, a file). Anything that sat unasked across more than one step is reported with the step at which it was known.
5. What comes next, and roughly how long.

A job is done with three things: the recap in this shape; the domain Document (`playbooks/deliver.md`); and a five-line walkthrough for whoever maintains it. What the CLI cannot write (the verified badge, glossary terms, AI-context notes) is listed as exact entries for the user to paste in the UI.

## Files and credentials

Working files go in `./.scratch` (`mkdir -p` first, kept out of git per `references/state.md`), never a system temp directory; they are not a deliverable. Never paste credentials or warehouse passwords into chat; the user runs any storing command.

- Never read files under `~/.rde`, and never edit `PATH` or shell files.
- Never ask the user for a password or an API key, and never handle one.
- Never run `rde credentials`. When the user needs the UI login for the installer's Metabase, tell them to run `rde credentials` in their own terminal.
- Logging in and repairing a login follow `SKILL.md`, Which Metabase (login rules): the user's yes before any installer command beyond `rde status --json` and `rde doctor --json`.
