# Query

Metabase supports 2 types of database queries: MBQL and native. MBQL queries are constructured via a graphical query editor, while native queries are plain SQL with some Metabase-specific additions. In many cases graphical queries should be preferred since they are easier to work with in Metabase. If something is not supported in MBQL, a SQL query can be used.

## MBQL query

Minimal MBQL query:

```yaml
database: Sample Database   # Database FK
type: query
query:
  source-table:             # Table FK
  - Sample Database  
  - PUBLIC           
  - PRODUCTS         
```

This query is the same as `SELECT * FROM PUBLIC.PRODUCTS` in SQL.

## Native query

Minimal native query:

```yaml
dataset_query:
database: Sample Database        # Database FK
type: native
native:
  query: SELECT * FROM PRODUCTS  # valid SQL
  template-tags: {}
```
