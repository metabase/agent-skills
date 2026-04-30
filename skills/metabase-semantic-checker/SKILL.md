---
name: metabase-semantic-checker
description: Runs the Metabase semantic checker against a tree of Representation Format YAML files to verify that all references resolve — cross-entity references (collection_id, dashboard_id, parent_id, parameter source cards, snippet references, transform tags, etc.) and references to columns inside MBQL and native queries. Slow (≥1 min per run). Only use when the user explicitly asks to verify entity references or column references in MBQL/SQL queries; in most cases this runs as a CI step, not locally. Requires database metadata on disk (by default `.metadata/table_metadata.json`).
model: opus
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

## Metabase semantic checker

The semantic checker validates a tree of **Metabase Representation Format** YAML files for referential integrity. Schema-level validation (shape of each file, required fields, enum values) is handled separately by `npx @metabase/representations validate-schema`; the semantic checker runs *after* schema validation and focuses on cross-file and cross-system consistency.

It compiles every MBQL query down to SQL against the database metadata and checks that each entity reference and each column reference resolves to something that actually exists. Concretely, it answers:

- Does every `collection_id`, `parent_id`, `dashboard_id`, `document_id`, `based_on_card_id`, transform tag, snippet name, etc. resolve to an entity that actually exists in the tree?
- For each MBQL query, do every `source-table`, field reference, join target, segment, measure, and expression resolve against the database schema? (Verified by compiling the query to SQL.)
- For each native query, do the referenced tables, columns, and snippets exist?
- Do dashboards' and documents' embedded card references point at real cards?

Each run takes **1 minute or more** — roughly a minute of fixed JVM + metadata-loading overhead before any checks start, plus query-compilation time that scales with the tree.

The checker ships inside the Metabase Enterprise JAR and is invoked via `--mode checker`. Default Docker image: `metabase/metabase-enterprise:latest`. Use `metabase/metabase-enterprise-head:latest` only when the user explicitly wants the in-development build — e.g. testing unreleased checker changes.

## Inputs

Two inputs, both required:

- **The representation tree** — the repo root containing `collections/`, `databases/`, `transforms/`, `python_libraries/`. This is what gets checked.
- **The database metadata** — a JSON file downloaded from the Metabase workspace page. **By default located at `.metadata/table_metadata.json`.** The checker uses it to resolve column/table references inside queries; without it, query-level checks cannot run.

If `.metadata/table_metadata.json` is missing, do **not** run the checker. Instead, tell the user it needs to be downloaded first and defer to the `metabase-database-metadata` skill (which handles where the file comes from and how to extract the YAML tree from it). Only run the checker once the metadata file is present on disk.

## When to run

**Do not run the semantic checker by default when making edits.** It is slow (≥1 minute per run) and in most projects is wired up as a CI step that runs on every push or PR — that is where it belongs. Local runs are for targeted diagnosis, not routine validation.

Only run it locally when **the user explicitly asks** for one of these:

- verify that all entity references resolve (collections, dashboards, cards, snippets, transform tags, etc.), or
- verify that all column references in queries — MBQL or SQL — are correct.

Phrasings that count as an explicit ask: "semantic check", "check references", "validate queries against the schema", "make sure the columns still exist", or diagnosing a broken reference the user already suspects. A bare "run the checker" does **not** count — by default "the checker" means the fast schema checker (`npx @metabase/representations validate-schema`). Only wording that explicitly names references or queries should trigger the semantic checker.

Otherwise, skip it. After editing YAML, rely on `npx @metabase/representations validate-schema` for local feedback and leave the semantic check to CI. Do not run it proactively at session start, and do not run it as a self-imposed "finishing step" after edits unless the user asked for it.

**If you do run it, batch.** Make all the YAML changes first, then run the checker once. Each invocation pays the ≥1-minute fixed overhead; running between edits multiplies that cost. If it surfaces issues, fix everything you can see in one pass before re-running.

## Running the checker

Once `.metadata/table_metadata.json` exists and Docker is available:

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
    --schema-dir /workspace/.metadata/table_metadata.json \
    --schema-format concise
```

Flag reference:

- **`--mode checker`** — selects semantic-check mode (skips server startup, import, etc.).
- **`--export /workspace`** — path **inside the container** to the representation tree root. With the `-v "$PWD:/workspace"` mount above, this maps to the current repo root on the host.
- **`--schema-dir /workspace/.metadata/table_metadata.json`** — path to the database metadata JSON. Despite the `-dir` suffix the flag accepts a single JSON file. Point it elsewhere only if the user has stored metadata at a non-default path.
- **`--schema-format concise`** — format the input metadata is in. `concise` matches what `@metabase/database-metadata` and the workspace-page download produce. Do not change unless the user explicitly has a different dump format.

The container needs no network access for the check itself — pull the image first if the host is offline-prone.

Exit code is non-zero on findings. Surface the checker's stdout/stderr verbatim to the user; do not summarize away specific paths or entity names, since those are how the user locates the broken reference.

## Common failure modes

- **"Database metadata not found" / schema load errors** — `.metadata/table_metadata.json` is missing, stale, or malformed. Refer the user to the `metabase-database-metadata` skill for a fresh download.
- **Unknown collection / card / dashboard / snippet / tag reference** — the referenced `entity_id` or name does not exist in the tree. Either the target YAML is missing, or the reference is a typo; grep the tree for the id/name to confirm which.
- **Unknown table or field inside a query** — the query references a column that the database metadata doesn't know about. Either the warehouse schema has drifted (refetch metadata), or the query itself is wrong.
- **Docker image missing / not pulled** — run `docker pull metabase/metabase-enterprise:latest` first. On slow networks warn the user; the image is multi-hundred-MB.

## Relationship to other skills

- **`metabase-representation-format`** — defines the YAML shape the checker reads. Use it when the user is editing or creating representation files.
- **`metabase-database-metadata`** — owns the `.metadata/table_metadata.json` file and the download/refresh flow. Invoke it whenever the metadata file is missing, stale, or the user explicitly asks to refresh it before re-running the checker.
- **Schema-level validation** (`npx @metabase/representations validate-schema`) — the fast, local-only check that runs in the `Schema Check` CI workflow and does not need database metadata. Essentially instant; run it freely between edits. The semantic checker assumes schema-valid input, so run schema validation first if a file looks structurally wrong.
