# Collaboration contract

Read once per job; its outputs (owner, mode, decisions, the personal-data answer) live in STATE.md ([state.md](state.md)).

## Owner, then mode

Ask once, near the start: "Who signs off on what a number means (what counts as a customer, a donor, revenue)? I will batch definition questions to them and decide the rest, showing you what I decided." Default to Balanced. Move to Check with me when the user corrects two decisions in a row or asks to see everything; move to Just go when they say so. Record both in STATE.md; never re-ask.

## Decide and show, or stop

A decision is reversible (a named constant, a labelled default, a re-run) or irreversible. Irreversible always stops with a `[CHECKPOINT]`, in every mode: publishing a number as canonical or to an audience, showing personal data, overwriting or dropping a table people read, changing a definition already handed back. A reversible decision whose two readings differ by more than the materiality threshold (default 5 percent of the headline number, to confirm) also stops. In Balanced and Just go, every other reversible decision is taken on the recommended option, recorded, and batched into the next hand-back; the user corrects by exception. In Check with me, every decision stops.

```
[DECIDED, reversible] <rule as implemented>. Evidence: <numbers>. Affects: <models, metrics>. To change: reply with the alternative; it is a re-run.
```

Routine reversible decisions: date basis, inclusion filter, derived classification column, grain, key among several candidates, unit and currency, line detail source, convention default. Decide each from the profile with the smallest defensible reading, the alternative reading's effect on the headline number measured and shown beside it. Business rules are the user's to decide; conventions are the company's to keep ([layering-and-naming.md](layering-and-naming.md)).

## The checkpoint block

Use literally; never paraphrase into prose.

```
[CHECKPOINT]
Decision: <one sentence naming what has to be decided>
Context: <what you measured: row counts, sample values, column names, distributions, match rates>
Options:
  A. <option and its tradeoff>
  B. <option and its tradeoff>
Recommendation: <preferred option and a one-sentence rationale>
Action required: reply with a letter or give alternate instructions before this work continues.
```

`Context` carries measured numbers: profile first, then ask. Two or more options, one recommendation. Wait for the reply.

## The decision memo

Before building, list the open decisions once, grouped by who can answer, each as: the question in one sentence, the default you will use and where it came from, what changes if it is wrong. Ask for changes only. Record each as a Decisions row; build the first slice on the defaults while waiting. An answered decision is never re-asked. An unanswered one proceeds as `PROVISIONAL`: named in the metric description and on the dashboard, and it blocks Library publishing and the `Reconciled` label. Never resolve a decision by inference from the data; never write a default as confirmed.

## Zero-row tables and personal data

An empty table on the path of a named question is a `[CHECKPOINT]` naming the number it blocks; an empty table off that path is listed and ignored. Exempt: the loader's bookkeeping tables and child tables for a nested field no parent row populated; list as skipped.

Personal data (names, emails, phones, addresses, payment details): ask once per job whether this audience may see it, or it is masked or reduced to counts (the default to confirm); record the answer; apply it everywhere.

## Plain language

Lead with the point; SQL and JSON stay on request, never in chat to ask or answer. Mirror the user's vocabulary and terseness. For a non-database reader: "one row per customer", not "the grain is customer"; avoid grain, fact table, dimension table, denormalize, surrogate key, materialize; Metabase terms (Question, Model, Segment, Metric, Transform, Library) are fine. Every question carries its context immediately before it: what you found, why it matters, then the question. Never name a probe or helper table the user never saw.

## The hand-back

Five parts, in this order, in every Reply:

1. What you can now do, with a browser link.
2. The headline numbers, each with its trust label.
3. What I decided for you: reversible, one line each; tables, keys, and checks only here, only when they changed a number.
4. What I need from you, batched by owner.
5. What comes next and roughly how long.

## Trust labels and restatement

The first line of every headline metric's description and every KPI card's description is its trust label: `Reconciled to <reference> on <date>, within <tolerance>` / `Self-consistent only, no external reference` / `Draft, provisional decisions: D3, D7`. The same label sits beside the number in every hand-back. A stakeholder's done is `Reconciled` or an explicit acceptance of `Self-consistent only`.

When a shipped number was wrong: fix the definition in place (`update` on the same id; a segment or measure carries a `revision_message` naming the cause, a metric's description gains a dated change line), add a timeline event with direction and size, a dated text card on the dashboard for one period (old figure, new figure, cause, which past periods moved), and say the same in the hand-back. Never restate silently.

## Final deliverables

Done needs three things: a recap in the hand-back shape with a browser link, never only an `mb` command; a document in the business collection titled `How to use <area> numbers` (`mb skills path document`) listing each metric and segment with its meaning and trust label, who owns definitions, how to ask a new question, and what to do when a number looks wrong; and a five-line walkthrough for the maintainer.

## Working files and credentials

Working files go in `./.scratch` (`mkdir -p ./.scratch` first), never a system temp directory; they are not a deliverable. Never paste credentials, tokens, or warehouse passwords into chat; when one must be stored, the user runs the storing command.
