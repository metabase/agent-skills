# Transforms

A **transform** persists the result of a query (native SQL or MBQL) to a warehouse table the user can read from cards, dashboards, and other transforms. It runs on a schedule (via `transform-job`) or on-demand (`transform run`).

This file covers the create-and-run flow. The general flag conventions, body-input precedence, and output flags live in `../SKILL.md`. If you're authoring a transform inside a workspace, also see `workspace.md` for the canonical-vs-isolation-schema rule.

## Body shape

A transform has two halves:

- `source` — the query to run (`type: "query"`, with `query.type` of `native` or `mbql`).
- `target` — the warehouse destination (`type: "table"`, with `database`, `schema`, `name`).

Native SQL is the simplest source and the easiest to author by hand. MBQL is what the Metabase UI emits and is much more verbose; pull a sample with `mb transform get <id> --full --json` if you need its shape.

If `source.query` is **MBQL 5** (`lib/type: "mbql/query"`), `transform create` and `transform update` validate it against the bundled query schema before sending; failure exits 2 with `{ ok, errors: [{path, message}] }` on stdout. To author MBQL 5 by hand: fetch the schema via `mb query --print-schema --profile <n>`, iterate the body with `mb query --file q.json --dry-run --profile <n>` until `ok: true`, then drop it into `source.query`. Legacy MBQL 4 and native sources skip pre-flight. Pass `--skip-validate` to bypass the pre-flight and let the server be the authority — useful when the bundled schema disagrees with what the server actually accepts.

**Mint UUIDs for `lib/uuid` slots before assembling the body — never invent, hard-code, or reuse them.** Every clause options object carries a `lib/uuid` (UUID v4); the bundled schema enforces RFC 4122 format strictly, so placeholder strings fail `--dry-run`. Workflow: count the slots, run `mb uuid --count <N> --json`, substitute each minted value into its slot. The examples below use `<UUID:label>` sentinels (NOT valid UUIDs) so the assembly step is unambiguous — replace each sentinel with a freshly-minted UUID before sending. Same `<UUID:label>` token must be replaced with the same minted UUID (used for aggregation-ref ↔ aggregation pairing); distinct sentinels get distinct UUIDs.

**Clause shape: opts always second, args after.** Every clause is `[op, {options}, ...args]`. Field refs are `["field", {options}, fieldId]` (id third), not the legacy MBQL 4 shape `["field", id, opts]`. The same rule holds for aggregations, filters, order-by — the options object never moves out of slot 1.

## MBQL 5 aggregations: name your output columns

Default MBQL 5 aggregations materialize as `count`, `count_where`, `count_where_2`, `avg`, `avg_2`, `sum`, … — ugly when the result is a transform target. Pass `name` and `display-name` in the aggregation's options object to control them. Mint 4 UUIDs (`mb uuid --count 4 --json`) for the slots below before assembling:

```json
["count",
 {"lib/uuid": "<UUID:agg-shipped>", "name": "shipments_shipped", "display-name": "Shipments shipped"}]

["count-where",
 {"lib/uuid": "<UUID:agg-delivered>", "name": "shipments_delivered", "display-name": "Shipments delivered"},
 ["=", {"lib/uuid": "<UUID:eq-filter>"},
  ["field", {"base-type": "type/Text", "lib/uuid": "<UUID:status-field>"}, 1779],
  "delivered"]]
```

The `name` value becomes the warehouse column name on the materialized table. The `display-name` is the column header in the UI.

## MBQL 5 order-by referencing an aggregation

Order by an aggregation column with an `["aggregation", {…}, "<aggregation-uuid>"]` ref — the third arg is the **string UUID** of the target aggregation's `lib/uuid`, **not** its numeric position. The aggregation's own `lib/uuid` and the ref's third element must be the same minted UUID (string equality); the order-by clause itself and the ref clause each carry their own separate `lib/uuid` in their options. Mint 3 UUIDs and substitute — note that `<UUID:agg-count>` appears twice and gets the same minted value:

```json
"aggregation": [
  ["count", {"lib/uuid": "<UUID:agg-count>"}]
],
"order-by": [
  ["desc", {"lib/uuid": "<UUID:order-desc>"},
    ["aggregation", {"lib/uuid": "<UUID:agg-ref>"},
     "<UUID:agg-count>"]]
]
```

A numeric index (`["aggregation", {…}, 0]`) fails pre-flight with `must be the target aggregation's lib/uuid (string), not a numeric position` at `/stages/0/order-by/0/2/2`.

## Create + run (native SQL)

```bash
cat > /tmp/transform.json <<'EOF'
{
  "name": "user_counts_by_signup_year",
  "description": "Sample transform: counts users by year of signup",
  "source": {
    "type": "query",
    "query": {
      "type": "native",
      "database": <db-id>,
      "native": {
        "query": "SELECT date_trunc('year', created_at)::date AS signup_year, COUNT(*)::int AS user_count FROM public.users GROUP BY 1 ORDER BY 1"
      }
    }
  },
  "target": {
    "type": "table",
    "database": <db-id>,
    "schema": "public",
    "name": "user_counts_by_signup_year"
  }
}
EOF

TRANSFORM_ID=$(mb transform create --file /tmp/transform.json --profile <name> --json | jq -r '.id')
mb transform run "$TRANSFORM_ID" --wait --profile <name> --json
```

Notes:
- `<db-id>` comes from `mb database list --profile <name> --json`. Database ids are per-instance — a workspace child re-numbers them independently of the parent.
- Target `schema` is the **canonical** name (e.g. `public`). In a workspace, the QP rewrites it to the per-workspace isolation schema (`mb__isolation_<hash>_<ws-id>`) at execution time — don't hard-code that prefix.
- `--wait` on `transform run` polls until status is `succeeded` or `failed`. Without it you only get `{message: "Transform run started", run_id, final: null}` and have to poll yourself.
- The `--json` envelope is shape-stable: `{message, run_id, final}`. `final` is always present — `null` when `--wait` is omitted or the run never started, otherwise a full `TransformRun` object with `status` and `message`. On a failed run (`final.status` ∈ {`failed`, `timeout`, `canceled`}) the CLI exits 1 and writes a one-line summary `transform run <id> failed` to stderr; the failure detail lives only in `final.message` on stdout, so `jq -r '.final.message'` is where to look.
- The heredoc with single-quoted `'EOF'` prevents shell from interpolating any `$vars` inside the SQL.
- `transform create --json` returns the agent-facing compact projection: `{id, name, description, source_type, target: {type, database, schema, name}, target_db_id}`. Read `target.schema`/`target.name` directly off the create output — no follow-up `transform get` needed to verify where the transform will write.
- If a transform with the same `name` already has a YAML representation on disk under the configured remote-sync repo, `create` mints a `_2` suffix on the exported filename (the new transform gets a fresh `entity_id`; the prior one isn't touched). For "iterate on the same concept" workflows, prefer `transform update <id>` — see "Iterating on a failing transform" below.

## Inspect

```bash
mb transform list --profile <name> --json
mb transform get <id> --profile <name> --full --json     # full transform incl. last run summary
```

After a run, the materialized table is queryable via `mb` (`card create` against it, native query against `<schema>.<name>`, etc.). Columns and types are inferred from the result set; if you change the SELECT shape, drop the table first or the next run will fail on a column-mismatch error.

## Inspect runs and cancel an in-flight run

```bash
# Recent runs across all transforms (drains all pages by default; cap with --limit):
mb transform runs --profile <name> --json
mb transform runs --transform-id <id> --limit 10 --profile <name> --json

# Fetch one run by RUN id (NOT transform id — the run id comes from `transform run` or `transform runs`):
mb transform get-run <run-id> --profile <name> --json

# Cancel the currently-running run for a transform:
mb transform cancel <id> --profile <name> --json
```

Notes:
- `transform runs` and `transform get-run` parse against the same `TransformRun` schema, so `get-run` returns the same per-run shape as one entry of `runs`. The compact projection is `{id, transform_id, status, run_method, start_time, end_time, message}`. Pass `--full` on `get-run` for the hydrated row including `is_active`, `user_id`, `transform_name`, `transform_entity_id`, `checkpoint_*` fields, and a nested `transform: {id, name, …}` block.
- `transform cancel` takes the **transform** id and 404s with `Endpoint not found — is this a Metabase instance?` if there is no active run. The response shape is `{canceled: true, id: <transform-id>}`.
- For native-SQL transforms, cancel marks the run as `canceling` but does **not** kill the warehouse query mid-flight — the query runs to completion, then the run lands as `canceled` (or stays `succeeded` if the cancel arrived after the writer committed). For Python transforms the worker is interrupted directly. Don't expect cancel to free warehouse resources instantly on long native queries; expect it to flip state and prevent downstream consumers from treating the result as good.
- The `--transform-id` filter on `runs` accepts a single integer; the CLI translates to the server's `transform-ids` query vector. To cross-filter multiple transforms, run `transform runs --json` and `jq` post-hoc.

## Update body: send only writable keys, never round-trip the GET body

`transform update <id>` is **PATCH semantics** — only send the fields you actually want to change. The endpoint accepts exactly these writable keys:

```
name, description, source, target, run_trigger,
tag_ids, collection_id, owner_user_id, owner_email
```

**Don't paste the output of `transform get` into a `transform update` body.** The GET response carries server-side fields (`id`, `entity_id`, `created_at`, `updated_at`, `creator_id`, `last_run`, `target_db_id`, `target_table_id`, `source_type`, `source_database_id`, `source_readable`, `creator`, `owner`, `table`, …) that the PUT endpoint isn't built to handle. Currently, unknown top-level keys flow into `t2/update!` and produce a leaked H2 SQL error like:

```
Column "TAGS" not found; SQL statement:
UPDATE "TRANSFORM" SET "TAGS" = (), "UPDATED_AT" = NOW() WHERE "ID" = ? [42122-214]
```

Two specific footguns:

- **`tags` is not a key on the REST API.** The serdes/YAML representation uses `tags`; the REST contract uses `tag_ids` (an array of integer ids). If you pulled a YAML representation and want to PUT it, translate `tags: [...]` → `tag_ids: [...]` first (or omit it entirely if you're not changing tag membership).
- **`source_type`, `target_db_id`, `target_table_id`, `entity_id`** are derived/computed by the server. They appear in GET responses for the agent's benefit; the server doesn't accept them on update.

Right shape — patch only what changes:

```bash
# Rename only:
mb transform update <id> --body '{"name":"renamed"}' --profile <name> --json

# Rewrite the SQL only:
cat > /tmp/patch.json <<'EOF'
{ "source": { "type": "query", "query": { "type": "native",
    "database": <db-id>,
    "native": { "query": "SELECT … FROM public.orders" } } } }
EOF
mb transform update <id> --file /tmp/patch.json --profile <name> --json

# Change tag membership (note: tag_ids, not tags):
mb transform update <id> --body '{"tag_ids":[1,3]}' --profile <name> --json
```

If you really must round-trip, project to the writable subset:

```bash
mb transform get <id> --full --profile <name> --json \
  | jq '{name, description, source, target, run_trigger, tag_ids, collection_id, owner_user_id, owner_email}
        | with_entries(select(.value != null))' \
  > /tmp/patch.json
```

## Iterating on a failing transform

When `transform run` fails and you want to retry with a fixed body, **prefer `transform update <id> --file body.json` over `transform delete <id>` + `transform create`.** Update keeps the same row, the same `entity_id`, the same materialized table, and the same on-disk YAML filename. Concretely this means:

- `remote-sync export` produces **one** clean commit containing only the fix, instead of "broken transform" + "remove broken transform" landing as two commits in `git log`.
- You don't have to chase `_2` suffixes minted when two YAMLs share a `name` on disk (see the `transform create` notes above).
- The materialized output table either updates in place or, if the SELECT shape changed incompatibly, errors loudly on the next run rather than landing in a parallel `..._2` table the agent has to clean up. (`transform delete-table <id>` resets the column shape if you need a clean slate.)

Recipe:

```bash
# 1. Try once
ID=$(mb transform create --file /tmp/t.json --profile <n> --json | jq -r '.id')
mb transform run "$ID" --wait --profile <n> --json     # → failed

# 2. Fix the body in place; PATCH only what changed.
#    Source-only patch — keeps name, target, tags untouched on the server.
cat > /tmp/source-patch.json <<'EOF'
{ "source": { "type": "query", "query": { "type": "native",
    "database": <db-id>,
    "native": { "query": "<fixed SQL here>" } } } }
EOF
mb transform update "$ID" --file /tmp/source-patch.json --profile <n> --json

# 3. Re-run
mb transform run "$ID" --wait --profile <n> --json     # → succeeded
```

If you really must `create + delete` instead, do the `delete` **before** the first `remote-sync export` so the failed entity never lands in git history. Order matters: agents reflex to "export to checkpoint progress," but for transforms an export of a soft-failed state is mostly noise that needs a follow-up cleanup commit. See `references/remote-sync.md` "Read state before mutating" for the ordering rule.

## Drop the materialized table (keep the transform)

```bash
mb transform delete-table <id> --yes --profile <name>
```

Useful when you've changed the SELECT and want a fresh `CREATE TABLE` on the next run. **`--yes` is required** in non-interactive contexts; without it the command exits with `--yes required to delete non-interactively`.

## Delete the transform

```bash
mb transform delete <id> --yes --profile <name>
```

Removes the definition. Whether the materialized table is dropped depends on the server — check with `mb table list --db-id <db-id> --profile <name> --json` if it matters. Same `--yes` rule as `delete-table`.

## Transform jobs (schedules)

A schedule lives in a separate resource (`transform-job`) and references one or more transform ids. Create with the same body-input pattern (`--file body.json`); see `mb transform-job --help` for the verb list. Most ad-hoc agent work is one-off `transform run`, not job authoring.

## Don't (transform-specific)

- Don't put `transform run` calls in tight polling loops — pass `--wait` and let the CLI handle the polling. Manual loops without `--wait` will hammer the server.
- Don't author MBQL 4 (the legacy nested `{ type: "query", query: {...} }` shape) by hand — pull a sample with `mb transform get <id> --full --json`. MBQL 5 (`lib/type: "mbql/query"`) **is** authorable by hand thanks to the `mb query --print-schema` + `--dry-run` feedback loop; for non-trivial pipelines you may still prefer building in the UI and exporting.
- Don't write the workspace isolation schema into `target.schema` or SQL. See `workspace.md` for the canonical-name rule.
- Don't paste a `transform get` body into `transform update` — the PUT endpoint only accepts writable keys, and unknown keys (notably `tags`, `source_type`, `entity_id`, `created_at`, `last_run`) leak as raw SQL errors. See "Update body: send only writable keys" above. Use `tag_ids` (not `tags`) on the REST contract.
