# Query

Metabase supports two types of database queries: MBQL and native. MBQL queries are constructed via a graphical query editor, while native queries are plain SQL with Metabase-specific additions. Prefer MBQL queries when possible since they are easier to work with in Metabase. Use native queries when something is not supported in MBQL.

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

### Aggregations

Aggregations compute summary values over rows. The general form is:

```yaml
aggregation:
- - <function>
  - <column reference>
```

Common aggregation functions: `count`, `sum`, `avg`, `min`, `max`, `distinct`, `cum-sum`, `cum-count`.

`count` does not require a column reference:

```yaml
aggregation:
- - count
```

Other functions take a `field` clause:

```yaml
aggregation:
- - sum
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
    - base-type: type/Float
```

Multiple aggregations can be combined:

```yaml
aggregation:
- - count
- - sum
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
    - base-type: type/Float
```

MBQL query with an aggregation:

```yaml
database: Sample Database   # Database FK
type: query
query:
  source-table:             # Table FK
  - Sample Database
  - PUBLIC
  - ORDERS
  aggregation:
  - - sum
    - - field
      - - Sample Database
        - PUBLIC
        - ORDERS
        - TOTAL
      - base-type: type/Float
```

This query is the same as `SELECT SUM(TOTAL) FROM PUBLIC.ORDERS` in SQL.

## Native queries

Minimal native query:

```yaml
database: Sample Database        # Database FK
type: native
native:
  query: SELECT * FROM PRODUCTS  # valid SQL
  template-tags: {}
```
