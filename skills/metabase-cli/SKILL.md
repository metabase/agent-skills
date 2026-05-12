---
name: metabase-cli
description: Drive a Metabase instance from the terminal via the `metabase` CLI. Authenticate with named profiles; inspect databases (list, get, full metadata rollup, schemas, tables in a schema) and trigger manual schema sync / field-values rescan; inspect tables, fields; list/get/create/update/archive cards (questions, models, metrics) and run them as JSON/CSV/XLSX; list/get/create/update dashboards and patch dashcards; list/get/create collections and traverse the hierarchy by id, entity_id, or "root"/"trash" (with items and recursive tree); list/get/create/update/archive native query snippets, segments, and measures; author/update/run transforms and schedule transform-jobs; read/update settings; search content (cards, dashboards, collections, transforms, metrics); manage Enterprise workspaces; remote-sync to/from a git remote (status, dirty, import, export, branches, stash, add/remove a collection from sync). Use whenever the user wants to interact with a Metabase from the terminal — "log into metabase", "what profiles do I have", "list cards", "run card 42 as CSV", "create a transform", "list dashboards", "move a dashcard", "list collections", "what's in collection 4", "show the collection tree", "list snippets", "create a segment", "archive a measure", "search metabase for X", "spin up a workspace", "import the latest changes", "add a directory to remote sync", "set a setting", "what schemas are in this database", "trigger a sync", "rescan field values", or anything hitting `metabase <verb>`.
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# metabase-cli

The official Metabase CLI (`metabase`) drives a Metabase instance over its REST API. It covers auth, list/get/create/update/delete on every resource, query and transform execution, content search, remote-sync (representations ↔ instance), Enterprise workspaces, and entity-id translation.

Top-level command groups (run `metabase <group> --help` to discover verbs):

```
auth | license | db | table | field | query | card | dashboard | snippet | segment | measure | collection | transform | transform-job
setting | search | sync | workspace | setup | api-key | eid
```

The general patterns below — auth, flag conventions, output flags, body input, common verb shapes — apply across **every** group. Two flows have enough surface to warrant their own reference files; load them on demand (see "Reference files" near the bottom).

## Auth & profiles

**The agent does not log in for the user.** Authentication is the human's job — they pick the base URL, paste credentials, and store them as a named profile under their own login. The agent's role is to *check* what profiles exist, *ask* which to use, and pass `--profile <name>` through every command.

**The one exception** is a freshly bootstrapped workspace child. The child's API credentials are minted by the parent the human already authorized; the agent reads them via `metabase workspace credentials <ws-id>` and saves them as a new profile non-interactively. This is the **only** legitimate place for the agent to call `auth login`. See `references/workspace.md` step 4 — and even there, pipe the key on stdin (`--api-key-stdin`), never on a flag value.

For everything else (parent profile, staging, prod, anything pointing at a Metabase the user has direct credentials for), follow the flow below.

### Discover what's already configured

```bash
metabase auth list --json                      # → {data: [{profile, url, present}], returned, total}
metabase auth status --json                    # → {profile, present, url} for the default profile
metabase auth status --profile <name> --json   # → status of a specific profile
```

`auth list` is the primary enumeration path — one call returns every configured profile with sanitized URL and `present` flag. Use it before asking the user which profile to pick. `auth status` is a single-profile probe; reach for it when you know the name and want a quick health check.

If `auth list` returns an empty `data: []` or the user has no profile set up, **stop and ask them to log in themselves**:

> Please run, yourself, `metabase auth login --url <your-base-url> --profile <name>`. Tell me the profile name when you're done.

Don't suggest a base URL, paste an API key, or run `auth login` on their behalf. Profile names are arbitrary local labels — `prod`, `staging`, the workspace name — let the user pick.

### Pick the profile to use

Run `metabase auth list --json` first. If exactly one profile is configured and the user's intent doesn't disambiguate, use it. If multiple profiles exist and the user hasn't named one, ask via `AskUserQuestion`, presenting the names from `auth list` as options. Once a name is established, pass `--profile <name>` to **every** subsequent command.

### Other secrets (license, warehouse passwords)

Same rule: the human runs the storing command. To check whether a license is present:

```bash
metabase license status --profile <name> --json   # → {present: bool}
```

If `present: false`, ask:

> Please run `echo "<your-token>" | metabase license set --profile <name>` from your terminal — don't paste the token in chat.

## Flag conventions (read once, internalize)

These trip up every fresh run.

### `--profile` is per-subcommand, not global

```bash
✅ metabase table list --profile prod --json
❌ metabase --profile prod table list           # → error: "Unknown command prod"
```

`--profile` attaches **after** the full verb chain (`table list`, `card get`, `workspace start`).

### When you do call `auth login` (workspace child only), pipe the key on stdin

The agent normally doesn't run `auth login` (see "Auth & profiles" — the human does). The one place it *does* — saving a workspace child's API key after `workspace credentials` — must use stdin, not a flag value:

```bash
✅ printf '%s' "$KEY" | metabase auth login --url <url> --api-key-stdin --profile <n> --json
❌ metabase auth login --api-key "$KEY" …       # → warns + rejects
```

Reason: shell history and process listings leak the value. The CLI rejects the flag form on purpose.

### `--wait` for async operations

`workspace start`, `workspace database provision`, `transform run`, and similar async verbs return immediately by default. Pass `--wait` for any interactive flow where the next step depends on completion. Without `--wait` you'll race the operation and see "not ready" / `state: starting` / transient connection refusals.

### Some outputs are JSON envelopes, not bare strings

A handful of "lookup" verbs return a JSON object even when you only want a single field. `metabase workspace url <id>` returns `{"workspace_id": ..., "url": "http://..."}`, not `"http://..."`. Don't drop them raw into another flag — extract:

```bash
WS_URL=$(metabase workspace url <id> --profile <n> --json | jq -r '.url')
```

If you find yourself writing `--url $(metabase ...)` and the receiving command rejects it with "URL must start with http://", this is what happened.

## Output

Every list/get verb supports the same output flags:

| Flag                | Effect                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------- |
| `--json`            | Emit full JSON envelope; safe for piping into `jq`. Default is human-readable text.         |
| `--full`            | Include every field (compact projection is the default for list/get).                       |
| `--fields a,b.c.d`  | Project specific dot-paths. Mutually exclusive with `--full`.                               |
| `--max-bytes <n>`   | Cap **list** output size (drops trailing items, sets `truncated`). Default 65 536; `0` disables. Single-item commands (`get`, `metadata`) never truncate — they only emit a stderr advisory when the body is over the cap. |

List envelope shape:

```json
{
  "data": [ /* items */ ],
  "returned": 10,
  "total": 42,
  "limit": 50,
  "truncated": false
}
```

Use `jq '.data[] | { ... }'` to slice it. The compact item projection is the agent-facing contract — for full Metabase fields, add `--full`.

`total` is best-effort and may be omitted or `null` — the server returns `null` for empty/permissions-filtered collections, and `--limit` early-stop omits it because the true total is unknown. Don't depend on it being a number; use `returned` for the count you actually got back and `data.length` for the rendered slice.

## Body input (create / update / run)

Verbs that take a payload accept it from one of four sources, **first non-empty wins**:

1. `--body '<inline JSON>'`
2. `--file <path>` — JSON file
3. stdin (auto-detected when piped, or explicit with `--stdin` on commands that support it)
4. positional argument

Picking exactly one is required; passing two of `--body` + `--file` + `--stdin` is rejected with a `ConfigError`.

Common pattern:

```bash
cat > /tmp/body.json <<'EOF'
{ ... }
EOF
metabase <noun> create --file /tmp/body.json --profile <n> --json
```

Heredoc with single-quoted `'EOF'` prevents shell from interpolating `$vars` inside the JSON.

## Discover the full surface: `metabase __manifest`

For the canonical, machine-readable inventory of every command — name, description, examples, every flag with type and default, and the output JSON Schema — run:

```bash
metabase __manifest
```

The leading `__` marks it as an internal command (hidden from `--help`), but it's stable: the build relies on it, and so do the in-repo tests. Reach for it instead of running `--help` per command when you need flag/output details. It pairs naturally with `jq`:

```bash
# Every command name:
metabase __manifest | jq -r '.commands[].command'

# Every verb under "transform":
metabase __manifest | jq -r '.commands[] | select(.command | startswith("transform")) | .command'

# Flags + types for `card query`:
metabase __manifest | jq '.commands[] | select(.command == "card query") | .args'

# Output schema for `card list` (so you know what to parse):
metabase __manifest | jq '.commands[] | select(.command == "card list") | .outputSchema'
```

Use it to (a) enumerate verbs you don't know by heart, (b) validate flag names before constructing a command, (c) read an output schema before parsing. Cheaper and more reliable than scraping `--help` text.

## Resources at a glance

The CLI exposes the Metabase REST API in 13 command groups beyond `auth` / `license`. Each follows the same shape (list/get/create/…); flags + output schemas are in `__manifest`. Only the deviations and quirks worth memorizing are below.

### `db` (alias `database`) — list and inspect databases

**Default agent traversal (granular, scales to real warehouses):**

```bash
metabase database list --profile <n> --json                             # discover db ids
metabase database schemas <db-id> --profile <n> --json                  # list schema names in one db
metabase database schema-tables <db-id> <schema> --profile <n> --json   # tables in ONE schema (compact)
metabase table get <table-id> --include fields --profile <n> --json     # fields for ONE table (see `table` section)
```

This is the path to use. A production Metabase typically has dozens of schemas, hundreds of tables, and dozens of fields per table — walking three levels and pulling one table's fields at a time keeps each response in the kilobytes. The rollup endpoints below pull megabytes and will blow the context window on any real warehouse.

**Other commands:**

```bash
metabase database list --saved --profile <n> --json                     # include the Saved Questions virtual db (id -1337)
metabase database get <db-id> --profile <n> --json                      # db record only (no tables)
metabase database sync-schema <db-id> --profile <n>                     # POST /sync_schema; queues async work, returns {status:"ok"}
metabase database rescan-values <db-id> --profile <n>                   # POST /rescan_values; queues async work, returns {status:"ok"}
```

**Rollup commands — only on small/dev warehouses:**

```bash
metabase database list --include tables --profile <n> --full --json                    # every db with its full table list
metabase database get <db-id> --include tables.fields --profile <n> --full --json      # one db, every table, every field
metabase database metadata <db-id> --profile <n> --full --json                         # alias for the above, server-rolled
```

Reach for these only when you know the db is small (a seeded dev instance, a sample db, a freshly-bootstrapped test fixture) or when you genuinely need every column of every table in one shot. On a real warehouse the response will exceed the agent context — use the granular traversal instead.

`sync-schema` / `rescan-values` are the two manual triggers admins reach for after warehouse-side changes; both queue work and return immediately.

### `table` — list and inspect tables

```bash
metabase table list --db-id <db-id> --profile <n> --json                # all tables in a db (compact, no fields)
metabase table get <table-id> --profile <n> --json                      # table-level metadata only
metabase table get <table-id> --include fields --profile <n> --json     # bundles compact-projected fields  ← default for field-listing
metabase table fields <table-id> --profile <n> --json                   # just the fields, as a list envelope
metabase table metadata <table-id> --profile <n> --json                 # fields + FKs + dimensions hydrated (heavier)
```

`table get` hits `/api/table/:id` and never returns fields on its own — `--full` only widens the projection over the already-fetched object. Pass `--include fields` for the field shape needed to author a card, transform, or measure; the hydrated path goes through `/api/table/:id/query_metadata`. Use `table fields` when you want just the field array (no surrounding table metadata) and `table metadata` only when you also need FKs and dimensions hydrated.

`table list --db-id <db-id>` returns every table across every schema as a flat compact list. On a real warehouse with hundreds of tables this is still smaller than `database get --include tables.fields`, but `database schema-tables <db-id> <schema>` is the right starting point when you know which schema you want.

### `field` — single field detail

```bash
metabase field get <field-id> --profile <n> --full --json
```

No `list` — fields are per-table, so use `table get <table-id> --include fields` (compact) or `table fields <table-id>` (list envelope). Never try to enumerate fields across an entire database — that's what blows up the context.

### `query` — run ad-hoc MBQL with pre-flight validation

```bash
metabase query --print-schema --profile <n> > /tmp/mbql.json    # fetch the JSON Schema
metabase query --file q.json --dry-run --profile <n>            # validate, no network
metabase query --file q.json --profile <n> --json               # validate + run
```

The canonical agent-side path for ad-hoc MBQL. Three modes:

- `--print-schema` — emits `{ mode, schema, defs }` where `defs` carries `id.yaml` / `parameter.yaml` / `ref.yaml` / `temporal_bucketing.yaml` keyed by the path used in the schema's `$ref`s. Use this **first** when authoring a non-trivial query — it's cheaper than guess-and-fail.
- `--dry-run` — validates and emits `{ ok, errors: [{path, message}] }`. Exit 0 if valid, 2 if not. No request sent.
- run (no flag) — validates, then on success runs the query. On validation failure: same envelope on stdout, exit 2, **never sends** the request.

Two MBQL flavors. Default is **internal** (numeric IDs: `database: 1`, `source-table: 7`). Pass `--external` for string-FK form (`database: "My DB"`, `source-table: ["My DB", null, "orders"]`). `--print-schema` defaults to internal too; pair with `--external` for the FK-form schema.

Validation error envelope (same shape across `query`, `card create`, `transform create/update`):

```json
{ "ok": false, "errors": [{ "path": "/stages/0/aggregation/0", "message": "must be array" }] }
```

`path` is a JSON Pointer into the body, `message` is the validator error string. Iterate against `--dry-run` until `ok: true`, then drop `--dry-run` to run.

Exit codes: `0` valid + ran, `2` validation failed / malformed body, `1` server-side error after a valid pre-flight.

**`--skip-validate`** is an escape hatch: bypasses the pre-flight and sends the body as-is. Use only when the bundled schema disagrees with what the server actually accepts (drift, false negative). Mutually exclusive with `--dry-run`. Same flag works on `metabase card create` and `metabase transform create / update`.

**MBQL 5 clause shape — opts always second.** Every clause is `[op, {options}, ...args]`: options object is the **second** element, not the third. Field refs are `["field", {options}, fieldId]` (id third), not the legacy MBQL 4 shape `["field", id, opts]`. The same `[op, {options}, …]` rule applies to aggregations (`["count", {options}]`, `["sum", {options}, <expr>]`), filters (`["=", {options}, <a>, <b>]`), order-by (`["asc", {options}, <expr>]`), and every other clause. Slot-1 violations surface from `--dry-run` as `must be the field options object` / `must be the clause options object` at `/stages/0/<verb>/<n>/1`.

### `uuid` — mint UUID v4 strings for `lib/uuid` slots

```bash
metabase uuid                          # one UUID, v4 from crypto.randomUUID
metabase uuid --count 5                # five UUIDs (one per line in TTY, JSON when piped)
metabase uuid --count 5 --json         # ["uuid1", "uuid2", …]
```

**Hard rule for agents: never generate, invent, hard-code, or reuse UUID values.** Always call `metabase uuid` for fresh UUIDs at the moment you need them. Do not copy UUIDs from documentation examples, prior conversations, prior queries you authored, or anywhere else — every `lib/uuid` slot gets a freshly-minted value. The bundled schema enforces RFC 4122 format strictly, so placeholder strings (`"a1"`, `"uuid-1"`, `"agg-uuid-001"`, …) fail pre-flight with `must be a UUID v4 (RFC 4122) — run \`metabase uuid\` …`. The same rule applies to native template-tag `id` fields, parameter ids, and any other `format: "uuid"` slot.

Workflow when assembling an MBQL 5 body:

1. Count the `lib/uuid` slots you need (one per clause options object, plus aggregation-ref ↔ aggregation pairings — those two share the same string).
2. `metabase uuid --count <N> --json` — mint exactly that many in one call.
3. Substitute each minted value into its slot as you build the JSON.

Aggregation-ref pairing: the `["aggregation", {options}, "<uuid>"]` ref's third arg must equal the target aggregation's own `lib/uuid` (string equality). Mint the aggregation's `lib/uuid` once, then reuse that *same minted value* for the ref — that's the only legitimate "reuse" pattern, and it's intra-body, not across bodies or sessions.

### `card` — questions, models, metrics

```bash
metabase card list  --profile <n> --json
metabase card get  <id> --profile <n> --full --json
metabase card query <id> --profile <n> --json --limit 50
metabase card query <id> --profile <n> --export-format csv  > /tmp/results.csv
metabase card query <id> --profile <n> --export-format xlsx > /tmp/results.xlsx
metabase card query <id> --profile <n> --parameters '[{"type":"category","value":"A","target":["variable",["template-tag","c"]]}]'
metabase card create --file body.json --profile <n> --json
metabase card update <id> --body '{"name":"renamed"}' --profile <n> --json
metabase card update <id> --body '{"display":"bar"}' --profile <n> --json
metabase card update <id> --body '{"archived":false}' --profile <n> --json    # unarchive
metabase card archive <id> --profile <n>                    # soft-delete; not undoable from the CLI
```

`--export-format csv|xlsx` bypasses the JSON envelope and streams the raw export — pipe to a file. There is no permanent-delete; `archive` is the only delete verb (and `update --body '{"archived":false}'` is the unarchive path).

**`card update <id>`** patches a partial subset of the create shape (`name`, `display`, `dataset_query`, `visualization_settings`, `description`, `archived`, `collection_id`, `dashboard_id`, `cache_ttl`, `parameters`, `parameter_mappings`, …). Only the keys you send are touched. If `dataset_query` is MBQL 5 (`lib/type: "mbql/query"`) it goes through the same pre-flight validation as `card create` and `metabase query`; pass `--skip-validate` to bypass.

**MBQL 5 `dataset_query` is a *flat* `mbql/query`, not a legacy envelope.** This is the most common authoring mistake — the legacy MBQL4 shape `{type:"query", database:N, query:{...}}` looks similar but the server *will silently double-wrap* an MBQL5 body submitted that way (you'll see the second-level `stages` nested inside an outer empty stage on `card get`), and queries fail with `"Initial MBQL stage must have either :source-table or :source-card"`. The right shape:

```json
{
  "name": "Total shipments",
  "display": "scalar",
  "collection_id": 8,
  "dataset_query": {
    "lib/type": "mbql/query",
    "database": 2,
    "stages": [
      { "lib/type": "mbql.stage/mbql", "source-table": 190,
        "aggregation": [["count", {"lib/uuid": "<mint via `metabase uuid`>"}]] }
    ]
  },
  "visualization_settings": {}
}
```

`dataset_query` is the mbql/query value itself — no `type:"query"` envelope, no `query:` nesting.

**MBQL 5 pre-flight on `card create` / `card update`:** when `dataset_query` has `lib/type: "mbql/query"`, the body is validated against the same schema as `metabase query` before sending. On failure, exit 2 with the standard `{ ok, errors }` envelope on stdout. Legacy `dataset_query` shapes (MBQL 4, native) skip pre-flight. The pre-flight also rejects the double-wrap mistake above (MBQL 5 nested inside a legacy `{type:"query", query:…}` envelope) with a `ConfigError` pointing at the right shape — no `--skip-validate` will get that past pre-flight. Author MBQL 5 by fetching the schema via `metabase query --print-schema` and iterating with `metabase query --dry-run`. Pass `--skip-validate` to bypass the pre-flight on schema-shape disagreements and let the server be the authority.

**Visualization settings.** The valid keys for `visualization_settings` are scoped by the card's `display` value (`scalar`, `bar`, `line`, `area`, `combo`, `pie`, `table`, `pivot`, `row`, `waterfall`, `scatter`, `boxplot`, …). The CLI does not validate this object client-side — the schema lives in the **`metabase-representation-format`** skill, `spec.md` "Visualization Settings" section (graph / series / table / pivot / pie / scalar subsections, plus common `column_settings`). Load that skill if it isn't active when authoring viz keys. Common keys you'll reach for:

- `bar` / `line` / `area` / `combo` / `scatter` / `waterfall` / `row` / `boxplot`: `graph.dimensions`, `graph.metrics`, `graph.show_values`, `graph.x_axis.title_text`, `graph.y_axis.title_text`, `graph.show_goal`, `graph.goal_value`, `stackable.stack_type`, plus per-series settings (`series_settings`).
- `pie`: `pie.dimension`, `pie.metric`, `pie.show_total`, `pie.percent_visibility`, `pie.show_legend`.
- `scalar`: `scalar.prefix`, `scalar.suffix`, `scalar.decimals`, plus `column_settings` for number formatting on the displayed column.
- `table`: `table.columns` (order + visibility), `table.column_formatting` (conditional formatting), `column_settings` for per-column display.
- `pivot`: `pivot_table.column_split` (rows / columns / values), `pivot.show_row_totals`, `pivot.show_column_totals`.

Empty `{}` is always valid; defaults apply.

### `dashboard` — dashboards and dashcards

```bash
metabase dashboard list   --profile <n> --json
metabase dashboard list   --filter archived --profile <n> --json
metabase dashboard get    <id> --profile <n> --full --json    # --full hydrates dashcards + tabs
metabase dashboard cards  <id> --profile <n> --json           # list of dashcards on the dashboard
metabase dashboard create --file body.json --profile <n> --json
metabase dashboard create --body '{"name":"D","dashcards":[{"id":-1,"card_id":42,"row":0,"col":0,"size_x":12,"size_y":6}]}' --profile <n> --json
metabase dashboard update <id> --body '{"name":"renamed"}' --profile <n> --json
metabase dashboard update-dashcard <dashboard-id> <dashcard-id> --body '{"row":4,"col":2}' --profile <n> --json
```

A "dashcard" is a card placement on a dashboard — its own id, position (`row`/`col`), and size (`size_x`/`size_y`). Dashcards are nested inside the parent dashboard's response; the API has no per-dashcard endpoint, so dashcard edits round-trip through `PUT /api/dashboard/:id`.

A dashcard's `visualization_settings` overrides the underlying card's — same key list as the `card` section above. Dashcards can additionally set `click_behavior` for cell-level navigation; see the `metabase-representation-format` skill's "Click Behavior" subsection for that schema.

**`dashboard create` accepts `dashcards` and `tabs` in the body.** The create endpoint itself only sets dashboard metadata (name, description, collection, parameters); when the body carries `dashcards` or `tabs`, the CLI chains a `PUT /api/dashboard/:id` automatically and renders the hydrated dashboard back. The compact projection includes the resulting `dashcards` and `tabs` arrays (each entry projected to id / position / size / card_id / tab_id), so the agent can confirm the placements landed without a second call. Use `--full` to also see dashboard-level metadata (width, embedding flags, parameters, …). Use a negative id (`-1`, `-2`, …) for new dashcards.

**Card-reference pre-flight on `dashboard create` / `dashboard update`.** Before either command sends anything, every positive `card_id` referenced from `dashcards` is checked against `GET /api/card/:id` in parallel (de-duplicated per id). Cards that don't exist, are archived, or aren't readable fail pre-flight: the CLI writes a `{ok:false, errors:[{path, message}]}` envelope to stdout (one entry per offending dashcard, `path` = JSON pointer like `/dashcards/3/card_id`) and exits **2** with `dashboard card-reference pre-flight failed: N error(s) — fix the dashcard card_id values listed above` on stderr. No dashboard is created or modified on a pre-flight miss — this is the contract that eliminates orphan dashboards from chained creates. The pre-flight is non-bypassable: it queries live server state (no bundled schema), so there is no `--skip-validate` escape hatch. If pre-flight rejects something you believe is valid, the input is stale — `card list --json` to confirm, then re-author.

**Chained-PUT failures call out the orphan risk explicitly.** If the chained `PUT /api/dashboard/:id` fails after the `POST /api/dashboard` already created the row (rare with pre-flight, but possible on permission / 5xx / network mid-flight), the user-facing error becomes `dashboard <id> created but follow-up PUT /api/dashboard/<id> failed: <reason>; dashcards not applied`. Recovery: `metabase dashboard get <id>` to confirm the empty row, then either `dashboard update <id> --body '{"dashcards":[...]}'` to retry the dashcards, or `dashboard update <id> --body '{"archived":true}'` to archive the orphan. Split-into-two recipe for debugging: `dashboard create` with a metadata-only body, then `dashboard update <id>` with the `dashcards` array — isolates which leg of the chain is at fault.

Two ways to edit dashcards:

- **`dashboard update <id> --body { "dashcards": [...] }`** — replaces the entire dashcard set. IDs in the array are kept (and updated to the values you send); IDs **absent** are deleted server-side. Use a negative id (`-1`, `-2`, …) for cards the server should create. You must include every existing dashcard you want to preserve.
- **`dashboard update-dashcard <dashboard-id> <dashcard-id>`** — patches a single dashcard's layout / settings without touching the others. Internally: GET dashboard → merge patch into the targeted dashcard → PUT the whole array. Safer than hand-rolling the full-array variant if you only meant to nudge one card.

`dashboard list` is a thin filter helper (`--filter all|mine|archived`; default `all`). The list endpoint omits `dashcards` / `tabs`; `dashboard get <id>` includes them as compact projections, and `dashboard get <id> --full` (or `dashboard cards <id>`) gives the full hydrated form.

Patch fields supported by `update-dashcard`:

| Field                                       | Type                               |
| ------------------------------------------- | ---------------------------------- |
| `row`, `col`                                | non-negative integer               |
| `size_x`, `size_y`                          | positive integer                   |
| `dashboard_tab_id`                          | integer or `null`                  |
| `parameter_mappings`                        | array of parameter-mapping objects |
| `inline_parameters`                         | array of strings                   |
| `visualization_settings`                    | object                             |

Empty-object patches are rejected client-side before any network call.

### `snippet` — native query snippets (reusable SQL fragments)

```bash
metabase snippet list  --profile <n> --json
metabase snippet list  --archived --profile <n> --json   # → ONLY archived (mutually exclusive with active)
metabase snippet get   <id> --profile <n> --full --json
metabase snippet create --body '{"name":"active","content":"WHERE active = true"}' --profile <n> --json
metabase snippet update <id> --body '{"name":"renamed"}' --profile <n> --json
metabase snippet update <id> --body '{"archived":false}' --profile <n> --json   # unarchive
metabase snippet archive <id> --profile <n>                                     # soft-delete
```

Hits `/api/native-query-snippet`. A snippet is a named, reusable piece of native (SQL) query text — referenced from cards via `{{snippet: Name}}`. **`--archived` is a swap, not a union**: list returns either active (default) or archived rows, never both. Compact projection: `id`, `name`, `description`, `archived`, `collection_id`. Create body required fields: `name`, `content`. Update body is partial — `name`, `content`, `description`, `archived`, `collection_id`.

### `segment` — saved MBQL filter macros

```bash
metabase segment list  --profile <n> --json
metabase segment get   <id> --profile <n> --full --json
metabase segment create --file segment.json --profile <n> --json
metabase segment update <id> --body '{"name":"renamed","revision_message":"rename"}' --profile <n> --json
metabase segment archive <id> --profile <n>                                                # default audit message
metabase segment archive <id> --revision-message "deprecated" --profile <n>                # custom audit message
```

Hits `/api/segment`. A segment is a saved MBQL filter macro tied to a table — used in card filters to share a reusable predicate. Create body required: `name`, `table_id`, `definition` (MBQL filter object), optional `description`. **Update bodies MUST include `revision_message`** (a non-blank string captured in the audit log); the CLI does not synthesize it. The `archive` verb hardcodes `"Archived via metabase CLI"` by default — override with `--revision-message`.

Compact projection: `id`, `name`, `description`, `archived`, `table_id`. The list response is bare; only the get/list responses hydrate `creator` and (list-only) `definition_description`.

### `measure` — saved MBQL aggregation macros

```bash
metabase measure list  --profile <n> --json
metabase measure get   <id> --profile <n> --full --json
metabase measure create --file measure.json --profile <n> --json
metabase measure update <id> --body '{"name":"renamed","revision_message":"rename"}' --profile <n> --json
metabase measure archive <id> --profile <n>
metabase measure archive <id> --revision-message "deprecated" --profile <n>
```

Hits `/api/measure`. A measure is a saved MBQL aggregation (a single `:aggregation` clause) tied to a table — referenced from cards and metrics to share a reusable computation. Create body required: `name`, `table_id`, `definition` (MBQL aggregation object), optional `description`. Same `revision_message` requirement on update / archive as `segment`.

Compact projection: `id`, `name`, `description`, `archived`, `table_id`. The full response on `get` adds `dimensions`, `dimension_mappings`, `result_column_name`; the list response adds `definition_description` instead.

### `collection` — folder hierarchy for cards, dashboards, sub-collections

```bash
metabase collection list   --profile <n> --json
metabase collection list   --filter archived  --profile <n> --json     # → just the trash collection
metabase collection list   --filter personal  --profile <n> --json     # → only personal collections
metabase collection get    <ref> --profile <n> --json --full
metabase collection items  <ref> --profile <n> --json
metabase collection items  <ref> --models card,dashboard --pinned-state is_pinned --profile <n> --json
metabase collection tree   --profile <n>                                # → JSON only, recursive
metabase collection create --body '{"name":"My Collection","parent_id":4}' --profile <n> --json
```

`<ref>` (the positional id on `get` and `items`) accepts **four** forms — anything else is rejected client-side with a `ConfigError` before any HTTP call:

| Form                  | Example                  | Notes                                                                                                                  |
| --------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Positive integer      | `4`                      | Database id of the collection.                                                                                         |
| `root`                | `metabase collection get root` | The virtual "Our analytics" root. Returns a stripped-down shape — `archived`, `description`, `location`, `type`, etc. are *absent*, not `null`. |
| `trash`               | `metabase collection get trash` | The trash collection — paradoxically returns `archived: false`, `type: "trash"`. Filter via `list --filter archived` to enumerate it.        |
| 21-char entity_id     | `voo1If9y8Sld0lXej6xl0`  | NanoID form (regex `^[A-Za-z0-9_-]{21}$`). Works wherever an int does — Metabase resolves it server-side via the same route. |

**`collection items` is auto-paginated.** The CLI drains all pages of `/api/collection/:id/items` by default; pass `--limit <n>` to cap the total returned. With `--limit` set, the result envelope omits `total` (true total is unknown after early-stop). Items at the root level (`collection items root`) carry `collection_id: null`.

**`collection tree` is JSON-only.** The recursive `{id, name, location, here, children, …}` structure does not render meaningfully as a key/value table; passing `--format text` is rejected with `ConfigError` so the user gets a clear signal rather than silent JSON.

**Compact projection** (default for `list` / `get`): `id`, `name`, `description`, `archived`, `location`, `parent_id`, `type`, `authority_level`, `is_personal`. Use `--full` for hydrated fields like `slug`, `entity_id`, `can_write`, `namespace`, `personal_owner_id`. The compact projection on items is even tighter: `id`, `model`, `name`, `description`, `archived`, `collection_id`.

**`collection create` body** accepts the same fields as `POST /api/collection`: `name` (required, non-empty), `description`, `parent_id` (omit or `null` for the root), `namespace`, `authority_level`. Note: the create response does *not* hydrate `parent_id` (only `location` reflects the parent path); use `collection get <id>` if you need `parent_id` populated.

For dashboard / card / collection enumeration, prefer the dedicated `collection list` / `dashboard list` / `card list` verbs over `metabase search --models collection` — search is for ranking against a query string or cross-resource lookup, not bulk enumeration.

### `transform` and `transform-job`

```bash
metabase transform list --profile <n> --json
metabase transform run <id> --wait --profile <n> --json
metabase transform runs --transform-id <id> --profile <n> --json   # recent runs, optionally filtered
metabase transform get-run <run-id> --profile <n> --json            # single run by RUN id (not transform id)
metabase transform cancel <id> --profile <n> --json                 # cancel the in-flight run for a transform
metabase transform-job list --profile <n> --json
```

**MBQL 5 pre-flight on `transform create` / `update`:** when `source.query` has `lib/type: "mbql/query"`, it's validated against the same schema as `metabase query` before sending; failures exit 2 with the standard `{ ok, errors }` envelope on stdout. Legacy `source.query` shapes and Python sources skip pre-flight. Pass `--skip-validate` to bypass.

**Iterate via `transform update`, not re-`create`.** When a `transform run` fails and you want to retry with a fixed body, patch the existing transform with `transform update <id> --file new-body.json` rather than `transform delete <id>` + `transform create`. Update keeps the same row, `entity_id`, materialized table, and on-disk YAML filename — `sync export` produces one clean commit, and you avoid the `_2` suffix the YAML serializer mints when two same-named transforms exist on disk. See `references/transform.md` "Iterating on a failing transform".

For the body shape, run-with-wait pattern, schedule authoring, and inspection see `references/transform.md`.

### `setting` (alias `settings`) — admin settings

```bash
metabase setting list --profile <n> --json                          # admin-only
metabase setting get <key> --profile <n> --json
metabase setting set <key> --body '"<string-value>"' --profile <n>  # value parsed as STRICT JSON
```

The value is parsed as strict JSON: a string setting is `'"value"'` (note the inner double quotes), not `value`. Booleans are `true` / `false`, numbers bare. Wrong quoting silently produces a parse error — confirm with `setting get <key>` after.

**`setting get --json` works on every value type.** String-valued settings (e.g., `remote-sync-branch=agent/shipments-analysis`, `remote-sync-url=file:///mnt/repo`) come back from `/api/setting/<key>` as bare text rather than a JSON-quoted string; the CLI sniffs the response Content-Type and wraps bare text into the `{key, value}` envelope so `--json` is uniform. The same fix applies to `sync status --json` (which reads `remote-sync-branch` internally).

### `search` — content search across types

```bash
metabase search "orders" --profile <n> --json
metabase search "orders" --models card,dashboard --limit 10 --profile <n> --json
metabase search "drafts" --archived --verified --profile <n> --json
metabase search "orders" --table-db-id <db-id> --profile <n> --json
```

`--models` filters: `card,dataset,metric,dashboard,collection,database,table,segment,measure,snippet,document,action,transform,indexed-entity`. For plain enumeration / inspection of cards, dashboards, or collections, prefer the dedicated `card list` / `dashboard list` / `collection list` verbs above; reach for `search --models <kind>` only when you need ranking against a query string or a cross-resource lookup.

### `sync` — remote-sync (representations ↔ instance)

```bash
metabase sync status   --profile <n> --json
metabase sync import   --branch <branch> --profile <n>     # --wait is the default
metabase sync export   -m "commit message" --profile <n>
metabase sync branches --profile <n> --json
```

14 verbs (status / is-dirty / has-remote-changes / dirty / current-task / cancel-task / wait / import / export / stash / branches / create-branch / add-collection / remove-collection). Both `import --force` and `export --force` are **lossy** — confirm with the user before either. `add-collection <id>` / `remove-collection <id>` toggle a collection's `is_remote_synced` and cascade to descendants by location prefix; the server rejects them in the default read-only mode (`metabase setting set remote-sync-type '"read-write"'` first). For the dirty-check workflow, stash semantics, and the full collection-toggle prerequisites, see `references/sync.md`.

### `workspace` — Enterprise workspaces (parent-side + local child)

Lifecycle, provisioning, child-credential extraction, diagnose. See `references/workspace.md` — it's the densest reference and assumes the conventions above.

### `api-key` — create API keys

```bash
metabase api-key create --body '{"name":"agent-demo","group_id":<id>}' --profile <n> --json
```

Admin-only. The response includes the unmasked key once — capture it; the API never reveals it again.

### `eid translate` — string EID → numeric id

```bash
metabase eid translate <eid> --profile <n> --json
```

Useful when an external system gives you a string entity id (like `Nd3A2qlmFIOYa5UZpQdsL`) and you need the numeric id for `card query`, `transform run`, etc.

### `setup` — initial setup wizard

```bash
metabase setup --file /path/to/setup-spec.json
```

Walks the `/api/setup` endpoint with a default user. **Don't run this against an instance the user already set up** — it errors out, and even successful runs are one-shot. Mostly useful for bootstrapping a fresh local instance (e2e harnesses).

## Reference files (load on demand)

The main SKILL.md is enough for any single-command task. Specialized flows live in `references/`. **Read the relevant file proactively when the user's intent matches** — don't wing the workspace lifecycle, transform body, or sync workflow from this overview alone.

| Read this file            | When the user's intent matches                                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| `references/workspace.md` | "spin up a workspace", "provision", "start a local Metabase against my prod", anything `metabase workspace …`. **Mandatory** before running `workspace start` — it tells you to ask the user about Remote Sync (current dir / custom path / none) up front, since the bind mount can only be set at container create. |
| `references/transform.md` | "create a transform", "run a transform", authoring transform body JSON, run inspection                |
| `references/sync.md`      | "import the latest changes", "export to git", "remote sync", "dirty check", "stash before pulling"   |

If a task spans more than one (e.g., "spin up `my_ws`, sync transforms from `main`, run them"), read each. Reference files assume you've internalized the general flag conventions above and won't repeat them.

## Don't

- **Don't run `metabase auth login` for the user.** Authentication is theirs — ask them to log in and tell you the profile name. The only legitimate exception is saving a freshly created workspace child's credentials (see `references/workspace.md`); even there, pipe the key on stdin.
- Don't paste credentials, license tokens, or warehouse passwords in chat. Have the user run the storing command themselves.
- Don't put `--profile` before the verb chain — the CLI parses it as a top-level subcommand and errors out.
- Don't pass an API key with `--api-key "$KEY"`; pipe it on stdin via `--api-key-stdin`. (Comes up only in the workspace-child case.)
- Don't omit `--wait` on `workspace start` / `transform run` / `workspace database provision` for interactive flows; the next step will race the operation.
- Don't drop a JSON-envelope verb's output raw into another flag. Extract with `--json | jq -r '.<field>'`.
- Don't add a third-party HTTP library or shell into `curl` workflows when a `metabase <verb>` exists — the CLI is the supported path; `curl` against `/api/...` bypasses retries, schema validation, and credential redaction.
