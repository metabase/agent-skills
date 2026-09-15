# Build the semantic layer

Applies once the final-layer tables are deployed with rows; produces field metadata, models, measures, segments, and metrics with a description each, a question-to-build map, and the verified canonical set. Missing tables: [`build-clean-tables.md`](build-clean-tables.md) first.

Read first: [`semantic-layer-design.md`](../references/semantic-layer-design.md), [`collaboration-contract.md`](../references/collaboration-contract.md), `mb skills get semantic-layer`, `mb skills get metadata`, and `mb skills get mbql`.

## 1. Discover what exists

Run the discovery commands in `semantic-layer-design.md`. Record existing definitions, naming, and filing; match them; reuse, never duplicate. Confirm each planned object type is supported (`mb <command> --help --json` reports the minimum server version); without the Library (no `library` feature, or a server below v59) the canonical set is the described objects in the agreed collection.

Confirm the defining tables have rows: `SELECT count(*)` per table through `mb query`, or the `rows:` line in the build ledger. Check: every planned object type is supported or its substitute named; every defining table is present. Never compensate for a missing table with row-level logic in a metric.

## 2. Field metadata on the defining tables

Verify the pass from `build-clean-tables.md` step 7 happened on every defining table and complete the gaps to the completeness bar in `semantic-layer-design.md`, mechanics per `mb skills get metadata`. Check: the bar is met; every declared foreign key resolves.

## 3. Collect the questions

Ask for the questions people ask: recurring reports, weekly numbers, what nobody can answer. Without one, infer it from the saved questions that repeat, mined per `semantic-layer-design.md`. Check: a written question list precedes any definition.

## 4. Decompose each question

Split each per `semantic-layer-design.md` into the number measured, the rows it is measured over, and the breakout columns; map in `./.scratch`, one row per question: metric, segments, dimensions, defining table, exists or to build. Row-level logic belongs in a transform: a question spanning two tables widens the table (single-table reach, `semantic-layer-design.md`). Two stakeholders defining one number differently is a checkpoint (block in `collaboration-contract.md`), not two objects.

Check: every question maps to objects on a single table each; no dimension is assumed to exist.

## 5. Define the objects

Order: models over the final-layer tables where a curated column set is wanted, then measures and segments, then metrics. Verbs and bodies: the bundled skills. File objects beside the company's existing ones.

Check: after each object, it appears on a question built directly on its table.

## 6. Describe every object

Name and one-line description in the user's words, per the naming rules in `semantic-layer-design.md`; where a definition encodes a judgment (excluded rows, measuring date, what it is net of), the description says so. Check: no object without a description, no description that restates the formula.

## 7. Verify every definition

Run each against the verification list in `semantic-layer-design.md`; proving a plausible number externally is [`validate-and-reconcile.md`](validate-and-reconcile.md). Check: every map row carries a run result.

## 8. Publish the canonical set

Present the tables and metrics you would publish; it is the user's call. With the Library: tables via `mb library publish --table-ids <ids> --json`; metrics reach it by being filed in its Metrics collection (`mb library get --json` reports the id; `mb card update <id> --body '{"collection_id":<id>}'`). Without it: file the canonical objects in the agreed collection and say the Library is unavailable. Check: nothing unratified or unverified is published or filed as canonical.

## Done when

Every check in steps 1 to 8 passes; every question in the map resolves to named objects or is recorded as unanswerable with the reason; the canonical set is published to the Library, or filed in the agreed collection where there is none, with the user's confirmation.

## Reply

What people can ask with one click that they could not before; the objects grouped by kind, each with its meaning, not its formula; the questions you could not answer and what is missing; one metric to open; the definitions that are still your proposal.
