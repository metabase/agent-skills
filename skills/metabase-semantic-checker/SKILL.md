---
name: metabase-semantic-checker
description: Runs the Metabase semantic checker against a tree of Representation Format YAML files to verify that all references resolve — cross-entity references (collection_id, dashboard_id, parent_id, parameter source cards, snippet references, transform tags, etc.) and references to columns inside MBQL and native queries. Use when the user asks to "semantic check", "check references", "validate queries against the schema", or diagnose a broken reference. Requires database metadata on disk (by default `.metabase/metadata.json`).
model: opus
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

## Metabase semantic checker

The semantic checker validates a tree of **Metabase Representation Format** YAML files for referential integrity. Schema-level validation (shape of each file, required fields, enum values) is handled separately by `npx @metabase/representations validate-schema`; the semantic checker runs *after* schema validation and focuses on cross-file and cross-system consistency.

It answers questions like:

- Does every `collection_id`, `parent_id`, `dashboard_id`, `document_id`, `based_on_card_id`, transform tag, snippet name, etc. resolve to an entity that actually exists in the tree?
- For each MBQL query, do every `source-table`, field reference, join target, segment, measure, and expression resolve against the database schema?
- For each native query, do the referenced tables, columns, and snippets exist?
- Do dashboards' and documents' embedded card references point at real cards?

The checker ships inside the Metabase Enterprise JAR and is invoked via `--mode checker`. Default Docker image: `metabase/metabase-enterprise:latest`. Use `metabase/metabase-enterprise-head:latest` only when the user explicitly wants the in-development build — e.g. testing unreleased checker changes.

## Inputs

Two inputs, both required:

- **The representation tree** — the repo root containing `collections/`, `databases/`, `transforms/`, `python_libraries/`. This is what gets checked.
- **The database metadata** — a JSON file produced by `GET /api/database/metadata`. **By default located at `.metabase/metadata.json`.** The checker uses it to resolve column/table references inside queries; without it, query-level checks cannot run.

If `.metabase/metadata.json` is missing, do **not** run the checker. Instead, tell the user it needs to be fetched first and defer to the `metabase-database-metadata` skill (which handles `.env`, credentials, and the fetch). Only run the checker once the metadata file is present on disk.

## When to run

**Run the semantic checker once, after you are done making changes to representation YAML files** — editing a card's query, renaming a collection, re-parenting entities, adding/removing snippets or transform tags, etc. A passing schema check does not catch broken cross-entity references or query columns that no longer exist; the semantic checker does. Treat it as the second half of local validation, paired with `npx @metabase/representations validate-schema`.

**Batch it — don't run between edits.** Each invocation spins up the Metabase JVM and loads the database metadata, which takes roughly a minute of fixed overhead before any checks run. Running it after every individual edit wastes that minute on each edit and bogs the session down. Make all the YAML changes you intend to make, then run the checker once at the end. If it surfaces issues, fix them and re-run — but again, fix everything you can see in one pass before re-running.

Outside of that, do not run it proactively at session start. At session start, just observe what's on disk — do not refresh metadata, do not pull the Docker image. Only run when the user explicitly asks, or once you have finished a batch of YAML edits.

## Running the checker

Once `.metabase/metadata.json` exists and Docker is available:

```sh
docker pull metabase/metabase-enterprise:latest

docker run --rm \
  -v "$PWD:/workspace" \
  --entrypoint "" \
  -w /app \
  metabase/metabase-enterprise:latest \
  java -jar metabase.jar \
    --mode checker \
    --export /workspace \
    --schema-dir /workspace/.metabase/metadata.json \
    --schema-format concise
```

Flag reference:

- **`--mode checker`** — selects semantic-check mode (skips server startup, import, etc.).
- **`--export /workspace`** — path **inside the container** to the representation tree root. With the `-v "$PWD:/workspace"` mount above, this maps to the current repo root on the host.
- **`--schema-dir /workspace/.metabase/metadata.json`** — path to the database metadata JSON. Despite the `-dir` suffix the flag accepts a single JSON file. Point it elsewhere only if the user has stored metadata at a non-default path.
- **`--schema-format concise`** — format the input metadata is in. `concise` matches what `@metabase/database-metadata` / `GET /api/database/metadata` produce. Do not change unless the user explicitly has a different dump format.

The container needs no network access for the check itself — pull the image first if the host is offline-prone.

Exit code is non-zero on findings. Surface the checker's stdout/stderr verbatim to the user; do not summarize away specific paths or entity names, since those are how the user locates the broken reference.

## Common failure modes

- **"Database metadata not found" / schema load errors** — `.metabase/metadata.json` is missing, stale, or malformed. Refer the user to the `metabase-database-metadata` skill for a fresh fetch.
- **Unknown collection / card / dashboard / snippet / tag reference** — the referenced `entity_id` or name does not exist in the tree. Either the target YAML is missing, or the reference is a typo; grep the tree for the id/name to confirm which.
- **Unknown table or field inside a query** — the query references a column that the database metadata doesn't know about. Either the warehouse schema has drifted (refetch metadata), or the query itself is wrong.
- **Docker image missing / not pulled** — run `docker pull metabase/metabase-enterprise:latest` first. On slow networks warn the user; the image is multi-hundred-MB.

## Relationship to other skills

- **`metabase-representation-format`** — defines the YAML shape the checker reads. Use it when the user is editing or creating representation files.
- **`metabase-database-metadata`** — owns the `.metabase/metadata.json` file and the fetch/refresh flow. Invoke it whenever the metadata file is missing, stale, or the user explicitly asks to refresh it before re-running the checker.
- **Schema-level validation** (`npx @metabase/representations validate-schema`) — the fast, local-only check that runs in the `Schema Check` CI workflow and does not need database metadata. Essentially instant; run it freely between edits. The semantic checker assumes schema-valid input, so run schema validation first if a file looks structurally wrong.
