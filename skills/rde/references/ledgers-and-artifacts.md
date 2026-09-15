# Ledgers and artifacts

Read this at the start of any build spanning more than one working stretch, and whenever a decision is recorded rather than taken.

## The build ledger

`./.scratch/BUILD_LEDGER.md`, one block per model, appended at deploy:

```
## <model_name>
layer:      the company's layer vocabulary
grain:      one row per ...
key:        the unique column or column set
status:     DEPLOYED | FAILED | BLOCKED
rows:       <n>
checks:     OK | FAIL: <check and value>
decisions:  each checkpoint resolved here, with its answer
open:       unanswered items affecting this model
```

- `status: DEPLOYED` requires all four: filed per the company's convention or, outside Metabase, landed; runs without error; every check passes; rows above zero or an empty result the user confirmed.
- On resume, read the ledger first; `status: DEPLOYED` is the line the build resumes from. Never rebuild a `DEPLOYED` model unless a checkpoint answer invalidated it; say so when you do.
- Read `decisions` before raising a checkpoint (block in [collaboration-contract.md](collaboration-contract.md)); never re-ask.
- The assumption ledger is indexed by decision and outlives the build; the build ledger is indexed by model and drives it; a checkpoint decision goes in both.

## The assumption and decision ledger

One file, sectioned by kind:

| Section | Holds |
| --- | --- |
| A. Environment and provenance | Facts capping accuracy: truncated sources, an unreachable system, a stale loader |
| B. Contradiction resolutions | One per contradiction, with resolution and the named constant carrying it |
| C. Corrections to source documents | Where a document is wrong about the data; each awaits ratification |
| D. Money, time, definitions | Currency, units, timezone, period boundaries, load-bearing path choice |
| E. Requirements not built faithfully | From the gap report, by cause |
| F onward. Per-phase build decisions | Appended as each phase closes |

```
id:        C-RES-3
scope:     models and metrics affected
decision:  the rule as implemented, one sentence
constant:  the named constant carrying it, if any
evidence:  profiling result or document
status:    PROVISIONAL | DECIDED <date> (user) | NEEDS RATIFICATION
gates:     what stays blocked until answered
```

- Provisional and ratified entries share the file, distinguished by tag.
- Label heuristics inline: `is_placeholder_suspected = active AND past end_date AND no renewal [HEURISTIC]`.
- Standing caveats travel with the number: limitation, consequences, what lifts it. On partial data, still write logic that is right on complete data, and say so.
- Mark each verified item structural or semantic; close each phase with verified numbers and a not-done list.

Contradictions are recorded, not resolved: prefer the source marked current or edited more recently; carry the choice as a parameterised constant in one place, logged with its identifier, so flipping it is one line and a re-run; never implement anything tagged planned as live, and separate policy from practice.

## The gap report

The gate between profiling and any SQL in a specification-driven build; produce it, then stop for review.

| Verdict | Meaning |
| --- | --- |
| `EXACT` | Reproducible faithfully from the source as defined |
| `APPROX` | Buildable with a stated deviation: partial data, an undocumented definitional choice, a proxy |
| `NONE` | Not buildable from this source; state what is missing |

Per metric, five fields: documented definition with citation; verified source as exact `schema.table.column` names you checked exist, with match rates; deviation or what is missing; grain, with fan-out warning and how to count; blockers, as identifiers into the assumption ledger and data-quality register, each tied to an open question.

- Open with a verdict matrix, one row per metric, and a headline counting verdicts from the matrix, never from memory.
- Dimension availability is a separate, mandatory section: dimension, verdict, verified source, coverage; flag a dimension at a different grain than the fact (modeling problem), one needing an undocumented collapse map (definitional choice), one covering part of the population, one unsourced.
- Carry forward only contradictions and open questions touching what you must build; mark each **blocks** (cannot be exact) or **degrades** (buildable with caveat).
- Close with the `NONE` set and what unblocks each (missing input versus missing effort), decisions as choices for the reviewer, and a reality check of acceptance criteria against the data.
- Verify every cited identifier against the live catalogue before shipping; keep the report as an artifact.

## Specification versus build instructions

- The specification carries the rules: definitions, taxonomy, states, checks, definition of done. No environment values (connections, schema, profile, collection names).
- The build instructions carry those environment values plus build order, checkpoints, ledger format, validation procedure, stop conditions; they cite specification sections by number, never restate logic.
- Where they disagree, the specification wins and the disagreement is a checkpoint.
- Declare the completeness level the specification aims at; a staging-only build needs no full business-logic interview.
- Tag every non-obvious rule with provenance: profiled, user-stated, lifted from code, or defaulted.
- Escape hatch for unanticipated rules: model, body verbatim, `why`.
- Preserve hardcoded identifiers exactly; legacy ids that look like typos rarely are.
- A filled example specification is never a source of defaults for another business: reuse schema, slot list, and checks, never values.

## Exclusions and known errors as data

Three tables beside the models, at a grain that joins to the numbers:

| Table | One row per | Columns |
| --- | --- | --- |
| `dim_metric_definition` | Metric | Definition, formula, source document and section, status (current, planned, disputed), error vectors, open questions |
| `dim_data_quality_issue` | Incident | Period, entity, issue type, error magnitude and direction, status, whether history was corrected or left dirty |
| `dim_exclusion_rule` | Exclusion | Predicate, entity, reason, source document, whether the source enforces it |

- A model left-joins `dim_data_quality_issue` and offers an adjusted figure in its own column beside the reported one, never in place; approximate matches are best-effort.
- Exclusions are a filter over a tagged column, not a deletion: keep excluded rows with a reason and an inclusion flag; the default view filters them, an analyst unfilters.
- Verify every documented exclusion identifier against the data; a documented test account is frequently a real customer.

## Extracting a specification from code or documents

- Write for a reader who sees only the raw tables and your document; never "see the code".
- Read from code (imports, configuration, migrations, constants): each literal, narrowing filter, enum with full and dead values, derived classification with tiebreakers, timezone and event-time versus load-time detail, join with keys, cardinality, and fan-out or row loss.
- Tag every claim `PROVEN` (read directly from code, schema, or an explicit statement), `INFERRED`, or `UNKNOWN` (also an open question answerable in a sentence); cite file and line, or page and last-edited date, on every non-obvious claim.
- Date everything: mechanical timestamp and any date in the body. Tag every documented rule current, deprecated, planned, or unclear; where a document admits a process is inconsistently followed, quote it verbatim.
- Surface contradictions: both positions, both citations, both dates, which is newer.
- Hardcoded-value inventory as `value | meaning | where`: thresholds, cutoffs, allowlists, denylists, retention windows, defaults on null.
- Join map with key columns and cardinalities, explicit fan-out and drop warnings, a note wherever keys are unenforced.
- Record unreachable sources with what surrounding text says they hold. Close with a completeness claim: a table or column in the database but not in the document is a defect.
