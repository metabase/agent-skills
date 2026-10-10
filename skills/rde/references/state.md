# State

Every playbook reads and writes here.

## STATE.md

`./.scratch/` is personal working state, kept out of git and never shared: a decision teammates need lives in the transform's or metric's description as its id plus its one line (`D7: churn after one month without revenue`), never the id alone. `./.scratch/STATE.md`, this schema:

````markdown
# STATE
```yaml
profile: prod
db_id: <db-id>
engine: <from mb db get>
raw_schema: raw_billing
out_schema: analytics
layers: stg, int, mart        # theirs, or the default
collections: stg=<id> int=<id> mart=<id> analytics=<id> drafts=<id>
library: data=<id> metrics=<id>   # or: unavailable
tag: <tag>=<id>  job: <id>
autonomy: balanced            # owner of definitions: the user, unless they name someone
environment: production       # or: staging, branch <name>
remote_sync: none             # or: <branch>, read-write | read-only; from mb git-sync status; none means never raise syncing
synced_root: none             # or: <id> <name>, the synced top-level collection content files under (SKILL.md, Remote sync)
domain: subscription-revenue  # or none, or two when a table genuinely straddles domains
stage: build-clean-tables
next: model 8 of 15, blocked on D7
last_complete_period: 2026-08 # max(event_at)=09-11, ratio 0.31
```

## Models
| model | transform_id | table_id | rows | tests | gate | note |
|---|---|---|---|---|---|---|

## Decisions
| id | decision | answer | readings | by | date | status | affects |
|---|---|---|---|---|---|---|---|
| D7 | churn gap, months | 1 | 1: 41 churned; 2: 48 (+17%, of 284 Aug churn) | CEO | | PROVISIONAL | churn metric |

## Questions
| question (verbatim) | metric | home table, time column | definitional filter | breakouts (own, or FK to entity.column) | exists or build | status |
|---|---|---|---|---|---|---|

## Checks
| model | dup_key | null_required | cast | rows | grain | non_negative | period_flag | enum |
|---|---|---|---|---|---|---|---|---|
````

The header stays inside its `yaml` fence. Every table keeps its `|---|` delimiter row; append rows below it.

Status: `open`, `PROVISIONAL` (default in use), `decided`. Record each the moment it is known. `readings` carries both measured figures and the gap for a decision on a column traced to a headline number, `n/a` otherwise ([collaboration-contract.md](collaboration-contract.md)).

## Where state lives

- A fact about a model (five header facts, constants): the transform's description; the SQL header mirrors it ([layering-and-naming.md](layering-and-naming.md)).
- A fact about a number: the metric's or segment's description.
- A definition change or data incident: a `mb timeline-event` in the affected questions' collection.
- Decisions and check results: those tables; `open` or `PROVISIONAL` holds its `affects` at `Draft` ([collaboration-contract.md](collaboration-contract.md)).
- An exclusion: a flagged column with a reason (a threshold as a `cfg_<domain>` constant), never a silent `WHERE`; a `dim_exclusion_rule` table (predicate, entity, reason, source, source-enforced) the models left-join only when several documented rules exist.

Nothing is written twice. Deployed means: filed per the company's convention (or landed outside Metabase); its transform tests pass (`tests` is a pass count, or `none` with a reason, or `unavailable` when the instance, the token, or the driver cannot run tests; [transform-tests.md](transform-tests.md)); last run succeeded; rows above zero or a confirmed empty result; no FAIL in Checks.

## Resume

`cat ./.scratch/STATE.md` first. If it exists: use its profile, ids, environment, and autonomy without asking; `mb transform list --fields id,name,description,target --json` confirms its models; continue at `stage` and `next`, rebuilding the playbook checklist from them with done steps ticked. If not, create it once the profile is known, with `autonomy: balanced`.

## The probe helper

An executable, written once per job; it reads `profile` and `db_id` from STATE.md on every call, so no shell state carries over:

```bash
cat > ./.scratch/q <<'SH'
#!/usr/bin/env bash
# ./.scratch/q "<sql>": one native query on STATE.md's profile and db_id
s="$(dirname "$0")/STATE.md"
v() { awk -v k="$1:" '$1 == k { print $2; exit }' "$s"; }
PROFILE=$(v profile) DB=$(v db_id)
case $DB in ''|*[!0-9]*) jq -nc --arg e "no numeric db_id in $s" '{status: "failed", error: $e}'; exit 1;; esac
jq -n --arg q "$1" --argjson db "$DB" '{"lib/type":"mbql/query",database:$db,stages:[{"lib/type":"mbql.stage/native",native:$q}]}' \
  | mb query --file - --profile "$PROFILE" --json --max-bytes 0 2>&1 \
  | grep -v 'Could not parse the Metabase version' \
  | jq -cR '(fromjson? // {ok: false, error: {message: .}})
           | if .ok == false then {status: "failed", error: .error.message}
             else {status, error, cols: [.data.cols[]?.name], rows: .data.rows} end'
SH
chmod +x ./.scratch/q
```

`./.scratch/q "SELECT count(*) FROM raw.orders"` is one call. Pass: `status == "completed"`; else read `error`. A warehouse SQL error, an unreachable instance, and a bad profile or database id all reach `mb` as `{"ok": false, "error": {...}}` on stderr with empty stdout; `q` merges stderr and returns each as `status: "failed"`, and any other stray stderr line as its own `failed` line. A missing or placeholder `db_id` in STATE.md fails the same way. Never add `2>/dev/null` to `q` or `mb query`: the only noise, the head-build version warning, is already dropped, and silencing stderr loses the error. `--max-bytes 0` lifts the CLI's 24 KB output cap; the instance's row limits still apply ([profiling-catalog.md](profiling-catalog.md)).
