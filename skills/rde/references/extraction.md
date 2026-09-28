# Extraction and the gap report

The method behind `playbooks/extract.md`.

## Two paths

- **Mirror what exists**: read each existing definition (`mb card get <id> --fields name,description,dataset_query`, transform descriptions, the company's project files) into the questions table and continue in `playbooks/semantic.md`; no tagging, no report. Two existing definitions of one number reconcile under `source_parity` and become one.
- **Migrate**: rules live in code or documents the instance does not hold, a number is disputed, or nobody can point at the rules. Extract below and stop on the gap report before any SQL.

## Extraction rules

- Write for a reader who sees only the raw tables and your document; never "see the code".
- From code read each literal, narrowing filter, enum with dead values, classification with tiebreakers, event-time vs load-time and timezone handling, and join with keys, cardinality, fan-out, row loss.
- Tag every claim `PROVEN` (read directly from code, schema, or an explicit statement), `INFERRED`, or `UNKNOWN`; cite file and line, or page and last-edited date, on every non-obvious claim; open the document by stating the scheme.
- Date everything; tag each rule current, deprecated, planned, or unclear; quote verbatim where a document admits a process is not followed; never implement a planned rule as live.
- Contradictions side by side (both positions, citations, dates, which is newer); record, do not resolve: the newer or current one is the default, as an open decision.
- A hardcoded-value inventory, `value | meaning | where` (thresholds, cutoffs, allow and deny lists, retention windows, null defaults), identifiers preserved exactly; a join map with keys, cardinality, fan-out and drop warnings, unenforced keys noted.
- Unreachable sources: record what surrounding text says they hold, ask for an export, carry the gap as `UNKNOWN`.
- Crawl stop: open a page or file only when its title, index entry, or a page already read names a table, column, or number the build needs; stop when a pass over the remaining index names none. A database table or column no document mentions is a defect to list.
- Documented exclusions and incidents join the exclusion rule list (`references/modeling.md`, Exclusions), each identifier verified in the data. A worked example in an artifact (a spreadsheet row, a code test, a figure with its inputs) becomes a test case for the model that will own the rule.

## The gap report

The gate between profiling and SQL on a migration; the deliverable, kept local until ratified (`playbooks/extract.md` §7), then filed as a document in the domain's collection or as Markdown where the user keeps specifications.

| Verdict | Meaning |
| --- | --- |
| `EXACT` | reproducible faithfully from the source as defined |
| `APPROX` | buildable with a stated deviation: partial data, an undocumented choice, a proxy |
| `NONE` | not buildable from this source; say what is missing |

- Open with a verdict matrix, one row per requested number; headline counts are recounted from it whenever a row changes, never remembered.
- Per number: the documented definition with citation; the verified source as exact `schema.table.column` names with match rates; the deviation or gap; the grain with fan-out warning and how to count; blockers as decision keys.
- Dimension availability as its own section (dimension, verdict, source, coverage), flagging a dimension at another grain, one needing an undocumented collapse map, one covering part of the population, one unsourced.
- Carry forward only contradictions and open questions touching what must be built, each marked `blocks` or `degrades`. Close with the `NONE` set and what unblocks each (missing input vs missing effort), and the open decisions as choices.
- Verify every cited identifier against the live catalog before shipping.

Shape only:

```
| number                | verdict | source (dated, tag)                | live data                             | gap                     |
| MRR                   | EXACT   | billing/mrr.sql, 2026-03, PROVEN   | invoice line amounts present, 0% null | none                    |
| Net revenue retention | APPROX  | wiki "Metrics", 2025-11, PROVEN    | no plan history before 2026-01        | history horizon 2026-01 |
| Activation rate       | NONE    | analyst chat, undated, INFERRED    | no signup event in the stream         | needs a definition      |
Summary: 1 exact, 1 approximate, 1 none; 4 contradictions; 2 cited columns absent from the catalog.
```

## The specification

The ratified rules plus the gap report, one document with labelled sections: rules (definitions, taxonomy, states, checks, definition of done, each tagged with provenance: profiled, user-stated, lifted from code, defaulted; instance ids cited from the state file, never restated), build notes (order, stops, validation, stop conditions; where notes and rules disagree, rules win), the completeness aimed at, and an escape hatch for an unanticipated rule (model, rule verbatim, why). Another business's filled specification is never a source of defaults. Matching the original artifact's output proves translation fidelity only (`source_parity`).
