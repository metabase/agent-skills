# Segment

A segment is a saved filter definition in Metabase. Segments allow reusable filters that can be applied across multiple questions and dashboards.

Each segment holds a `definition` that specifies the source table and filter criteria. See [query.md](../common/query.md) for the query and filter specification.

## Minimal required properties

```yaml
name: Widget products
entity_id: aB3kLmN9pQrStUvWxYz1a  # nanoid
creator_id: internal@metabase.com
definition:
  source-table:                    # Table FK
  - Sample Database
  - PUBLIC
  - PRODUCTS
  filter:
  - =
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - CATEGORY
    - null
  - Widget
serdes/meta:
- id: aB3kLmN9pQrStUvWxYz1a       # nanoid, matches entity_id
  label: widget_products           # lowercased name, spaces converted to underscores
  model: Segment
```

## Optional properties

```yaml
description: Products in the Widget category          # string or null
archived: false                                       # boolean
created_at: '2024-08-28T09:46:24.692002Z'             # ISO 8601 date
```
