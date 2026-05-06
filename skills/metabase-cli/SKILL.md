---
name: metabase-cli
description: Drive a Metabase instance from the command line via the official `metabase` CLI — authenticate with profiles, run ad-hoc MBQL queries with built-in pre-flight validation, list and run cards (questions, models, metrics), list/get/create/update dashboards and patch their dashcards, author and run transforms, schedule transform jobs, inspect databases/tables/fields, search content (cards, dashboards, collections, transforms, snippets, metrics), read and write admin settings, sync content to and from a remote git repo (import, export, branches, stash, dirty checks), manage Enterprise workspaces (lifecycle and database provisioning), create API keys, translate entity ids. Use whenever the user wants to interact with a Metabase from the terminal: "log into metabase", "run an MBQL query", "validate this query", "list cards", "run card 42 as CSV", "create a transform", "list dashboards", "move a dashcard", "search metabase for X", "import the latest changes", "spin up a workspace", "set a setting", or anything hitting `metabase <verb>`.
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# metabase-cli

The official Metabase CLI (`metabase`) drives a Metabase instance over its REST API. It covers auth, list/get/create/update/delete on every resource, query and transform execution, content search, remote-sync (representations ↔ instance), Enterprise workspaces, and entity-id translation.

Top-level command groups (run `metabase <group> --help` to discover verbs):

```
auth | license | db | table | field | query | card | dashboard | transform | transform-job
setting | search | sync | workspace | setup | api-key | eid
```

The general patterns below — auth, flag conventions, output flags, body input, common verb shapes — apply across **every** group. Two flows have enough surface to warrant their own reference files; load them on demand (see "Reference files" near the bottom).

## Auth & profiles

**The agent does not log in for the user.** Authentication is the human's job — they pick the base URL, paste credentials, and store them as a named profile under their own login. The agent's role is to *check* what profiles exist, *ask* which to use, and pass `--profile <name>` through every command.

**The one exception** is a freshly bootstrapped workspace child. The child's API credentials are minted by the parent the human already authorized; the agent reads them via `metabase workspace credentials <ws-id>` and saves them as a new profile non-interactively. This is the **only** legitimate place for the agent to call `auth login`. See `references/workspace.md` step 4 — and even there, pipe the key on stdin (`--api-key-stdin`), never on a flag value.

For everything else (parent profile, staging, prod, anything pointing at a Metabase the user has direct credentials for), follow the flow below.

### Discover what's already configured

```bash
metabase auth status --json                    # → {profile, present, url} for the default profile
metabase auth status --profile <name> --json   # → status of a specific profile
```

If `present: false` or the user has no profile set up, **stop and ask them to log in themselves**:

> Please run, yourself, `metabase auth login --url <your-base-url> --profile <name>`. Tell me the profile name when you're done.

Don't suggest a base URL, paste an API key, or run `auth login` on their behalf. Profile names are arbitrary local labels — `prod`, `staging`, the workspace name — let the user pick.

### Pick the profile to use

If multiple profiles exist and the user hasn't named one, ask via `AskUserQuestion`. Once a name is established, pass `--profile <name>` to **every** subsequent command.

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
| `--max-bytes <n>`   | Cap output size; `0` disables. Default 65 536.                                              |

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

```bash
metabase database list --profile <n> --json
metabase database get <db-id> --profile <n> --full --json
```

Read-only. Returns the `database_id` you need for `table list`, `card create`, `transform create`, etc.

### `table` — list and inspect tables

```bash
metabase table list --db-id <db-id> --profile <n> --json
metabase table get <table-id> --profile <n> --full --json    # bundles fields
```

To enumerate the schemas the parent already syncs for a database:
```bash
metabase table list --db-id <db-id> --profile <n> --json | jq -r '[.data[].schema] | unique | .[]'
```

### `field` — single field detail

```bash
metabase field get <field-id> --profile <n> --full --json
```

No `list` — fields come bundled with `table get`.

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

### `card` — questions, models, metrics

```bash
metabase card list  --profile <n> --json
metabase card get  <id> --profile <n> --full --json
metabase card query <id> --profile <n> --json --limit 50
metabase card query <id> --profile <n> --export-format csv  > /tmp/results.csv
metabase card query <id> --profile <n> --export-format xlsx > /tmp/results.xlsx
metabase card query <id> --profile <n> --parameters '[{"type":"category","value":"A","target":["variable",["template-tag","c"]]}]'
metabase card create --file body.json --profile <n> --json
metabase card archive <id> --profile <n>                    # soft-delete; not undoable from the CLI
```

`--export-format csv|xlsx` bypasses the JSON envelope and streams the raw export — pipe to a file. There is no permanent-delete; `archive` is the only delete verb.

**MBQL 5 pre-flight on `card create`:** when `dataset_query` has `lib/type: "mbql/query"`, the body is validated against the same schema as `metabase query` before sending. On failure, exit 2 with the standard `{ ok, errors }` envelope on stdout. Legacy `dataset_query` shapes (MBQL 4, native) skip pre-flight. Author MBQL 5 by fetching the schema via `metabase query --print-schema` and iterating with `metabase query --dry-run`.

### `dashboard` — dashboards and dashcards

```bash
metabase dashboard list   --profile <n> --json
metabase dashboard list   --filter archived --profile <n> --json
metabase dashboard get    <id> --profile <n> --full --json    # --full hydrates dashcards + tabs
metabase dashboard cards  <id> --profile <n> --json           # list of dashcards on the dashboard
metabase dashboard create --file body.json --profile <n> --json
metabase dashboard update <id> --body '{"name":"renamed"}' --profile <n> --json
metabase dashboard update-dashcard <dashboard-id> <dashcard-id> --body '{"row":4,"col":2}' --profile <n> --json
```

A "dashcard" is a card placement on a dashboard — its own id, position (`row`/`col`), and size (`size_x`/`size_y`). Dashcards are nested inside the parent dashboard's response; the API has no per-dashcard endpoint, so dashcard edits round-trip through `PUT /api/dashboard/:id`.

Two ways to edit dashcards:

- **`dashboard update <id> --body { "dashcards": [...] }`** — replaces the entire dashcard set. IDs in the array are kept (and updated to the values you send); IDs **absent** are deleted server-side. Use a negative id (`-1`, `-2`, …) for cards the server should create. You must include every existing dashcard you want to preserve.
- **`dashboard update-dashcard <dashboard-id> <dashcard-id>`** — patches a single dashcard's layout / settings without touching the others. Internally: GET dashboard → merge patch into the targeted dashcard → PUT the whole array. Safer than hand-rolling the full-array variant if you only meant to nudge one card.

`dashboard list` is a thin filter helper (`--filter all|mine|archived`; default `all`). The list endpoint omits `dashcards` / `tabs` — use `dashboard get <id> --full` (or `dashboard cards <id>`) to inspect them.

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

### `transform` and `transform-job`

```bash
metabase transform list --profile <n> --json
metabase transform run <id> --wait --profile <n> --json
metabase transform-job list --profile <n> --json
```

**MBQL 5 pre-flight on `transform create` / `update`:** when `source.query` has `lib/type: "mbql/query"`, it's validated against the same schema as `metabase query` before sending; failures exit 2 with the standard `{ ok, errors }` envelope on stdout. Legacy `source.query` shapes and Python sources skip pre-flight.

For the body shape, run-with-wait pattern, schedule authoring, and inspection see `references/transform.md`.

### `setting` (alias `settings`) — admin settings

```bash
metabase setting list --profile <n> --json                          # admin-only
metabase setting get <key> --profile <n> --json
metabase setting set <key> --body '"<string-value>"' --profile <n>  # value parsed as STRICT JSON
```

The value is parsed as strict JSON: a string setting is `'"value"'` (note the inner double quotes), not `value`. Booleans are `true` / `false`, numbers bare. Wrong quoting silently produces a parse error — confirm with `setting get <key>` after.

### `search` — content search across types

```bash
metabase search "orders" --profile <n> --json
metabase search "orders" --models card,dashboard --limit 10 --profile <n> --json
metabase search "drafts" --archived --verified --profile <n> --json
metabase search "orders" --table-db-id <db-id> --profile <n> --json
```

`--models` filters: `card,dataset,metric,dashboard,collection,database,table,segment,measure,snippet,document,action,transform,indexed-entity`. For plain dashboard enumeration / inspection, prefer the dedicated `dashboard list` / `dashboard get` verbs above; reach for `search --models dashboard` only when you need ranking against a query string or a cross-resource lookup.

### `sync` — remote-sync (representations ↔ instance)

```bash
metabase sync status   --profile <n> --json
metabase sync import   --branch <branch> --profile <n>     # --wait is the default
metabase sync export   -m "commit message" --profile <n>
metabase sync branches --profile <n> --json
```

12 verbs (status / is-dirty / has-remote-changes / dirty / current-task / cancel-task / wait / import / export / stash / branches / create-branch). Both `import --force` and `export --force` are **lossy** — confirm with the user before either. For the dirty-check workflow and stash semantics, see `references/sync.md`.

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
