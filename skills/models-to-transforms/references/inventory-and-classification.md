# Inventory and classification

`scripts/inventory.py` does all of this. Read this file to understand its output, to extend it, or to answer questions
the script doesn't.

## Two data paths

| | API path (default) | App-DB path (`--app-db <id>`) |
|---|---|---|
| Needs | an admin `mb` profile | the instance's own application DB connected as a data source (PostgreSQL only; SELECT only) |
| Enumerates models with | `mb search --models dataset --db-id <db> --include-dashboard-questions` per database, plus `--archived` with `--include-archived`. Search caps at 1,000 results per query and hides the usage-analytics namespace, so the script lists the audit database separately (`card list --filter database --model-id 13371337`) | `report_card where type='model'` |
| Dependents | `mb dependency dependents card <id> --include-personal-collections`: active only, and personal collections hidden without the flag. Newer servers return kinds an older CLI rejects; the script then falls back to `GET /api/ee/dependencies/graph/dependents` | the `dependency` table, active **and** archived, joined to live rows (edges can dangle after deletes) |
| Bookmarks, subscriptions | **not visible** for other users | `card_bookmark`, `pulse_card` |
| Alerts, actions (any state), model indexes, cache config, sandboxes | with `--extras`: `mb card alerts`, `GET /api/action?model-id=` (+ `&archived=true`), `/api/model-index?model_id=`, `/api/cache?model=question&id=`, `/api/mt/gtap` | `notification_card` joined to active `notification`, `action`, `model_index`, `cache_config`, `sandboxes` |
| Action buttons, chart series, consumers' cache policies | not collected | `report_dashboardcard.action_id`, `dashboardcard_series`, `cache_config` of dependent questions and dashboards (`consumer_cache`) |
| Without the dependencies feature (`--no-deps`) | `card list --filter using_model` (unarchived, same database) | regex scan of `report_card.dataset_query`, archived included |
| Speed for about 1,000 models | tens of minutes | about a minute |

**Identity check.** Before using an app DB, the script compares a few cards' `id`, `name` and `entity_id` with the API.
It also checks that it isn't a replica (`pg_is_in_recovery()`) and that `view_log` is recent, and refuses to continue
otherwise (unless `--allow-partial`). A staging copy looks identical, and stale counts would let gates pass wrongly.
Re-run the check before using the app DB for an archive or purge gate in a later session.

**Unreadable items.** Anything that couldn't be read lands in `failures.csv`, `summary.md` says so in its heading, and
the run exits 3. Never classify on a partial inventory.

### Stored query shapes

- The REST API always returns **MBQL 5**: `{"lib/type":"mbql/query","stages":[…]}`, with native template tags as a list.
- The app DB stores both MBQL 5 and **legacy** MBQL. Legacy uses `"query":{"source-table":N|"card__N","source-query":{…}}`
  with `filter` instead of `filters`, and native template tags as a dict. The script handles both.
- `report_card.table_id` and `source_card_id` aren't reliable for classification: for a card-based model they hold the
  *root* table of the chain, or null. Parse `dataset_query`.
- Effective table metadata (`is_published`, `collection_id`, `data_layer`) is the `metabase_table_user_settings`
  overlay on `metabase_table`, and field metadata likewise with `metabase_field_user_settings`. `mb table get` returns
  it already merged.

## Classes

Rules are evaluated top to bottom. The `class` column holds these slugs; in anything the user reads, describe the
model in words instead.

| Class | Rule | Target table |
|---|---|---|
| **card-based** | any card reference, at any depth: `source-card`, `card__N`, `{{#N}}` outside SQL comments, `card` template tags. `upstream_models` lists the models reached directly or through saved questions | none yet. Exception: a wrapper of a saved question that itself wraps one table swaps straight to that table |
| **upload-based** | the source table has `is_upload` | the table, if the model is a wrapper |
| **transform-output-wrapper** | wrapper shape, and the table has `transform_id` / `transform_target` | the table |
| **table-wrapper** (MBQL) | one stage; `source-table`; other keys ⊆ {`fields`, `order-by`, `limit`}; no joins; no implicit-join (`source-field`) fields | the table |
| **sql-table-wrapper** | one native stage: `SELECT * / t.* / plain column list FROM one_table`, optional `ORDER BY` / `LIMIT`. No joins, `WHERE`, `GROUP BY`, CTEs, snippets, parameters, literals, renames or ClickHouse `FINAL`. A `{{table}}` template tag also counts. The relation is resolved against active tables of the same database | the table. `native_parse_confidence` is `high` / `medium` / `low` (ambiguous name, or a schemaless match) / `unresolved` |
| **derived-mbql** | any other MBQL | – |
| **derived-sql** | any other SQL: renames, multi-stage queries over native SQL, expressions | – |

A `fields` subset on a wrapper is fine for the swap, because extra table columns are allowed. They do become visible to
people who explore the table, though.

## Proposed actions

| Action | When |
|---|---|
| `swap-archived-feeder` | already in the Trash, and still serves active content |
| `purge-candidate` | already in the Trash, nothing depends on it |
| `wait: archived model N built on it still serves live content` | in the Trash, and an archived model downstream still feeds live content: purge only after that one is migrated |
| `review: archived, but still used by …` | in the Trash, but action buttons, sandboxes or filter sources still use it |
| `exclude` | Metabase-managed usage analytics (`collection.type = instance-analytics`) |
| `review: unparsed dataset_query` | the query couldn't be parsed |
| `broken` | inactive source table, or a missing upstream card |
| `review: an upstream card could not be read` | permissions or an API error; it is not treated as missing |
| `archive: unused` | stale (not used in `--stale-days`, default 180; never used *and* older than that), no active dependents, and no direct use (dashcards, alerts, subscriptions, filter sources, sandboxes, actions in any state, action buttons). It is suffixed "(verify)" when some of those counts are unknown |
| `swap-to-upstream-table: the table that replaces model N` / `create-transform: reads the tables that replace models …` | card-based with model upstreams, classified through its own shape over them (`upstream_shape`: `wrapper` when it only selects, orders or limits over one upstream, else `derived`). The table is the one the plan gives the upstream |
| `blocked: upstream model(s) … will not be migrated` | card-based, when any upstream is excluded, blocked, broken or a purge candidate |
| `review: LIMIT wrapper` | a wrapper with `LIMIT`: a swap would return every row |
| `convert-to-verified-question` | a derived MBQL model on one table with no joins, aggregation or breakout (fields, filters, expressions, sort and limit are fine), or one SELECT over one table with no JOIN, GROUP BY, window, CTE or aggregate. Card-based models whose own shape over a single upstream model is like that convert once that upstream's swap has re-pointed them. The card stays, becomes a question, and gets verified |
| `swap-to-existing-table` | any wrapper with a target (table, SQL, upload-based, transform-output), and a card-based wrapper of a saved question that wraps one table (`via saved question`) |
| `verify-source-table` | an `sql-table-wrapper` whose relation Metabase doesn't know: sync the schema, or check the SQL |
| `blocked: sandbox card` | the model backs a sandbox policy; rebuild the policy first |
| `create-transform` | `derived-mbql`, `derived-sql`, upload-based models with logic, and card-based models whose only upstreams are saved questions (inline them) |
| `blocked: <reason>` | no `transforms/table`, an audit or sample DB, or DB routing. The instance's own app DB is **not** blocked: it gets `create-transform` with a confirm-the-schema flag |

Flags worth reading:

- `swap-check-fails: N model columns missing on the table`: predicts a `check-replace-source` failure (long or
  truncated keys, stale `result_metadata`, implicit-join columns).
- `needs FK metadata on the table before the swap`.
- `metadata_diffs` (a column, not a flag): display names, semantic types and descriptions that change for dependents.
- `shares-table-with:<ids>`: dedupe candidates.
- `limit-wrapper`.
- `upstream-model-outside-this-run`: in a subset run, the upstream's depth and fate are unknown, so re-run without `--ids`.
- `card-tag-only-in-comment`: a stale `card` tag; drop it before materializing.
- `reads-saved-question`.
- `required-parameter-without-default`.
- `non-snake-column-keys` / `long-or-truncated-column-keys` / `implicit-join-columns`.
- `used-as-sandbox-card`.
- `builds on transform N's output (consider extending that transform)`: see `transforms-and-scheduling.md`.
- `source has coerced columns (...)`: cast them in the transform.
- `order-by-wrapper`: dependents lose the model's sort after a swap.
- `target db is this instance's own application database` / `no transform writes to this database yet`: confirm the schema, or prove it is writable, before authoring.

## Waves

`wave` is the longest chain of model→model references below the model, counting models reached through saved questions.
Wave 0 reads tables or only saved questions. Every wave is planned up front: a wave-*k* model is classified through
the tables the plan gives its upstreams (`upstream_shape`), so the plan names its target before anything runs. After
wave *k*'s swaps, **re-run the inventory** for wave *k+1* as a check: the swaps rewrote those models onto tables, so
the script now classifies them mechanically (a wrapper of a swapped wrapper becomes a `table-wrapper`, a derived one
`derived-mbql` or `derived-sql`), and the result must match the plan.

## Queries for later phases (app-DB path)

Run every query through the guarded runner:
`python3 <skill>/scripts/inventory.py --profile <p> --app-db <id> --sql q.sql > out.csv`. It refuses anything that isn't
a single SELECT/WITH. Replace `:model` with the id. The CLI times out around 30 s, so aggregate in CTEs.

**Closure of a model** (everything a swap can touch):

```sql
with recursive closure(t, id) as (
  select from_entity_type, from_entity_id from dependency where to_entity_type = 'card' and to_entity_id = :model
  union
  select d.from_entity_type, d.from_entity_id from dependency d join closure c on d.to_entity_type = c.t and d.to_entity_id = c.id
)
select t, count(*) from closure group by t;
```

**Synced entities in the closure:** on a read-only sync instance, a swap needs this to return 0 rows.

```sql
with recursive closure(t, id) as ( /* as above */ )
select c.t, c.id, r.status from closure c
join remote_sync_object r on r.model_id = c.id and r.status <> 'removed'
 and r.model_type = case c.t when 'card' then 'Card' when 'dashboard' then 'Dashboard' when 'transform' then 'Transform'
                             when 'document' then 'Document' when 'segment' then 'Segment' when 'measure' then 'Measure' end;
```

**Text references with no dependency edge** (cards whose analysis failed are missed by the swap). Archived cards are
included on purpose:

```sql
select id, name, archived from report_card
where dataset_query ~ ('("source-card": ?' || :model || '\M|card__' || :model || '\M|\{\{ *#' || :model || '\M)')
  and id not in (select from_entity_id from dependency where from_entity_type = 'card' and to_entity_type = 'card' and to_entity_id = :model);
```

**Links and URLs pointing at the model:**

```sql
select 'dashcard' kind, id from report_dashboardcard where visualization_settings ~ ('"targetId": ?' || :model || '\M|/model/' || :model || '\M')
union all select 'card', id from report_card where description ~ ('/model/' || :model || '\M') and not archived
union all select 'dashboard', id from report_dashboard where description ~ ('/model/' || :model || '\M') and not archived;
```

Also check documents (`document.document::text`) on versions that have them.

**Pre-archive and purge gate** (SKILL.md § "Archive, then purge"). Each count must be 0, or accepted by the user by
name. The columns marked "info" don't block.

```sql
select
 (select count(*) from dependency d
    left join report_card c on d.from_entity_type = 'card' and c.id = d.from_entity_id
    left join report_dashboard b on d.from_entity_type = 'dashboard' and b.id = d.from_entity_id
  where d.to_entity_type = 'card' and d.to_entity_id = :model
    and (c.id is not null or b.id is not null or d.from_entity_type not in ('card','dashboard'))) as dependency_edges_live,
 (select count(*) from report_dashboardcard dc join report_dashboard b on b.id = dc.dashboard_id and not b.archived where dc.card_id = :model) as dashcards,
 (select count(*) from dashboardcard_series s where s.card_id = :model) as series,
 (select count(*) from parameter_card where card_id = :model) as filter_sources,
 (select count(*) from sandboxes where card_id = :model) as sandboxes,
 (select count(*) from notification_card nc join notification n on n.payload_id = nc.id and n.payload_type = 'notification/card' and n.active where nc.card_id = :model) as alerts,
 (select count(*) from pulse_card where card_id = :model) as subscriptions,
 (select count(*) from action where model_id = :model) as actions_any_state,
 (select count(*) from report_dashboardcard dc join action a on a.id = dc.action_id where a.model_id = :model) as action_buttons,
 (select count(*) from model_index where model_id = :model) as model_indexes,
 (select count(*) from report_card where id = :model and (public_uuid is not null or enable_embedding)) as public_or_embedded,
 (select count(*) from remote_sync_object where model_type = 'Card' and model_id = :model and status <> 'removed') as remote_synced,
 (select count(*) from card_bookmark where card_id = :model) as bookmarks_info,
 (select count(*) from report_dashboardcard dc join report_dashboard b on b.id = dc.dashboard_id and b.archived where dc.card_id = :model) as dashcards_on_archived_dashboards_info;
```

Also run the text-reference query above. It must return 0.

**API path equivalents:**

- `mb dependency dependents card <id> --include-personal-collections`;
- `mb card list --filter using_model --model-id <id>`: unarchived cards only, so say that archived ones weren't scanned;
- `mb card alerts <id>`;
- `GET /api/action?model-id=<id>` **and** `&archived=true`. Then, for each action, find dashboards whose dashcards
  carry its `action_id` (`mb dashboard get <id> --fields dashcards`);
- `GET /api/mt/gtap` for sandboxes;
- dashboards' `parameters` for filter sources;
- `mb card get <id> --fields public_uuid,enable_embedding,collection`.
