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

### Template tags

Template tags are placeholders in native SQL queries that become interactive filters or dynamic references. They are used in the SQL as `{{tag_name}}` and defined in `template-tags`.

#### String variable

```yaml
native:
  query: "SELECT * FROM PRODUCTS WHERE CATEGORY = {{category}}"
  template-tags:
    category:
      type: text
      name: category
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Category
      default: Widget
```

Compiled SQL (with value `Widget`):
```sql
SELECT * FROM PRODUCTS WHERE CATEGORY = 'Widget'
```

#### Number variable

```yaml
native:
  query: "SELECT * FROM PRODUCTS WHERE PRICE > {{min_price}}"
  template-tags:
    min_price:
      type: number
      name: min_price
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Minimum Price
      default: null
```

Compiled SQL (with value `50`):
```sql
SELECT * FROM PRODUCTS WHERE PRICE > 50
```

#### Date variable

```yaml
native:
  query: "SELECT * FROM ORDERS WHERE CREATED_AT > {{after_date}}"
  template-tags:
    after_date:
      type: date
      name: after_date
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: After Date
      default: null
```

Compiled SQL (with value `2024-01-01`):
```sql
SELECT * FROM ORDERS WHERE CREATED_AT > '2024-01-01'
```

#### Boolean variable

```yaml
native:
  query: "SELECT * FROM PRODUCTS WHERE {{is_active}}"
  template-tags:
    is_active:
      type: boolean
      name: is_active
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Is Active
      default: true
```

Compiled SQL (with value `true`):
```sql
SELECT * FROM PRODUCTS WHERE 1 = 1
```

When `false`, the clause becomes `1 <> 1`. When no value is provided, the tag is omitted entirely (`WHERE 1 = 1`).

#### Field filter (dimension)

Field filters map a template tag to a specific database field, enabling Metabase to generate smart filter widgets (e.g., date pickers, category dropdowns). The SQL must use the tag in a `WHERE` clause context — Metabase replaces it with the appropriate SQL expression.

```yaml
native:
  query: "SELECT * FROM PRODUCTS WHERE {{category_filter}}"
  template-tags:
    category_filter:
      type: dimension
      name: category_filter
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Category
      dimension:                       # Field FK
      - field
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - CATEGORY
      - null
      widget-type: string/=            # filter widget type
      default: null
```

Common `widget-type` values: `string/=`, `string/!=`, `string/contains`, `number/=`, `number/>=`, `number/between`, `date/single`, `date/range`, `date/month-year`, `date/quarter-year`, `date/relative`, `date/all-options`.

Compiled SQL (with `widget-type: string/=` and value `Widget`):
```sql
SELECT * FROM PRODUCTS WHERE CATEGORY = 'Widget'
```

Compiled SQL (with `widget-type: date/range` on a date field, value `2024-01-01~2024-12-31`):
```sql
SELECT * FROM ORDERS WHERE CREATED_AT >= '2024-01-01' AND CREATED_AT < '2025-01-01'
```

When no value is provided, the entire `WHERE {{tag}}` clause is omitted (the query runs unfiltered).

#### Time grouping

```yaml
native:
  query: "SELECT CREATED_AT AS {{created_at}}, COUNT(*) FROM ORDERS GROUP BY {{created_at}}"
  template-tags:
    created_at:
      type: time-grouping
      name: created_at
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Created At
      default: month
```

Compiled SQL (with value `month`):
```sql
SELECT DATE_TRUNC('month', CREATED_AT) AS CREATED_AT, COUNT(*) FROM ORDERS GROUP BY DATE_TRUNC('month', CREATED_AT)
```

#### Table references

```yaml
native:
  query: "SELECT * FROM {{source_table}}"
  template-tags:
    source_table:
      type: table
      name: source_table
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Source Table
```

Compiled SQL (with `PUBLIC.PRODUCTS` selected):
```sql
SELECT * FROM PUBLIC.PRODUCTS
```

### Card references

Reference a saved card (question) as a subquery using `{{#entity_id-card_name}}`:

```yaml
native:
  query: "SELECT * FROM {{#f1C68pznmrpN1F5xFDj6d-products_question}} WHERE PRICE > 50"
  template-tags:
    "#f1C68pznmrpN1F5xFDj6d-products_question":
      type: card
      name: "#f1C68pznmrpN1F5xFDj6d-products_question"
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Products Question
      card-id: f1C68pznmrpN1F5xFDj6d  # entity_id of the referenced card
```

Metabase replaces the tag with the card's query as a CTE.

Compiled SQL (assuming the referenced card's query is `SELECT * FROM PUBLIC.PRODUCTS`):
```sql
WITH f1C68pznmrpN1F5xFDj6d_products_question AS (SELECT * FROM PUBLIC.PRODUCTS)
SELECT * FROM f1C68pznmrpN1F5xFDj6d_products_question WHERE PRICE > 50
```

### Snippet references

Reference a reusable SQL snippet using `{{snippet: Snippet Name}}`:

```yaml
native:
  query: "SELECT * FROM ORDERS WHERE {{snippet: Active Order Filter}}"
  template-tags:
    "snippet: Active Order Filter":
      type: snippet
      name: "snippet: Active Order Filter"
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Snippet: Active Order Filter
      snippet-name: Active Order Filter
      snippet-id: xK7mPqR2sT4uVwXyZ9a1b  # entity_id of the snippet
```

Metabase replaces the tag with the snippet's SQL content inline.

Compiled SQL (assuming the snippet contains `STATUS = 'active' AND TOTAL > 0`):
```sql
SELECT * FROM ORDERS WHERE STATUS = 'active' AND TOTAL > 0
```
