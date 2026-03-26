# Query

Metabase supports 2 types of database queries: MBQL and native. MBQL queries are constructed via a graphical query editor, while native queries are plain SQL with some Metabase-specific additions. In many cases graphical queries should be preferred since they are easier to work with in Metabase. If something is not supported in MBQL, a SQL query can be used.

## MBQL queries

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

MBQL query with a filter:

```yaml
database: Sample Database   # Database FK
type: query
query:
  source-table:             # Table FK
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
```

This query is the same as `SELECT * FROM PUBLIC.PRODUCTS WHERE CATEGORY = 'Widget'` in SQL.

### Filters

Filters are MBQL clauses expressed as YAML lists. The general form is:

```yaml
filter:
- <operator>
- <column reference>
- <value>
```

The column reference uses a `field` clause with a Field FK:

```yaml
- field
- - My Database        # database name
  - null               # schema (null for schemaless databases)
  - Schemaless Table   # table name
  - Some Field         # field name
- null                 # field options (usually null)
```

Common filter operators: `=`, `!=`, `<`, `>`, `<=`, `>=`, `is-null`, `not-null`, `contains`, `starts-with`, `ends-with`, `between`.

Compound filters use `and` / `or`:

```yaml
filter:
- and
- - ">="
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
    - null
  - 10
- - <
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
    - null
  - 100
```

## Native queries

Minimal native query:

```yaml
database: Sample Database        # Database FK
type: native
native:
  query: SELECT * FROM PRODUCTS  # valid SQL
  template-tags: {}
```
