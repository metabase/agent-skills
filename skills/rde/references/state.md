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

`./.scratch/rde-state.md` caches what the instance cannot hold, plus a working copy of the decisions; the instance wins on disagreement. Write each entry the moment it is known. Its first line is the format line, so a later version can tell older files apart.

```markdown
# rde state (format 1)
profile: <profile>   url: <base url>   chosen: env | state | named | installer | only | asked
db_id: <id>   engine: <engine>
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

## Stops
intake: answered 2026-09-28 (<who>)
proposal <slice>: answered 2026-09-28 (<who>)
go-live <layer>: answered 2026-09-28 (<who>)

## Questions
| question (verbatim) | definition | home table, time column | flags, breakouts | exists or build | status |

## Build
| model | transform | table | rows | tests | gate | note |
```

`profile` and `url` name the Metabase every command uses, and `chosen` says how it was picked: the step of `SKILL.md`, Which Metabase, that matched (`env`, `named`, `installer`, `only`, `asked`), or `state` for a file from before format 1, whose pick is re-checked but whose reason is unknown. A file without the format line gets it, and `chosen: state`, at its first write.

`## Stops` gets one line per planned stop (`references/collaboration.md`, The planned stops) the moment it returns, never before; a headless run writes `unanswered (headless)` in place of `answered …`. A stop with no line did not happen.

Keep `./.scratch` out of git: it holds probe output, row samples, and CSV diffs, and often sits inside the git-sync working directory, where a `git add -A` would commit it. When the working directory is inside a git repository, the first write to `./.scratch` also adds `.scratch/` to `.git/info/exclude` (in a worktree, the file `git rev-parse --git-path info/exclude` names), which is untracked and changes nothing anyone else sees:

```bash
mkdir -p ./.scratch
x=$(git rev-parse --git-path info/exclude 2>/dev/null) && { mkdir -p "$(dirname "$x")"; grep -qxF '.scratch/' "$x" 2>/dev/null || echo '.scratch/' >> "$x"; }
```

`tests`: a pass count, `none` with the reason, or `unavailable` with its signal (`references/transform-tests.md`). Deployed means tests pass, the last run succeeded, rows are above zero (or a confirmed empty result), and the gate has no blocking failure.

## Resume

If the file exists: re-check its instance first (`SKILL.md`, Which Metabase, step 1); when it no longer answers, say so plainly and re-run that order instead of silently switching. Then use its ids without asking; re-read what it names on the instance (transforms, runs, descriptions, caveats, the Document's decisions); trust the instance and name any drift; continue at `stage` and `next`. What is built, passing, and decided is done, whoever did it. If the file is missing but the work exists (`mb search "How to use" --models document`), rebuild it from the Document and the objects before asking anything; otherwise create it once the Metabase is picked.
