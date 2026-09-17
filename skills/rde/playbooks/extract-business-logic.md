# Extract business logic from existing artifacts

Applies: the rules exist in code, documents, another tool's project, a spreadsheet, or in definitions already in the instance. Produces either a mirror of the existing definitions (the light path) or a tagged reference plus a gap report per requested number (the migration path). No SQL is written.

Checklist (copy into TodoWrite; a resumed session reads the todo list and STATE.md first): `1 path` `2 inventory` `3.<artifact> read` `4 tag` `5 live check` `6 gap report` `7 ratify` `reply`.

Read first: [`extraction-and-gap-report.md`](../references/extraction-and-gap-report.md), [`profiling-catalog.md`](../references/profiling-catalog.md), and the domain file STATE.md names.

## Commands you will run

Every line also takes `--profile $PROFILE --json`; `q()` is sourced from `./.scratch/probe.sh`.

```bash
mb search "<number or term>" --models metric,measure,segment,card,dataset,transform --db-id $DB
mb card get <id> --fields name,description,dataset_query          # a definition people already use
mb transform list --fields id,name,description,target             # the five facts, if anyone wrote them
mb table list --db-id $DB --fields id,name,schema                 # every cited table exists here, or it does not
mb table get <table-id> --include fields
q "SELECT <cited column>, count(*) AS n FROM <schema.table> GROUP BY 1 ORDER BY 2 DESC LIMIT 50"   # does the cited value still occur
```

## 1. Pick the path

"Reuse what we have": read the definitions in use (`card get`, transform descriptions, the company's own project files), write each into STATE.md Questions with its home table and filter, tag each per `extraction-and-gap-report.md`, and continue in [`build-semantic-layer.md`](build-semantic-layer.md); nothing below runs. A migration, a disputed number, or rules nobody can point at: steps 2 to 7.

## 2. Inventory the artifacts

Scope is what you can read locally or fetch; an unreachable document space is exported by the user on request and recorded per the unreachable-sources rule. Crawl stop rule: read a page only when it names a table, a column, or a number the build needs; stop when a level of links adds none. `[DECIDED, reversible]`: the scope, written down.

## 3. Read

Apply the code reading list and the dating rules in `extraction-and-gap-report.md` to every artifact in scope.

## 4. Tag every claim

Confidence tags, citation rule, contradiction rule, the hardcoded-value inventory, and the join map per `extraction-and-gap-report.md`; the document opens by stating the scheme. No untagged claim; no proven claim without a citation.

## 5. Check against live data

Every cited table and column exists in the catalog; the values behind each rule are profiled with `profiling-catalog.md`. Verdict-changing findings: a filter on a value that no longer occurs; a mapping covering only inactive keys; a documented uniqueness rule the data violates. On a fact about the data, the data wins; the divergence is a finding.

## 6. Build the gap report

One record per requested number and dimension in the format in `extraction-and-gap-report.md`, opening with the verdict matrix; the report is the deliverable. Specification and environment values are one document; the ids live in STATE.md.

## 7. Ratify

Present the report; open questions as one decision memo per the contract, grouped by owner. Reversible items proceed on the default; an irreversible one is a `[CHECKPOINT]`. Every item is a STATE.md Decisions row; an unratified assumption enters the build as an open row, never as a fact. The ratified reference plus the report is the plan [`build-clean-tables.md`](build-clean-tables.md) expects; a worked example found in an artifact (a spreadsheet row, a test in the code, a figure in a document with its inputs) is carried over as a transform-test case for the model that will own the rule ([`transform-tests.md`](../references/transform-tests.md)); validation against the original artifact's own output measures parity only (`reconciliation.md`).

Finished example, the verdict matrix:

```
| number                | verdict | source (dated, tag)                        | live data                                   | gap                       |
| MRR                   | EXACT   | billing_sql/mrr.sql, 2026-03, PROVEN       | invoice_line amounts present, 0.0% null     | none                      |
| Net revenue retention | APPROX  | wiki "Metrics", 2025-11, DOCUMENTED        | no plan history before 2026-01              | history horizon 2026-01   |
| Activation rate       | NONE    | analyst chat, undated, INFERRED            | events carry no signup event                | needs a definition (D12)  |
Summary: 1 exact, 1 approximate, 1 none; 4 contradictions recorded; 2 cited columns absent from the catalog.
```

## Done when

Every artifact in scope is read or marked unreachable; every claim is tagged; every cited identifier was checked live; the gap report's counts match a recount of the matrix; the open questions are in STATE.md with owners.

## Reply

The five-part hand-back in `collaboration-contract.md`; under part three: the verdict counts and one sentence on why, the contradictions with both positions and dates, where the data disagreed with the documents.
