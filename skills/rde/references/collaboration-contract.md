# Collaboration contract

Read once per job; its outputs (owner, mode, decisions, the personal-data answer) live in STATE.md ([state.md](state.md)).

## Mode

Never ask who owns definitions: the person in the session does, unless they name someone else, and the decision memo carries the definition questions themselves. Default to Balanced. Move to Check with me when the user corrects two decisions in a row or asks to see everything; move to Just go when they say so. Record both in STATE.md; never re-ask.

## Decide and show, or stop

A decision is reversible (a named constant, a labelled default, a re-run) or irreversible. Irreversible always stops with a `[CHECKPOINT]`, in every mode: publishing a number as canonical or to an audience, showing personal data, overwriting or dropping a table people read, changing a definition already handed back. A reversible decision whose two readings differ by more than the materiality threshold (default 5 percent, against the denominator below, to confirm) also stops. In Balanced and Just go, every other reversible decision is taken on the recommended option, recorded, and batched into the next hand-back; the user corrects by exception. In Check with me, every decision stops.

```
[DECIDED, reversible] <rule as implemented>. Evidence: <numbers>. Affects: <models, metrics>. To change: reply with the alternative; it is a re-run.
```

Routine reversible decisions: date basis, inclusion filter, derived classification column, grain, key among several candidates, unit and currency, line detail source, convention default. Decide each from the profile with the smallest defensible reading. When the inventory traces the decision's column to a headline number, run both readings on the slice before choosing and record both figures in the Decisions row; express the gap against the driving measure at the layer where the decision is taken — row count in staging, the sum of the amount column in a fact, the headline number itself once one exists — and stop when it clears the threshold. A decision no headline number depends on is `[DECIDED, reversible]` on the recommended reading, with no second reading taken. An unmeasured decision on a traced column is not decided; it is open. Business rules are the user's to decide; conventions are the company's to keep ([layering-and-naming.md](layering-and-naming.md)).

A checkpoint is raised in the response that produced the fact. "I will report this in the hand-back" is not a checkpoint — by the hand-back, the work that depended on it is done. A write that lands outside `out_schema` stops before the next tool call of any kind, including before investigating it.

## The checkpoint

A checkpoint is one `AskUserQuestion`, and nothing else runs in that response. Never print it as a text or code block as well: the question is the only place the user sees it. The decision memo below is the exception: it is printed in full before the gate that asks about it. Draft a checkpoint from these fields:

```
[CHECKPOINT]
Decision: <one sentence naming what has to be decided>
Context: <what you measured: row counts, sample values, column names, distributions, match rates>
Example: <one record the options treat differently: its id, dates, and amounts, and what each option makes of it>
Options:
  A. <option and its tradeoff>
  B. <option and its tradeoff>
Recommendation: <preferred option and a one-sentence rationale>
```

Then map them onto the tool call. The question text opens with the example, then the context in one plain sentence, then the decision as a question about that record. Each option's label says what happens to the record in the user's words, never the term for the rule ("Count it as $49 a month", not "Interval-based normalisation"), and its description gives the tradeoff with the measured figure it moves. The recommendation comes first, with `(Recommended)` on its label. `Context` carries measured numbers: profile first, then ask. Two or more options, one recommendation. The full block goes in the decision's STATE.md Decisions row (`decision`, `readings`, status `open`), not in chat. A block printed in chat with no tool call behind it is not a checkpoint. When a stop would carry more than three decisions, offer the batch rather than the list — accept all defaults as listed / show me the ones that move the headline number most / review each one — because over-asking ends with the user reading none of it.

The example is a real row from the profile: `sub_4471, cancelled 30 July, paid through 31 August`. When no single row shows the choice (a test fixture, a job schedule, a threshold), give a small made-up case and say it is one: "for example, a customer who pays in January and March but not February". Before asking, test the draft: could the user answer it without asking what a word means? A question led by a term ("fixture usage", "payment methods", "cadence") comes back as "tell me more" and costs a second round; one led by a record ("this monthly renewal was counted as annual") is answered at once. A "tell me more" means the question failed: the re-ask leads with a record, not a longer definition.

## The decision memo

Before building, list the open decisions once, grouped by who can answer, each as: the question in one sentence, shown on one record it changes, the default you will use and where it came from, what changes if it is wrong. Ask for changes only. Record each as a Decisions row. Print the memo in chat as a numbered list, one line per decision, in the response that asks item 3 of the pre-create gate in `SKILL.md`, immediately before the question; the question and its batch options refer to it by number. A batch option (accept all defaults / show the ones that move the headline most / review each) is only offered beneath a printed list. The first slice begins on whichever defaults the gate returns unchanged — never before it returns. An answered decision is never re-asked. An unanswered one proceeds as `PROVISIONAL`: named in the metric description and on the dashboard, and it blocks Library publishing and the `Reconciled` label. Never resolve a decision by inference from the data; never write a default as confirmed. More than three rows at `PROVISIONAL` at once is itself a stop: ask before building further, batched per the checkpoint rule. Six unanswered decisions shaping a number reported as reconciled is the failure this prevents.

Finished example, one memo line: `3. Invoice in_8812 renews monthly at $49. Default: $49 a month, from its price record. If it were read as annual, it would count $588 and August MRR would rise 12%.`

## Zero-row tables and personal data

An empty table on the path of a named question is a `[CHECKPOINT]` naming the number it blocks; an empty table off that path is listed and ignored. Exempt: the loader's bookkeeping tables and child tables for a nested field no parent row populated; list as skipped.

Personal data (names, emails, phones, addresses, payment details): ask once per job whether this audience may see it, or it is masked or reduced to counts (the default to confirm); record the answer; apply it everywhere.

## Plain language

Lead with the point; SQL and JSON stay on request, never in chat to ask or answer. Mirror the user's vocabulary and terseness. For a non-database reader: "one row per customer", not "the grain is customer"; avoid grain, fact table, dimension table, denormalize, surrogate key, materialize; Metabase terms (Question, Model, Segment, Metric, Transform, Library) are fine. Every question carries its context immediately before it: what you found, why it matters, then the question. Never name a probe or helper table the user never saw.

## The hand-back

Five parts, in this order, in every Reply:

1. What you can now do, with a browser link.
2. The headline numbers, each with its trust label.
3. What I decided for you: reversible, one line each; tables, keys, tests, and checks only here, only when they changed a number.
4. **What I need from you** — carried by `AskUserQuestion`, not prose, and limited to items that could not have been asked earlier: they need a person, another system, or a file you must produce. Two or three, recommendation first. What to build next is never one of them: that is item 5.

   Test each item before it goes here: *when did I first know this?* If it could have been a two-option question at that moment, it belonged in a checkpoint then, and listing it here is the failure the hand-back exists to surface. Any item that sat unasked across more than one playbook step is reported with the step at which it was known.
5. What comes next and roughly how long, as a statement, never a question: the next STATE.md Questions row in the order the user gave, which the user redirects by exception.

## Trust labels and restatement

The first line of every headline metric's description and every KPI card's description is its trust label: `Reconciled to <reference> on <date>, within <tolerance>` / `Self-consistent only, no external reference` / `Draft, provisional decisions: D3, D7`. The same label sits beside the number in every hand-back. A stakeholder's done is `Reconciled` or an explicit acceptance of `Self-consistent only`.

When a shipped number was wrong: fix the definition in place (`update` on the same id; a segment or measure carries a `revision_message` naming the cause, a metric's description gains a dated change line), add a timeline event with direction and size, a dated text card on the dashboard for one period (old figure, new figure, cause, which past periods moved), and say the same in the hand-back. Never restate silently.

## Final deliverables

Done needs three things: a recap in the hand-back shape with a browser link, never only an `mb` command; a document in the business collection titled `How to use <area> numbers` (`mb skills path document`) listing each metric and segment with its meaning and trust label, who owns definitions, how to ask a new question, and what to do when a number looks wrong; and a five-line walkthrough for the maintainer.

## Working files and credentials

Working files go in `./.scratch` (`mkdir -p ./.scratch` first), never a system temp directory; they are not a deliverable. Never paste credentials, tokens, or warehouse passwords into chat; when one must be stored, the user runs the storing command.
