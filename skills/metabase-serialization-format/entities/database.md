# Database

A database represents a connected data source in Metabase. Database entities are synced from the connected database and should not be edited by hand.

Databases use their **name** as identifier (not entity_id).

## Minimal required properties

```yaml
name: Sample Database                      # string, also the identifier
serdes/meta:
- id: Sample Database                      # database name as id
  model: Database
```

## Optional properties

```yaml
description: null                           # string or null
engine: h2                                  # database engine: h2, postgres, mysql, bigquery, redshift, snowflake, etc.
dbms_version: null                          # map or null
auto_run_queries: true                      # boolean
refingerprint: null                         # boolean or null
is_full_sync: true                          # boolean
is_on_demand: false                         # boolean
is_sample: false                            # boolean
is_audit: false                             # boolean
is_attached_dwh: false                      # boolean
metadata_sync_schedule: 0 5 * * * ? *       # cron expression
cache_field_values_schedule: 0 0 23 * * ? *  # cron expression
settings: {}                                # engine-specific settings map
caveats: null                               # string or null
points_of_interest: null                    # string or null
timezone: null                              # string or null
provider_name: null                         # string or null
uploads_enabled: false                      # boolean
uploads_schema_name: null                   # string or null
uploads_table_prefix: null                  # string or null
created_at: '2024-08-28T14:38:42.753121Z'   # ISO 8601 date
creator_id: null                            # User FK, email or null
router_database_id: null                    # Database FK, name or null
initial_sync_status: complete               # "complete", "incomplete", or "aborted"
```

`details` (connection config with credentials) is only exported in certain modes and is typically excluded for security reasons.
