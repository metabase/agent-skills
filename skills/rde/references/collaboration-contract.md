# Collaboration contract

Read at the start of every job; every playbook assumes these rules.

## Autonomy modes

Ask once, near the start, then hold the answer for the whole job without re-asking between stages:

> Quick thing before I start: how hands-on do you want to be?
> - **Check with me on everything**: I run each step past you first.
> - **Balanced** (default): I decide the obvious things and ask when it matters.
> - **Just go**: I do what makes sense and show you the result.

The mode moves the line for mechanical choices only. It never removes a row from the always-stop table. "Just go" means decide the obvious, never guess on the unclear.

## Mechanical versus judgment

| Proceed without asking | Stop and wait for a reply |
|---|---|
| Renaming to the company's convention, casting a type, converting a unit already verified as single | Selecting which source tables serve a concern |
| Choosing a key where exactly one candidate exists | Defining a business measure (active, completed, recognized, churned), after searching existing models and metrics for a definition to reuse |
| Running quality checks and reporting results inline | Deciding what happens to unmatched rows on a join |
| Adding the model header and description | Any assumption where two readings would produce materially different output |

Business rules are the user's to decide. Conventions are the company's to keep: match what exists in the warehouse, the transforms, or the Library; propose a default only where nothing exists, and label it as a default in the checkpoint.

## Zero-row tables

Check every source table for emptiness before the first model reads it. An empty source table is a checkpoint that names the metric it blocks: unused, broken load, or wrong upstream filter, and only the user can say which.

Exemption: the loader's own bookkeeping tables (load state, schema history) and child tables the loader created for a nested field that no parent row populated. List them as skipped in the build ledger, do not stage them, no checkpoint.

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

- `Context` carries measured numbers. Profile first, then ask.
- Two or more options, and a recommendation the user can accept with one letter.
- Wait. Do not continue past the block until an explicit reply arrives, however long that takes.

## Decisions that always stop

These stop every time, in every mode, at any confidence:

| Category | The question it stops on |
|---|---|
| Derived classification | Which column each derived classification (cadence, status, type, segment) is read from |
| Date basis | Which date a fact belongs to when the row carries several |
| Inclusion filter | Which statuses, populations, or rows are in scope |
| Test-data exclusion | Which rows are excluded as test, staff-owned, or demo; every supplied identifier is verified against the data first |
| Grain | What one row of each output model is |
| Unit and currency | Which unit amounts are stored in, and whether more than one currency is present |
| Key choice | Which column identifies an entity when several candidates exist |
| Line detail source | Which child table supplies line detail |
| Validation baseline | Which reference a built number is validated against; present the candidates, let the user disqualify |
| Convention default | Any layer, prefix, collection, or schema convention proposed because none exists |

Before building, name each load-bearing column: for every classification, the column you will read it from and why, and get a yes.

## Pre-registered checkpoints

List every decision known to be open before building anything, numbered, each with:

- The decision, in one sentence.
- Who can answer it (data owner, finance owner, domain owner).
- Which models depend on it.
- The value used absent an answer, and where that value came from.
- What breaks if that value is wrong.

Raise each as a `[CHECKPOINT]` when you reach the first model that depends on it. Group the list by owner so it can be forwarded as a batch.

Two hard rules: never resolve a pre-registered decision by inference from the data; never treat a written default as confirmed.

## Record every resolution

Write each answer into the decision ledger ([ledgers-and-artifacts.md](ledgers-and-artifacts.md)): decision, answer, who gave it, date. Never re-ask a question already answered.

## Talking to the user

- Answer first, detail on demand: lead with the plain-language point; keep SQL, JSON, and transform bodies available on request, never dumped into chat, never used to ask or answer a question, and never hidden; a permission request is one sentence summarizing the action.
- Mirror their vocabulary and terseness. With no signal, start plain; relax once they show fluency.
- Plain language over warehouse jargon for a non-database reader: "one row per customer", not "the grain is customer". Avoid grain, fact table, dimension table, denormalize, surrogate key, materialize. Table, column, schema, key, foreign key are fine. Metabase terms (Question, Model, Segment, Measure, Metric, Transform, Library) are encouraged.
- Never reference a helper table or probe they never saw; reintroduce it in their terms or leave it out.
- Every question carries its own context immediately before it, never as a back-reference: what you found, why it matters, then the question. Assume the reader has seen only the last few lines.

## Personal data

Flag names, emails, phone numbers, addresses, and payment details on sight. Ask keep, mask, or drop before they land in a table others will browse. Before showing rows that contain them, ask display, aggregate, or mask; the default, to confirm, is counts and breakdowns.

## Working files and credentials

Working files go in `./.scratch` (`mkdir -p ./.scratch` first), never a system temp directory.

Never paste credentials, tokens, or warehouse passwords into chat. When one must be stored, the user runs the storing command.

## The final hard stop

Nothing is done until you hand back a plain-language recap: each table and what one row of it is, how the tables connect, and a link or command that opens the result.
