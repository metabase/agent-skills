# Measure

A measure is a saved aggregation definition in Metabase. Measures allow reusable aggregations that can be applied across multiple questions and dashboards.

Each measure holds a `definition` that specifies the database and aggregation clause. See [query.md](../common/query.md) for the query specification.

## Minimal required properties

```yaml
name: Total revenue
entity_id: xK7mPqR2sT4uVwXyZ9a1b     # nanoid
creator_id: internal@metabase.com
definition:
  database: Sample Database          # Database FK
  query:
    aggregation:
    - - sum
      - - field
        - - Sample Database
          - PUBLIC
          - ORDERS
          - TOTAL
        - base-type: type/Float
serdes/meta:
- id: xK7mPqR2sT4uVwXyZ9a1b         # nanoid, matches entity_id
  label: total_revenue              # lowercased name, spaces converted to underscores
  model: Measure
```

## Optional properties

```yaml
description: Sum of all order totals            # string or null
archived: false                                 # boolean
created_at: '2024-08-28T09:46:24.692002Z'       # ISO 8601 date
```
