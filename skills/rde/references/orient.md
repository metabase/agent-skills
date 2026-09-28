# Orient

Read before anything that builds or changes. One read-only pass over the scope the request names, recorded in the state file; where the work stands picks the situation, not the request alone.

```bash
source ./.scratch/probe.sh
mb db list --profile <profile> --json; mb db get "$DB" --include tables --profile <profile> --json
mb table list --db-id "$DB" --fields id,schema,name,data_layer,data_source,is_published,owner_email,description --max-bytes 0 --profile <profile> --json \
  | jq '[.data[] | {id, schema, name, data_layer, data_source, is_published, owner_email, described: (.description != null)}]'
mb transform list --fields id,name,description,target --max-bytes 0 --profile <profile> --json
mb search --models metric,measure,segment,dataset --db-id "$DB" --limit 50 --profile <profile> --json
mb search --verified --db-id "$DB" --profile <profile> --json
mb collection tree --profile <profile> --json; mb git-sync status --profile <profile> --json
mb db get "$DB" --profile <profile> --json | jq .engine    # Snowflake or BigQuery: transform tests cannot run (references/transform-tests.md)
```

A list whose `has_more` is still true is incomplete; page it before judging.

| Readiness | Means |
| --- | --- |
| L0 raw | no curated tables; tables lack descriptions, keys, or semantic types |
| L1 described | no curated tables; every table described with keys and types |
| L2 curated | curated tables exist (published, `data_layer: final`, or `data_source` `metabase-transform`/`transform`), no owned metric on them |
| L3 defined | metrics on curated tables, each with an owner |
| L4 governed | every such metric verified, every curated table published |

Practice style decides whose conventions you match: Metabase transforms, transforms built elsewhere (`data_source: transform`, schemas like `stg_`, `int_`, `mart_`, `dbt_`), models, native SQL cards.

- Greenfield (L0–L1): explore, build, semantic, deliver; one thin slice end to end first.
- Resume (open decisions, `Draft.`/`Ad hoc:` descriptions, failing runs or tests): start at the first item whose last run (`mb transform runs --transform-id <id>`) or test (`mb transform-test list --transform <id>`, run each) fails.
- Mature (owned tables, verified metrics, conventions you did not write): `change`, or the playbook of what is added, planned against dependents. Extend, never rebuild.
An `unknown field path` error means this server lacks that field (an older version): drop it from `--fields` and read the table with `mb table get <id> --full`.
