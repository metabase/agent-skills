# Build the semantic layer

Applies when curated tables exist with rows (transform outputs, externally built tables, or models where those are the curated layer), including the light path from `playbooks/extract.md`. Produces the metadata pass, definitions with plain descriptions, a passing golden set, and the canonical set published or filed with owners. No curated tables in scope: offer `playbooks/build.md` first.

Read first: `references/semantic-layer.md`; the domain note's For answering before writing descriptions; `references/methods/retention-and-cohorts.md` for retention, cohorts, or activation.

Order: 1 read what exists, 2 questions table, 3 proposal point (stop), 4 metadata pass, 5 define, 6 describe, 7 verify, 8 publish or file (stop), hand-back.

## 1. Read what exists

`mb search "<each question's wording>" --models metric,measure,segment,dataset --db-id <db-id>`, then `mb card get <id> --fields name,description,dataset_query`: what exists is extended in place by id; existing names and definitions are the company's conventions and outrank a domain note. Two definitions of one number: reconcile first (`playbooks/reconcile.md`).

## 2. The questions table

One row per cluster in the state file (`references/semantic-layer.md`, The questions table). A flag or column the table lacks is a gap for build, never a metric filter.

## 3. The proposal point

Nothing is written before it returns. Print as a numbered list: each definition to create or extend (kind, name, home table, time column, one-line meaning), the date basis and flags each reads, the tables whose metadata you will write (and, on tables you did not build, which existing descriptions or settings you would change), and the open decisions with defaults. Then one `AskUserQuestion` about it by number, as in explore §8; answers become decided lines.

## 4. The metadata pass

The order in `references/semantic-layer.md` on the approved tables, entity tables first, one batch per table (`mb table update`, `mb field update`), before any metric. With two or more tables, fan out the reading: one subagent per table (`Agent`), given the table, its question rows, the decided date basis and flags, and the entity tables its breakouts reach, returning metadata bodies and metric specs as text; you apply them, entity tables first, so writes stay in one sequence.

## 5. Define

Per `references/semantic-layer.md` (Which kind, Bodies), metrics first, into `Definitions` until §8. Changing an existing one: `playbooks/change.md`. A number the definitions cannot express is a gap for build.

## 6. Describe

Per `references/semantic-layer.md`, Describe and name; list the glossary entries for the hand-back.

## 7. Verify

Per `references/semantic-layer.md`, Verify before handing back. A headline over tolerance goes to `playbooks/reconcile.md`.

## 8. Publish or file

The canonical set is a stop (`references/semantic-layer.md`, The Library and the canonical set). Once the golden set passes, ask the user to verify the canonical metrics in the UI.

## Learn from a correction

A correction lands in the layer, never only in chat: find where the wrong reading came from (a missing flag, an ambiguous name, a description silent on an exclusion), fix it through the right playbook, add the question as a golden case, re-run the set.

## Done when

Every question resolves to named objects or is marked unanswerable with the reason; the golden set passes; the canonical set is published or filed with owners; open decisions are named on what they shape. Hand-back: the objects by kind with their meaning, the golden pass rate, glossary entries and verified badges for the user to set, definitions still Draft and what they wait on.
