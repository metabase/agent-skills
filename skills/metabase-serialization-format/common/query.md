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

### Joins

Joins combine data from multiple tables. Each join specifies a source table, join condition, alias, and which fields to include.

```yaml
joins:
- source-table:                        # Table FK
  - Sample Database
  - PUBLIC
  - PRODUCTS
  condition:
  - =
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - PRODUCT_ID
    - null
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - ID
    - null
  alias: Products
  strategy: left-join                  # "left-join", "right-join", "inner-join", "full-join"
  fields: all                          # "all", "none", or list of field clauses
```

MBQL query with a join:

```yaml
database: Sample Database
type: query
query:
  source-table:
  - Sample Database
  - PUBLIC
  - ORDERS
  joins:
  - source-table:
    - Sample Database
    - PUBLIC
    - PRODUCTS
    condition:
    - =
    - - field
      - - Sample Database
        - PUBLIC
        - ORDERS
        - PRODUCT_ID
      - null
    - - field
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - ID
      - null
    alias: Products
    strategy: left-join
    fields: all
```

This query is the same as `SELECT * FROM PUBLIC.ORDERS LEFT JOIN PUBLIC.PRODUCTS ON ORDERS.PRODUCT_ID = PRODUCTS.ID` in SQL.

### Expressions

Expressions define computed columns. Each expression is a named MBQL clause.

```yaml
expressions:
  Profit:
  - -
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
    - null
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TAX
    - null
```

Common expression operators: `+`, `-`, `*`, `/`, `concat`, `coalesce`, `case`, `abs`, `ceil`, `floor`, `round`, `upper`, `lower`, `trim`, `length`.

`case` expressions:

```yaml
expressions:
  Price Tier:
  - case
  - - - - ">"
        - - field
          - - Sample Database
            - PUBLIC
            - PRODUCTS
            - PRICE
          - null
        - 100
      - Premium
    - - - "<="
        - - field
          - - Sample Database
            - PUBLIC
            - PRODUCTS
            - PRICE
          - null
        - 100
      - Standard
```

Referencing an expression in other clauses uses the `expression` keyword:

```yaml
filter:
- ">"
- - expression
  - Profit
- 0
```

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

### Breakouts

Breakouts group results by one or more columns, similar to `GROUP BY` in SQL. Breakouts are typically used together with aggregations.

```yaml
breakout:
- - field
  - - Sample Database
    - PUBLIC
    - ORDERS
    - CREATED_AT
  - temporal-unit: month
```

The `temporal-unit` option groups date/time fields by a time unit: `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year`.

MBQL query with aggregation and breakout:

```yaml
database: Sample Database
type: query
query:
  source-table:
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
  breakout:
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - CREATED_AT
    - temporal-unit: month
```

This query is the same as `SELECT DATE_TRUNC('month', CREATED_AT), SUM(TOTAL) FROM PUBLIC.ORDERS GROUP BY DATE_TRUNC('month', CREATED_AT)` in SQL.

### Order by

Order-by sorts results by one or more columns.

```yaml
order-by:
- - asc                                # "asc" or "desc"
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
    - null
```

Multiple sort clauses:

```yaml
order-by:
- - desc
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - CREATED_AT
    - null
- - asc
  - - field
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
    - null
```

Sorting by an aggregation result uses the aggregation index:

```yaml
order-by:
- - desc
  - - aggregation
    - 0                                # index of the aggregation clause
```

### Limit

Limit restricts the number of rows returned.

```yaml
limit: 10
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
