# Authoring the transforms, and choosing their schedule

Load `mb skills get transform` for the CLI body shapes, and `mb skills get transform-test-plan` before writing tests.

## Before you write one

- **Database support.** `mb db get <id> --fields engine,features,is_audit,is_sample,router_user_attribute,router_database_id`
  must list `transforms/table`. Refuse audit and sample databases, and DB routing: a non-null `router_user_attribute`
  marks a router database, a non-null `router_database_id` a routing destination. The `database-routing` entry in
  `features` only means the driver supports routing. Mongo is Python-only; Athena and SQLite have no transforms.
  The target always lives in the **model's own database**, because the swap refuses a cross-database replacement.
- **Writable schema.** The warehouse user, or the writable connection, needs create/drop/write on the target schema,
  and `CREATE SCHEMA` if the schema is new.
  - Prefer a schema that existing transforms already write to: look at `transform list` targets, or successful runs.
  - A database with no transforms yet is unproven. Run a tiny test transform there first, on a rehearsal instance or with approval.
  - Ask before writing into a database that is itself a Metabase application DB, or into a production OLTP database.
- **Fresh target name.** All of these must hold:
  - `mb table list --db-id <db> --term <name> --include-transform-targets` returns nothing;
  - no existing transform targets `schema.name`;
  - the warehouse has no such relation. Check `information_schema.tables` and the views, through `mb query` with a
    native SQL stage, case-insensitively: `lower(table_schema) = lower(:s) and lower(table_name) = lower(:n)`.
    Snowflake stores unquoted names upper-case.

  Re-run the check right before the PR merges, and again right before the first `mb transform run`. A dbt job may
  have created the table in between; stop if it now exists.

  Use snake_case, keep within the engine's identifier limit (Postgres: 63 bytes), and follow the house convention.
- **No card references.** Rewrite the model's query to read only tables:
  - **T6 on a model:** wait until the upstream model is swapped; its query then reads the table.
  - **T6 on a saved question** (not a model, so not part of the migration): inline it. Get its SQL with
    `mb card get <q> --fields dataset_query`, then `mb query --file … --compile`, and paste it as a CTE.
  - **Snippets:** inline their text, or keep the snippet if it is synced and stable.
- **Parameters.** A native model with a required `{{variable}}` and no default can't be a transform. Make it optional
  with `[[ ]]` or give it a default.

## A model that builds on another transform's output

Some models are thin projections over a table a transform already builds: `select *, <one expression> from <transform output>`,
or a filter on it. The inventory flags these as "builds on transform N's output". There are three options, so put them to the user:

1. **New transform.** Self-contained, and you own it. It's a near-duplicate table, and it must be scheduled after the
   upstream one; the job runs stale dependencies first. Use the same tag as the upstream transform.
2. **Extend the upstream transform** with the extra columns, then swap onto its existing table. No new table, and the
   schedule is inherited. But it changes someone else's transform and a table that may already be published and
   shared, so it needs the upstream owner's OK. It must also be run once before the swap, so the new columns exist.
3. **Swap onto the upstream table as-is.** Possible only when every model column already exists there. The swap check
   enforces that.

## Types and metadata the transform must reproduce

- **Coerced columns.** If the source table casts a field in Metabase (`coercion_strategy`, e.g. ISO8601 text → date),
  the model's column is a date but the warehouse column is text. The transform must output the real type, e.g.
  `cast(hire_date as date)` in SQL. Otherwise `check-replace-source` reports `column-type-mismatch`, and native
  dependents that use date functions break. The inventory flags "source has coerced columns".
- **FKs and display remaps.** A model column that is an FK (or is remapped to a name from another table) needs the same
  FK semantics on the new table, plus a `___dimension` remap where one existed. Put the FK target on a published table.
- **Sort and limit.** A transform table has no order. Dependents that relied on the model's `ORDER BY` need their own sort.

## Keep the swap working: output column names

The swap matches the model's column key (`desired-column-alias`, falling back to `name`) to the table's field `name`.
The match is exact and case-sensitive. If a name differs, dependents keep refs that no longer resolve, and they break
silently.

- **SQL models:** the transform's SQL is the model's SQL, so the result names are the same, provided the engine returns
  them the same way. On Redshift, result names already come back lower-case, so that is fine.
- **MBQL models:** output columns are the final stage's desired aliases, passed through the driver's `escape-alias`:
  - every engine truncates aliases to 60 bytes with a hash suffix;
  - BigQuery turns non-alphanumerics into `_`;
  - Redshift folds identifiers to lower case, unless `enable_case_sensitive_identifier` is on [unverified].

  Joined columns are named like `Products__ID`, and expressions keep their display-ish names (`Field Value Scanning`).
  On Postgres those survive verbatim, as ugly but matching names. On Redshift or BigQuery they don't.
- **Rule:** before authoring, predict each output name per engine and compare it with the model's keys. After the first
  run, confirm with `check-replace-source`. If they differ, choose with the user:
  - keep the model's exact names (quoted identifiers, where the engine preserves case);
  - rename for readability, and accept that you must rewrite every dependent's refs yourself with an explicit rename map;
  - keep the model.
- Choose the transform type deliberately; it can't be changed later. A SQL model gets a SQL transform. An MBQL model
  gets either an MBQL transform (same semantics, keeps field-path refs portable) or hand-written SQL (cleaner names,
  but then you own the rename map).

## Owner, folder, tests

- **Owner** (`owner_user_id` or `owner_email`): scheduled runs execute as the owner, falling back to the creator. Pick
  an account that exists and can run the source query, typically a human admin. API-key users and non-admin owners can
  fail scheduled runs with a permission error. In YAML, a typo'd email creates an inactive user.
- **Folder:** a transforms-namespace collection. Group by domain, and mirror the Library folder you will publish into.
- **Tests** (`mb transform-test`, where supported: postgres, mysql, h2, clickhouse, redshift, sqlserver):
  - 3–10 representative input rows, with hand-derived expected output;
  - an `empty` expectation for key uniqueness.
  - Tests refuse table-qualified column refs, so don't paste compiled SQL.
  - On a read-only synced instance tests can't even run: run them on rehearsal, and ship them as YAML next to the transform.

## Verify the first run

1. `mb transform run <id> --sync --json` returns `target_table_id`.
2. Compare it with the model:
   - row count;
   - key uniqueness;
   - a checksum over the shared columns (`verification-and-rollback.md`).
   - Expect differences only where the model had an `ORDER BY` or a `LIMIT`, or relies on query-time functions such as
     `now()`, which freeze at run time. Point those out.
3. Check the output field names against the model's keys, as above.

## Schedule: from evidence to a tag

A transform refreshes **only** when an **active** job runs one of its tags. With no tag, it never runs on a schedule.

1. **List the jobs:** `mb transform-job list --json --full` (active flag, cron, `tag_ids`). Built-in jobs can be disabled or
   re-scheduled on a given instance, so never assume "hourly" runs hourly.
2. **Collect the freshness evidence for the model:**

   | Evidence | Where | What it implies |
   |---|---|---|
   | Model persistence | `card get --fields persisted`; `persisted_info` (app DB); setting `persisted-model-refresh-cron-schedule` | Consumers already accept staleness up to that cron. Use the same or a finer cadence |
   | Cache policy on the model itself | `GET /api/cache?model=question&id=<M>` (`cache_config` model `question`) | duration N → job period ≤ N; schedule → a job just before it; adaptive → depends on query cost, so ask |
   | Policies on consumers (questions, dashboards) | `consumer_cache` in models.csv (app-DB path). On the API path, `GET /api/cache?model=question&model=dashboard` filtered to the dependents | Consumers tolerate their own TTL. `nocache` consumers expect live data |
   | Database policy | `cache_config` model `database` | It applies to dependents whether or not they read the model, so the swap doesn't change it |
   | Upstream transforms | the model's source tables that are transform targets, and their tags | No point running more often than the upstream. Jobs already run stale dependencies first |
   | Upstream ELT (dbt, Fivetran, …) | not visible to Metabase | **Ask** when the sources load. Schedule after it |
   | Query cost | `query_execution.running_time` (app DB) or the model's average runtime | Expensive models benefit most from materializing |
   | Usage | `last_used_at`, `view_count`, dashboards and alerts on it | A daily-viewed model rarely needs hourly |

3. **Propose, then ask.** State the inferred cadence and the reason, for example: "persisted hourly → propose the
   active hourly job `<tag>`", or "no cache, no persistence, sources load at 06:00 UTC → propose daily at 07:00". When
   the model was **live** (no persistence, no cache) and consumers include `nocache` dashboards or alerts, flag it.
   Choose with the user between:
   - a frequent job;
   - an incremental transform with a frequent job;
   - keeping it live via a table or view that already exists;
   - accepting a daily snapshot.
4. **Timezones.** Persistence crons use the report timezone; transform jobs use the system timezone. Convert, and say so.
5. **New cadence.** Add a tag (in YAML if tags sync), then create the job on the instance (jobs never sync), and record
   it in the docs.
6. **Alerts on dependents** are now evaluated against a snapshot. Tell their owners that the data changes at the refresh time, not continuously.

## Incremental transforms (only when asked or clearly needed)

- They need a monotonically increasing checkpoint column (an id, or an `updated_at` that bumps on every write).
- Append is the default. A merge key upserts. A lookback window reprocesses recent rows; pair it with a merge key.
- SQL incremental transforms need a table variable on the checkpoint table.
- Any index change triggers a full rebuild. "Reprocess all data" resets the checkpoint.
