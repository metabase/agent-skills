# Transforms

A **transform** persists the result of a query (native SQL or MBQL) to a warehouse table the user can read from cards, dashboards, and other transforms. It runs on a schedule (via `transform-job`) or on-demand (`transform run`).

This file covers the create-and-run flow. The general flag conventions, body-input precedence, and output flags live in `../SKILL.md`. If you're authoring a transform inside a workspace, also see `workspace.md` for the canonical-vs-isolation-schema rule.

## Body shape

A transform has two halves:

- `source` — the query to run (`type: "query"`, with `query.type` of `native` or `mbql`).
- `target` — the warehouse destination (`type: "table"`, with `database`, `schema`, `name`).

Native SQL is the simplest source and the easiest to author by hand. MBQL is what the Metabase UI emits and is much more verbose; pull a sample with `metabase transform get <id> --full --json` if you need its shape.

If `source.query` is **MBQL 5** (`lib/type: "mbql/query"`), `transform create` and `transform update` validate it against the bundled query schema before sending; failure exits 2 with `{ ok, errors: [{path, message}] }` on stdout. To author MBQL 5 by hand: fetch the schema via `metabase query --print-schema --profile <n>`, iterate the body with `metabase query --file q.json --dry-run --profile <n>` until `ok: true`, then drop it into `source.query`. Legacy MBQL 4 and native sources skip pre-flight. Pass `--skip-validate` to bypass the pre-flight and let the server be the authority — useful when the bundled schema disagrees with what the server actually accepts.

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
metabase transform delete-table <id> --profile <name>
```

Useful when you've changed the SELECT and want a fresh `CREATE TABLE` on the next run.

## Delete the transform

```bash
metabase transform delete <id> --profile <name>
```

Removes the definition. Whether the materialized table is dropped depends on the server — check with `metabase table list --db-id <db-id> --profile <name> --json` if it matters.

## Transform jobs (schedules)

A schedule lives in a separate resource (`transform-job`) and references one or more transform ids. Create with the same body-input pattern (`--file body.json`); see `metabase transform-job --help` for the verb list. Most ad-hoc agent work is one-off `transform run`, not job authoring.

## Don't (transform-specific)

- Don't put `transform run` calls in tight polling loops — pass `--wait` and let the CLI handle the polling. Manual loops without `--wait` will hammer the server.
- Don't author MBQL 4 (the legacy nested `{ type: "query", query: {...} }` shape) by hand — pull a sample with `metabase transform get <id> --full --json`. MBQL 5 (`lib/type: "mbql/query"`) **is** authorable by hand thanks to the `metabase query --print-schema` + `--dry-run` feedback loop; for non-trivial pipelines you may still prefer building in the UI and exporting.
- Don't write the workspace isolation schema into `target.schema` or SQL. See `workspace.md` for the canonical-name rule.
