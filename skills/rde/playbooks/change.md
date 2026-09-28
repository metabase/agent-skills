# Change what is delivered

Applies when the user changes, adds to, or disputes a delivered definition, table, or number, when a transform gets one case wrong, and on any instance humans built. Produces the change in one place, planned against dependents, approved with its before and after, tests and dependents re-run, restated, and a hand-back naming what moved and by how much. It owns versioning, retirement, and restatement.

Read first: `references/transform-tests.md` for a transform; `references/semantic-layer.md` for a definition. Follow the instance's naming, collection, and description conventions.

Order: 1 find the rule and dependents, 2 plan (the stop for a definition or dispute), 3 transform (the stop at 3.6) or 4 definition, 5 restate, hand-back.

## 1. Find the rule and what depends on it

Read the object as it stands (the transform's description, SQL, runs, tests; the definition's body and description; its decisions in the state file and the domain Document). The rule lives in one place: a transform's SQL, `cfg_<domain>`, or a definition's query. List dependents: transforms reading its table, cards and metrics naming its id or table, dashboards holding them (`mb dashboard cards`), documents embedding them, subscriptions and alerts on them:

```bash
source ./.scratch/probe.sh; P=(--profile <profile> --json --max-bytes 0)
mb search "<name>" --models card,metric,dataset,dashboard,document,transform,segment,measure --limit 500 "${P[@]}"   # search defaults to 20; page while has_more
mb transform list --fields id,name,source "${P[@]}" | jq --argjson t <table-id> '[.data[] | select((.source | tostring | test("<schema>\\.<table>"; "i")) or (.source | tostring | test("\"source-table\":\($t)[,}]"))) | {id, name}]'
mb card list --fields id,name,type,dataset_query "${P[@]}" | jq --argjson id <definition-id> --argjson t <table-id> '[.data[] | select(.dataset_query | tostring | test("\"(metric|measure|segment)\",\\{[^}]*\\},\($id)[],]") or test("\"source-table\":\($t)[,}]")) | {id, name, type}]'
```

If stored queries reference definitions by `entity_id`, scan for that string. What the scan cannot see (another database's native questions, exports scheduled elsewhere) is named unchecked. A permission error is a stop for the admin, never a copy under another name.

## 2. Plan

- Non-breaking (logic only; same columns, grain, key): in place, same id.
- Breaking (a column a dependent reads removed, renamed, or retyped; grain, key, or a definition's table changed): a new version beside the old (version in the name), a migration list naming each dependent and its edit, the old renamed `Deprecated: <name>` with a description naming its successor, one reporting cycle for dependents to move, then archive; never delete.

Every change to a delivered object is approved once, with the before and after on the last three complete periods and the direction and size of the move: for a definition here (old and new queries through `mb query`), for a transform at §3.6 once the dev copy's diff exists. The approval also lists the restatement writes §5 will make (the timeline event, the dated text cards and the dashboards they go on, description change lines). A dispute between owners is a stop here with both readings; until answered the published definition stands, its description saying it is disputed.

## 3. A transform

1. Save the current state: `mb transform get <id> --full > ./.scratch/<model>.prev.json`, its SQL in `.prev.sql` (rollback is a source patch with it).
2. Run its tests as they stand: a green baseline, or a finding to report first.
3. Dev copy: an untagged transform `<model>__dev` with the patched SQL targeting `<model>__dev` in the output schema (a scratch object, removed in step 8); copy the tests onto it (the target name in `empty` SQL becomes `<model>__dev`) and add the motivating case there as a fixture row and expectation; see it fail on the unpatched SQL, then run to green by fixing the SQL; run the dev copy and its gate.
4. The live tests stay untouched until step 7.
5. Diff dev against live on the grain (`references/reconciliation.md`, Compare at the finest shared grain): moved rows are the change; a row moved by no rule you changed is a bug.
6. The approval stop: the diff in numbers, before and after on the headline, the tests. A test that must be deleted is its own question.
7. Patch live in place (source only); a changed column shape needs `mb transform delete-table <id> --yes` first; a rename is breaking and follows §2's versioned path. Update the live tests (moved expectations get new rows; old and new rows go in the hand-back; never deleted), then run tests, transform, gate.
8. Remove the dev copy: `mb transform delete-table <dev-id> --yes`, `mb transform delete <dev-id> --yes`.
9. Run the job so dependents rebuild, their tests and gates with them.

A `cfg_<domain>` change runs the tests of every model reading it under the new value before the update and the job run.

## 4. A definition

After the §2 approval: same id (dashcards and documents hold it), `mb measure update` / `mb segment update` with a `revision_message` naming the cause, `mb card update` for a metric; the body validated as in `SKILL.md` (mb conventions). A changed metric loses its verified badge: re-run the golden set, then ask the user to re-verify in the UI.

## 5. Restate

This is also the protocol for any shipped number found wrong; never restate silently.

- Prepend `Changed <date>: <what and direction>` to the definition's description.
- Re-run every dependent (`mb card query`), showing each number before and after; the plausibility pass (`references/dashboards.md`) on every dependent dashboard.
- One timeline event (`mb timeline-event create`: name, description, `timestamp`, `timezone`, `time_matters`, `timeline_id`) in the collection of the metric's time-series questions, with direction and size; create the timeline there first if none exists (events render only on questions in the same collection).
- A dated text card on each dependent dashboard for one period: old figure, new figure, cause, which past periods moved.
- The decision closed as a decided line with who and both readings; the domain Document updated; glossary entries listed when a meaning moved; the same said in the hand-back.

Small chores on the way (collections, snippets, timelines, settings, uploads, tags, jobs): the matching verb after `--help`; destructive writes (archive, delete, a setting, replacing an upload) need the user's word first.

## Done when

The rule changed in one place; every dependent re-run or on the migration list; tests and gate green; dev copy gone; change line, timeline event, and decided line written. Hand-back: which numbers moved, by how much, which past periods restated.
