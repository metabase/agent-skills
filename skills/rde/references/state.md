# State

Where each fact lives, the working file, and how a session resumes.

## State lives on the objects

| Fact | Home |
| --- | --- |
| One row per what, key, scope, filters a reader must apply | the table's `description`: `grain:`, `scope:`, `required filters:` lines (`references/modeling.md`, The description) |
| Incomplete period, history horizon, exclusions, provisional rules | the table's `caveats` |
| Owner | `owner_email` on table and transform; the last sentence of a definition's description |
| How a model is built; what its rules must do | the transform's description and SQL; its transform tests |
| What a number means | the definition's description |
| Whether a table is for readers | `data_layer` (`final`, `internal`, `hidden`) and `is_published` |
| A definition change or data incident | a timeline event in the collection of the affected time-series questions |
| Decisions, owners, open questions | the domain Document's decisions section, created at the first proposal point |

Nothing on the instance is written twice. Read back with `mb table get <id> --full`, `mb transform get <id> --full`, `mb card get <id>`, `mb transform-test list --transform <id>`.

## The working file

`./.scratch/rde-state.md` caches what the instance cannot hold, plus a working copy of the decisions; the instance wins on disagreement. Write each entry the moment it is known.

```markdown
# rde state
profile: <profile>   url: <base url>   db_id: <id>   engine: <engine>
environment: production | staging (branch <name>)
raw_schemas: <names>   out_schema: <name>
conventions: <prefixes, naming, collection layout found, or "defaults">
collections: <role>=<id> …   library: data=<id> metrics=<id> | unavailable
tag: <name>=<id>   job: <id>   domain_notes: <fired>   document: <id>
owner: <who owns definitions>   mode: default | check-with-me | just-go
stage: <playbook>   next: <next step and what blocks it>
last_complete_period: <period> (watermark <time> on <table>; lateness p99 <duration>; newest-period volume <ratio> of trailing average)

## Decisions
open 2026-09-28 [churn-date]: which timestamp stops MRR; default end of paid service; readings: end of service: 41 churned vs cancellation: 48

## Questions
| question (verbatim) | definition | home table, time column | flags, breakouts | exists or build | status |

## Build
| model | transform | table | rows | tests | gate | note |
```

`tests`: a pass count, `none` with the reason, or `unavailable` with its signal (`references/transform-tests.md`). Deployed means tests pass, the last run succeeded, rows are above zero (or a confirmed empty result), and the gate has no blocking failure.

## Resume

If the file exists: use its profile and ids without asking; re-read what it names on the instance (transforms, runs, descriptions, caveats, the Document's decisions); trust the instance and name any drift; continue at `stage` and `next`. What is built, passing, and decided is done, whoever did it. If the file is missing but the work exists (`mb search "How to use" --models document`), rebuild it from the Document and the objects before asking anything; otherwise create it once the profile is known.
