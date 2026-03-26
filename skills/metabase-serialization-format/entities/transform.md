# Transform

A transform generates a table in the database by running a query. Transforms allow materializing query results as persistent database tables.

The `source` wraps a query that produces the data. See [query.md](../common/query.md) for the query specification. The `target` specifies where the resulting table is written.

## Minimal required properties

```yaml
name: Product summary
entity_id: rT5vWxYz1aBcDeFgHiJkL  # nanoid
creator_id: internal@metabase.com
source:
  type: query
  query:
    database: Sample Database      # Database FK
    type: query
    query:
      source-table:                # Table FK
      - Sample Database
      - PUBLIC
      - PRODUCTS
target:
  database: Sample Database        # Database FK
  type: table
  schema: PUBLIC
  name: product_summary            # target table name
serdes/meta:
- id: rT5vWxYz1aBcDeFgHiJkL        # nanoid, matches entity_id
  label: product_summary           # lowercased name, spaces converted to underscores
  model: Transform
```

## Optional properties

```yaml
description: Materialized product summary table    # string or null
collection_id: M-Q4pcV0qkiyJ0kiSWECl               # Collection FK, entity_id or null for the root collection
created_at: '2024-08-28T09:46:24.692002Z'          # ISO 8601 date
```
