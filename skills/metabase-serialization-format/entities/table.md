# Table

A table represents a database table or view in Metabase. Table entities are synced from the connected database and should not be edited by hand.

Tables use `[database, schema, table_name]` as identifier.

## Minimal required properties

```yaml
name: ORDERS                               # string
db_id: Sample Database                     # Database FK, database name
schema: PUBLIC                             # string or null (null for schemaless databases)
serdes/meta:
- id: Sample Database
  model: Database
- id: PUBLIC                               # omitted if schema is null
  model: Schema
- id: ORDERS
  model: Table
```

## Optional properties

```yaml
display_name: Orders                       # string
description: null                          # string or null
entity_type: entity/TransactionTable       # entity type classification or null
active: true                               # boolean
is_upload: false                           # boolean
field_order: database                      # "database", "alphabetical", "custom", "smart"
visibility_type: null                      # null, "hidden", "technical", "cruft"
show_in_getting_started: false             # boolean
initial_sync_status: complete              # string
points_of_interest: null                   # string or null
caveats: null                              # string or null
database_require_filter: null              # boolean or null
is_writable: null                          # boolean or null
data_authority: unconfigured               # string
data_source: null                          # string or null
owner_email: null                          # string or null
is_published: false                        # boolean
created_at: '2024-08-28T14:38:42.774331Z'  # ISO 8601 date
archived_at: null                          # ISO 8601 date or null
deactivated_at: null                       # ISO 8601 date or null
data_layer: null                           # keyword or null
collection_id: null                        # Collection FK, entity_id or null
transform_id: null                         # Transform FK, entity_id or null
owner_user_id: null                        # User FK, email or null
```
