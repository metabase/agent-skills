# Extraction and gap report

Read by `extract-business-logic`, and by `plan-the-build` for the files people bring: lifting rules from code, documents, and existing definitions, and the gap report it delivers.

## Two paths

- Reuse what we have: the company wants its existing definitions mirrored, not migrated. Read each existing definition (`mb card get <id> --fields name,dataset_query --json`, and the company's tool); write every definition as a row in STATE.md's Questions table ([state.md](state.md)): home table, time column, definitional filter, breakouts. No claim tagging, no gap report. Two existing definitions of one number reconcile under `source_parity` ([reconciliation.md](reconciliation.md)) and become one.
- Migration: the rules live in code or documents the instance does not hold. Run the extraction below and stop on the gap report before any SQL.

## Reading what people bring

Classify each input once, then read it with the extraction rules below; the method never branches on the input type, and arriving with nothing is the same method with more profiling. An input arrives as a path, a file dropped into chat, through a connector to a document space, or as an export the user makes on request; a file holding personal data is read where it is and never copied into `plans/`.

| Input | Read | Settles | Proposes only |
| --- | --- | --- | --- |
| dbt project, or `target/manifest.json` with `catalog.json` | each model's `compiled_code`, `depends_on` walked up from the outputs in use, tests, `exposures`, `seeds/`, `snapshots/` | grain and keys from `unique` and `not_null` tests, joins from `relationships`, what is in use from `exposures` | every definitional filter, unless the plan translates as it is |
| LookML | views (`sql_table_name`, dimensions, measures), explores (joins and their `relationship`), derived tables, `access_filter` | join paths and their cardinality | measures, as measure and metric candidates |
| Saved SQL, another BI tool's calculated fields | each query and field behind a number in use | the predicates that number applies | its definition |
| Definitions documents (Notion, Confluence, Google Docs) | per the crawl stop rule | nothing alone | definitions, exclusions, owners' wording |
| Mapping sheets as CSV, JSON, or a spreadsheet | every row, identifiers exactly | the mapping as people maintain it, once its keys are checked live | — |
| A baseline export | grain, keys, periods covered | the reference ([reconciliation.md](reconciliation.md)) | — |
| A previous plan | every entry | decided entries, with who and when | — |

What an input settles is written into the plan with its source and ratified at the gate, not asked; what it proposes is an open entry with that default. When two inputs disagree and nobody is asked: code that runs in production and that live data agrees with settles mechanics (keys, joins, grain), and settles definitions too when the plan translates as it is; otherwise code proposes them. Documents and prose propose. Profiling lists the options and never decides. On a fact about the data, the data wins. A `snapshots/` folder or a history table is said loudly: that history cannot be recomputed from current state ([entities-and-time.md](entities-and-time.md)).

## Extraction rules

- Write for a reader who sees only the raw tables and your document; never "see the code".
- Read from code: each literal, narrowing filter, enum with dead values, derived classification with tiebreakers, timezone and event-time versus load-time detail, join with keys, cardinality, and fan-out or row loss.
- Tag every claim `PROVEN` (read directly from code, schema, or an explicit statement), `INFERRED`, or `UNKNOWN`; cite file and line, or page and last-edited date, on every non-obvious claim.
- Date everything: file timestamp and dates in the body. Tag every rule current, deprecated, planned, or unclear; quote verbatim where a document admits a process is not followed. Never implement a planned rule as live.
- Contradictions side by side: both positions, both citations, both dates, which is newer. Record, do not resolve: prefer the source marked current or edited more recently, carried as a named constant in `cfg_<domain>` ([layering-and-naming.md](layering-and-naming.md)) with its Decisions id.
- Hardcoded-value inventory as `value | meaning | where`: thresholds, cutoffs, allowlists, denylists, retention windows, defaults on null. Preserve identifiers exactly.
- Join map: key columns, cardinality per path, explicit fan-out and drop warnings, a note wherever keys are unenforced.
- Unreachable sources: record what surrounding text says they hold, ask the user to export them, carry the gap as `UNKNOWN`.
- Crawl stop rule: open a page or file only when its title, its index entry, or a page already read names a table, a column, or a number the build needs; stop when one pass over the remaining index names none. A table or column in the database absent from the document is a defect to list.
- Documented exclusions and known incidents land as `dim_exclusion_rule` rows ([state.md](state.md)) the models left-join, so an adjusted figure sits beside the reported one; verify each documented identifier against the data first.

## The gap report

The gate between profiling and any SQL on the migration path; produce it, then stop for review. Under a build plan, the report is the plan's Migration section and the review is the plan's gate.

| Verdict | Meaning |
| --- | --- |
| `EXACT` | Reproducible faithfully from the source as defined |
| `APPROX` | Buildable with a stated deviation: partial data, an undocumented definitional choice, a proxy |
| `NONE` | Not buildable from this source; state what is missing |

- Open with a verdict matrix, one row per metric; the headline counts verdicts from the matrix, never from memory, and is recounted whenever a row changes.
- Per metric, five fields: documented definition with citation; verified source as exact `schema.table.column` names checked to exist, with match rates; deviation or what is missing; grain, with fan-out warning and how to count; blockers as Decisions ids.
- Dimension availability is its own mandatory section: dimension, verdict, verified source, coverage; flag a dimension at a different grain than the fact, one needing an undocumented collapse map, one covering part of the population, one unsourced.
- Carry forward only contradictions and open questions touching what you must build; mark each `blocks` (cannot be exact) or `degrades` (buildable with a caveat).
- Close with the `NONE` set and what unblocks each (missing input versus missing effort), and the open decisions as choices for the reviewer.
- Verify every cited identifier against the live catalogue before shipping; the report is the deliverable.

## The specification

Under a build plan, the plan is this document ([plan-file.md](plan-file.md)). Otherwise one document with labelled sections, never a second file:

- Rules: definitions, taxonomy, states, checks, definition of done, each non-obvious rule tagged with its provenance (profiled, user-stated, lifted from code, defaulted). Environment values live in STATE.md and are cited, never restated.
- Build notes: build order, checkpoints, validation procedure, stop conditions, citing rule sections by number. Where notes and rules disagree, the rules win.
- Declare the completeness level aimed at.
- Escape hatch for an unanticipated rule: model, body verbatim, `why`.
- A filled example specification is never a source of defaults for another business: reuse the schema, slot list, and checks, never the values.
