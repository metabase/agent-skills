# Transforms

A **transform** persists the result of a query (native SQL or MBQL) to a warehouse table the user can read from cards, dashboards, and other transforms. It runs on a schedule (via `transform-job`) or on-demand (`transform run`).

This file covers the create-and-run flow. The general flag conventions, body-input precedence, and output flags live in `../SKILL.md`. If you're authoring a transform inside a workspace, also see `workspace.md` for the canonical-vs-isolation-schema rule.

## Body shape

A transform has two halves:

- `source` — the query to run (`type: "query"`, with `query.type` of `native` or `mbql`).
- `target` — the warehouse destination (`type: "table"`, with `database`, `schema`, `name`).

Native SQL is the simplest source and the easiest to author by hand. MBQL is what the Metabase UI emits and is much more verbose; pull a sample with `metabase transform get <id> --full --json` if you need its shape.

If `source.query` is **MBQL 5** (`lib/type: "mbql/query"`), `transform create` and `transform update` validate it against the bundled query schema before sending; failure exits 2 with `{ ok, errors: [{path, message}] }` on stdout. To author MBQL 5 by hand: fetch the schema via `metabase query --print-schema --profile <n>`, iterate the body with `metabase query --file q.json --dry-run --profile <n>` until `ok: true`, then drop it into `source.query`. Legacy MBQL 4 and native sources skip pre-flight. Pass `--skip-validate` to bypass the pre-flight and let the server be the authority — useful when the bundled schema disagrees with what the server actually accepts.

## Workspace caveat: native SQL transforms can't reference *other* transforms' output tables

In a workspace, MBQL queries and ad-hoc native queries (run via `metabase query`) get their canonical references (`public.foo`) rewritten to the per-workspace isolation schema (`mb__isolation_<hash>_<ws-id>`) at execution time. **Transform execution of a native-SQL source does not get this rewrite.** The transform runs the SQL "raw" against the warehouse — fine for source tables that exist canonically in the warehouse, but it fails for the materialized output of *other* transforms (which only exist in the isolation schema, named `<canonical_schema>__<table>`).

Symptom: a native-SQL transform `SELECT … FROM public.shipments_enriched` (where `shipments_enriched` is itself a transform output) fails with:

```
Error executing raw queries: ERROR: relation "public.shipments_enriched" does not exist
```

…even though `metabase query --file q.json --skip-validate` against the same SQL works fine (because that path goes through the QP).

Fix: **author transform-of-transform sources as MBQL 5**, with a numeric `source-table` referring to the upstream transform's table id (look it up via `metabase table list --db-id <id> --profile <ws-name> --json` after the upstream transform has run — the materialized table will appear under the canonical schema). The MBQL execution path goes through the QP and the rewrite applies. Native SQL is fine when the transform reads only from canonical source tables (`public.orders`, `public.shipments`, …) — those exist in the warehouse under the canonical name and don't need rewriting.

Don't reach for the workspace's isolation-schema name as a workaround — it changes per workspace and breaks portability. See `workspace.md`'s "Don't" list.

## MBQL 5 aggregations: name your output columns

Default MBQL 5 aggregations materialize as `count`, `count_where`, `count_where_2`, `avg`, `avg_2`, `sum`, … — ugly when the result is a transform target. Pass `name` and `display-name` in the aggregation's options object to control them:

```json
["count",
 {"lib/uuid": "...-1111", "name": "shipments_shipped", "display-name": "Shipments shipped"}]

["count-where",
 {"lib/uuid": "...-2222", "name": "shipments_delivered", "display-name": "Shipments delivered"},
 ["=", {"lib/uuid": "...-2222a"}, ["field", {"base-type": "type/Text", "lib/uuid": "...-2222b"}, 1779], "delivered"]]
```

The `name` value becomes the warehouse column name on the materialized table. The `display-name` is the column header in the UI.

## MBQL 5 order-by referencing an aggregation

Order by an aggregation column with an `["aggregation", {…}, "<aggregation-uuid>"]` ref — the third arg is the **string UUID** of the target aggregation's `lib/uuid`, **not** its numeric position:

```json
"aggregation": [["count", {"lib/uuid": "agg-uuid-001"}]],
"order-by": [
  ["desc", {"lib/uuid": "..."},
    ["aggregation", {"lib/uuid": "..."}, "agg-uuid-001"]]
]
```

A numeric index (`["aggregation", {…}, 0]`) fails pre-flight with `must be string` at `/stages/0/order-by/0/2/2`.

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

TRANSFORM_ID=$(metabase transform create --file /tmp/transform.json --profile <name> --json | jq -r '.id')
metabase transform run "$TRANSFORM_ID" --wait --profile <name> --json
```

Notes:
- `<db-id>` comes from `metabase database list --profile <name> --json`. Database ids are per-instance — a workspace child re-numbers them independently of the parent.
- Target `schema` is the **canonical** name (e.g. `public`). In a workspace, the QP rewrites it to the per-workspace isolation schema (`mb__isolation_<hash>_<ws-id>`) at execution time — don't hard-code that prefix.
- `--wait` on `transform run` polls until status is `succeeded` or `failed`. Without it you only get `{run_id, message: "Transform run started"}` and have to poll yourself.
- The heredoc with single-quoted `'EOF'` prevents shell from interpolating any `$vars` inside the SQL.

## Inspect

```bash
metabase transform list --profile <name> --json
metabase transform get <id> --profile <name> --full --json     # full transform incl. last run summary
```

After a run, the materialized table is queryable via `metabase` (`card create` against it, native query against `<schema>.<name>`, etc.). Columns and types are inferred from the result set; if you change the SELECT shape, drop the table first or the next run will fail on a column-mismatch error.

## Drop the materialized table (keep the transform)

```bash
metabase transform delete-table <id> --yes --profile <name>
```

Useful when you've changed the SELECT and want a fresh `CREATE TABLE` on the next run. **`--yes` is required** in non-interactive contexts; without it the command exits with `--yes required to delete non-interactively`.

## Delete the transform

```bash
metabase transform delete <id> --yes --profile <name>
```

Removes the definition. Whether the materialized table is dropped depends on the server — check with `metabase table list --db-id <db-id> --profile <name> --json` if it matters. Same `--yes` rule as `delete-table`.

## Transform jobs (schedules)

A schedule lives in a separate resource (`transform-job`) and references one or more transform ids. Create with the same body-input pattern (`--file body.json`); see `metabase transform-job --help` for the verb list. Most ad-hoc agent work is one-off `transform run`, not job authoring.

## Don't (transform-specific)

- Don't put `transform run` calls in tight polling loops — pass `--wait` and let the CLI handle the polling. Manual loops without `--wait` will hammer the server.
- Don't author MBQL 4 (the legacy nested `{ type: "query", query: {...} }` shape) by hand — pull a sample with `metabase transform get <id> --full --json`. MBQL 5 (`lib/type: "mbql/query"`) **is** authorable by hand thanks to the `metabase query --print-schema` + `--dry-run` feedback loop; for non-trivial pipelines you may still prefer building in the UI and exporting.
- Don't write the workspace isolation schema into `target.schema` or SQL. See `workspace.md` for the canonical-name rule.
