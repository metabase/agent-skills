---
name: metabase-serialization-format
description: Generate and understand Metabase serialized YAML data for export/import across instances
allowed-tools: Read, Write, Edit, Grep, Glob
---

## Overview

Metabase serialization (SerDes) exports instance configuration as a tree of YAML files. Each file represents one entity (a collection, card, dashboard, database definition, etc.). The format is designed to be **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

## Entity keys

Metabase uses 2 ways of identifying entities: by `entity_id` (nanoid) and natural entity keys.

`entity_id` is saved with each entity and should not change after it was created. The entity can be renamed, moved to a different collection, but as long as its `entity_id` remains the same, Metabase will understand that it's the same entity.

`entity_id` is a 21-character [NanoID](https://github.com/ai/nanoid) string like `NDzkGoTCdRcaRyt7GOepg`. This is the primary portable identifier used in cross-references.

Generate a NanoID in Bash:
```bash
head -c 21 /dev/urandom | base64 | tr -dc 'A-Za-z0-9_-' | head -c 21
```

NanoID alphabet: `A-Za-z0-9_-` (64 chars, 21 chars long).

### Natural entity keys

Some entities use natural keys instead of NanoIDs:
- **Database**: identified by `name` (e.g., `"Sample Database"`)
- **Schema**: identified by name within a database
- **Table**: identified by `[database_name, schema, table_name]` (e.g., `["Sample Database", "PUBLIC", "ORDERS"]`)
- **Field**: identified by `[database_name, schema, table_name, field_name]` (e.g., `["Sample Database", "PUBLIC", "ORDERS", "TOTAL"]`)
- **Setting**: identified by setting key
- **Glossary**: identified by `term`

## Folder structure

Metabase serialization exports instance configuration as a tree of YAML files under an export root directory.

```
export-root/
├── settings.yaml                          # Global Metabase settings (flat key-value map)
│
├── collections/                           # All content organized by collection hierarchy
│   ├── {entity_id}_{slug}/                # A collection folder
│   │   ├── {entity_id}_{slug}.yaml        # The collection's own definition
│   │   ├── cards/                          # Questions and models in this collection
│   │   │   └── {entity_id}_{slug}.yaml
│   │   ├── dashboards/                     # Dashboards in this collection
│   │   │   └── {entity_id}_{slug}.yaml
│   │   ├── timelines/
│   │   │   └── {entity_id}_{slug}.yaml
│   │   ├── transforms/                     # Transforms in this collection
│   │   │   └── {entity_id}_{slug}.yaml
│   │   ├── metabots/
│   │   │   └── {entity_id}.yaml
│   │   ├── documents/
│   │   │   └── {entity_id}_{slug}.yaml
│   │   └── {entity_id}_{slug}/             # Nested child collection
│   │       └── cards/
│   │           └── ...
│   │
│   ├── cards/                              # Cards in root collection (no parent)
│   │   └── {entity_id}_{slug}.yaml
│   ├── dashboards/                         # Dashboards in root collection
│   │   └── {entity_id}_{slug}.yaml
│   ├── transforms/                         # Transforms in root collection
│   │   └── {entity_id}_{slug}.yaml
│   ├── metabots/
│   │   └── {entity_id}.yaml
│   └── channels/
│       └── {name}_{slug}.yaml
│
├── databases/                              # Database metadata (schema, tables, fields)
│   └── {database_name}/
│       ├── {database_name}.yaml            # Database definition
│       ├── schemas/                         # If database has schemas
│       │   └── {schema_name}/
│       │       └── tables/
│       │           └── {table_name}/
│       │               ├── {table_name}.yaml
│       │               ├── fields/
│       │               │   ├── {field_name}.yaml
│       │               │   ├── {field_name}___fieldvalues.yaml
│       │               │   └── {field_name}___fieldusersettings.yaml
│       │               ├── segments/
│       │               │   └── {entity_id}_{slug}.yaml
│       │               └── measures/
│       │                   └── {entity_id}_{slug}.yaml
│       └── tables/                          # If database is schemaless
│           └── {table_name}/
│               ├── {table_name}.yaml
│               └── fields/
│                   └── ...
│
├── actions/                                # Top-level actions
│   └── {entity_id}_{slug}.yaml
│
├── glossary/                               # Glossary terms
│   └── {term}.yaml
│
├── python-libraries/                       # Shared Python code for transforms
│   └── {entity_id}.yaml
│
├── snippets/                               # Native query snippets
│   └── {entity_id}_{slug}.yaml
│
├── transform_tags/
│   └── {entity_id}_{slug}.yaml
│
└── transform_jobs/
    └── {entity_id}_{slug}.yaml
```

### Path construction rules

- **Collection hierarchy is reflected in directory nesting.** A child collection folder lives inside its parent collection folder.
- **Entity files are named `{entity_id}_{label}.yaml`** where label is the slugified name.
- **Entity type subdirectories use lowercase plural model names**: `cards/`, `dashboards/`, `timelines/`, `transforms/`, `metabots/`, `documents/`, `channels/`.
- **Database/table/field paths use actual names** (not entity_ids), since these entities are identified by name.
- **FieldValues and FieldUserSettings** are stored alongside the field file with `___fieldvalues` and `___fieldusersettings` suffixes.
- **Slashes in names** are escaped as `__SLASH__` and backslashes as `__BACKSLASH__`.

## Parameter

A parameter is a filter control on a dashboard or card. Parameters are not standalone entities — they are embedded in the `parameters` array of their parent entity.

### Minimal required properties

```yaml
parameters:
- id: a1b2c3d4-e5f6-7890-abcd-ef1234567890   # UUID
  name: Category
  slug: category                               # URL-friendly identifier
  type: string/=                               # filter widget type
```

### Common `type` values

- `string/=`, `string/!=`, `string/contains`, `string/starts-with`, `string/ends-with`
- `number/=`, `number/!=`, `number/>=`, `number/<=`, `number/between`
- `date/single`, `date/range`, `date/month-year`, `date/quarter-year`, `date/relative`, `date/all-options`
- `temporal-unit`
- `id`

### Optional properties

```yaml
parameters:
- id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  name: Category
  slug: category
  type: string/=
  default: Widget                              # default value, type depends on filter type
  required: false                              # boolean
  sectionId: string                            # parameter section grouping
  temporal_units:                              # for temporal-unit type
  - month
  - quarter
  - year
  values_query_type: list                      # "list", "search", or "none"
  values_source_type: null                     # null, "card", or "static-list"
  values_source_config: {}                     # configuration for the values source
```

### Parameter target

A parameter target specifies which column or variable a parameter maps to. Targets are used in `parameter_mappings` (see Dashboard > ParameterMapping) and other places where parameters connect to queries.

#### MBQL queries — field reference

Maps to a column in a structured query:

```yaml
target:
- dimension
- - field
  - - Sample Database
    - PUBLIC
    - PRODUCTS
    - CATEGORY
  - null
```

#### MBQL queries — multi-stage field reference

For multi-stage queries, a `stage-number` option identifies which stage the field belongs to:

```yaml
target:
- dimension
- - field
  - - Sample Database
    - PUBLIC
    - PRODUCTS
    - CATEGORY
  - null
- stage-number: 1
```

#### Native queries — Field filter and Time grouping variables

Maps to a `dimension` or `time-grouping` template tag in a native query:

```yaml
target:
- dimension
- - template-tag
  - category_filter
```

#### Native queries — other variable types

Maps to a `text`, `number`, `date`, or `boolean` template tag:

```yaml
target:
- variable
- - template-tag
  - min_price
```

## Query

Metabase supports two types of database queries: MBQL and native. MBQL queries are constructed via a graphical query editor, while native queries are plain SQL with Metabase-specific additions. Prefer MBQL queries when possible since they are easier to work with in Metabase. Use native queries when something is not supported in MBQL.

### MBQL queries

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

#### Joins

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

#### Expressions

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

#### Filters

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

#### Aggregations

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

#### Breakouts

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

#### Order by

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

#### Limit

Limit restricts the number of rows returned.

```yaml
limit: 10
```

### Native queries

Minimal native query:

```yaml
database: Sample Database        # Database FK
type: native
native:
  query: SELECT * FROM PRODUCTS  # valid SQL
  template-tags: {}
```

#### Template tags

Template tags are placeholders in native SQL queries that become interactive filters or dynamic references. They are used in the SQL as `{{tag_name}}` and defined in `template-tags`.

##### String variable

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

##### Number variable

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

##### Date variable

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

##### Boolean variable

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

##### Field filter (dimension)

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

##### Time grouping

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

##### Table references

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

#### Card references

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

#### Snippet references

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

## Database

A database represents a connected data source in Metabase. Database entities are synced from the connected database and should not be edited by hand.

Databases use their **name** as identifier (not entity_id).

### Minimal required properties

```yaml
name: Sample Database                      # string, also the identifier
serdes/meta:
- id: Sample Database                      # database name as id
  model: Database
```

### Optional properties

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

## Table

A table represents a database table or view in Metabase. Table entities are synced from the connected database and should not be edited by hand.

Tables use `[database, schema, table_name]` as identifier.

### Minimal required properties

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

### Optional properties

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

## Field

A field represents a column in a database table. Field entities are synced from the connected database and should not be edited by hand.

Fields use `[database, schema, table, field_name]` as identifier.

### Minimal required properties

```yaml
name: PRODUCT_ID                           # string
table_id:                                  # Table FK, [database, schema, table]
- Sample Database
- PUBLIC
- ORDERS
base_type: type/Integer                    # Metabase base type
serdes/meta:
- id: Sample Database
  model: Database
- id: PUBLIC
  model: Schema
- id: ORDERS
  model: Table
- id: PRODUCT_ID
  model: Field
```

### Optional properties

```yaml
display_name: Product ID                   # string
description: null                          # string or null
active: true                               # boolean
visibility_type: normal                    # "normal", "details-only", "hidden", "sensitive", "retired"
database_type: INTEGER                     # database-native type string
effective_type: type/Integer               # effective type (after coercion)
semantic_type: type/FK                     # type/PK, type/FK, type/Name, type/Email, type/Category, type/City, etc., or null
database_is_auto_increment: false          # boolean
database_required: false                   # boolean
json_unfolding: false                      # boolean
coercion_strategy: null                    # string or null (e.g., "Coercion/UNIXSeconds->DateTime")
preview_display: true                      # boolean
position: 2                                # integer
custom_position: 0                         # integer
database_position: 2                       # integer
has_field_values: null                     # null, "none", "list", "search", "auto-list"
settings: null                             # map or null
caveats: null                              # string or null
points_of_interest: null                   # string or null
nfc_path: null                             # array or null (JSON column path for nested fields)
database_default: null                     # string or null
database_indexed: null                     # boolean or null
database_is_generated: null                # boolean or null
database_is_nullable: null                 # boolean or null
database_is_pk: null                       # boolean or null
database_partitioned: null                 # boolean or null
created_at: '2024-08-28T14:38:42.774331Z'  # ISO 8601 date
fk_target_field_id: null                   # Field FK, [database, schema, table, field] or null
parent_id: null                            # Field FK, [database, schema, table, field] or null (for nested/JSON fields)
dimensions: []                             # array of Dimension entities
```

### Foreign key example

A field referencing another table's primary key:

```yaml
name: PRODUCT_ID
semantic_type: type/FK
fk_target_field_id:
- Sample Database
- PUBLIC
- PRODUCTS
- ID
```

### Dimensions

Dimensions are nested inside the field's `dimensions` array:

```yaml
dimensions:
- name: My Dimension                       # string
  type: internal                           # "internal" or "external"
  entity_id: abc123nanoid                  # nanoid
  created_at: '2024-08-28T09:46:24.692002Z'  # ISO 8601 date
  human_readable_field_id: null            # Field FK, [database, schema, table, field] or null
```

### FieldValues

**Path**: `databases/.../fields/{field_name}___fieldvalues.yaml`

Stores cached distinct values for a field, used for filter dropdowns.

```yaml
values:                                    # array of values
- Doohickey
- Gadget
- Gizmo
- Widget
human_readable_values: []                  # array of display names (parallel to values)
has_more_values: false                     # boolean
hash_key: null                             # string or null
created_at: '2024-08-28T14:38:42.774331Z'  # ISO 8601 date
last_used_at: '2024-08-28T14:38:42.774331Z'  # ISO 8601 date
type: full                                 # "full", "sandbox", or "linked-filter"
serdes/meta:
- id: Sample Database
  model: Database
- id: PUBLIC
  model: Schema
- id: PRODUCTS
  model: Table
- id: CATEGORY
  model: Field
- id: '0'
  model: FieldValues
```

### FieldUserSettings

**Path**: `databases/.../fields/{field_name}___fieldusersettings.yaml`

User-customized field display settings that override synced field metadata. All fields are nullable; only non-null values override the field's defaults.

```yaml
semantic_type: null
description: Some custom Description
display_name: null
visibility_type: null
has_field_values: null
effective_type: null
coercion_strategy: null
caveats: null
points_of_interest: null
nfc_path: null
json_unfolding: null
settings: null
created_at: '2025-06-13T12:52:06.383265Z'  # ISO 8601 date
fk_target_field_id: null                   # Field FK, [database, schema, table, field] or null
serdes/meta:
- id: Sample Database
  model: Database
- id: PUBLIC
  model: Schema
- id: PRODUCTS
  model: Table
- id: CATEGORY
  model: Field
- id: '1'
  model: FieldUserSettings
```

## Collection

A collection is a folder-like container for organizing cards, dashboards, and other entities in Metabase. Collection hierarchy is reflected in the directory structure of the export.

### Minimal required properties

```yaml
name: Marketing Analytics                  # string
entity_id: M-Q4pcV0qkiyJ0kiSWECl           # nanoid
serdes/meta:
- id: M-Q4pcV0qkiyJ0kiSWECl                # nanoid, matches entity_id
  label: marketing_analytics               # lowercased name, spaces converted to underscores
  model: Collection
```

### Optional properties

```yaml
description: Reports for the marketing team  # string or null
slug: marketing_analytics                    # string, URL-friendly name
archived: false                              # boolean
archived_directly: null                      # boolean or null
type: null                                   # null or "instance-analytics"
namespace: null                              # null, "transforms", or "snippets"
authority_level: null                        # null or "official"
archive_operation_id: null                   # string or null
is_remote_synced: false                      # boolean
is_sample: false                             # boolean
created_at: '2024-08-28T09:46:18.671622Z'    # ISO 8601 date
parent_id: null                              # Collection FK, entity_id of parent collection or null for root
personal_owner_id: null                      # User FK, email or null
```

## Card

A card represents a Question, Model, or Metric in Metabase. Cards are the primary way to save and share queries.

Each card holds a `dataset_query`. See the Query section for the query specification.

### Minimal required properties

Card with an MBQL query:

```yaml
name: Products question
entity_id: f1C68pznmrpN1F5xFDj6d  # nanoid
display: table
creator_id: internal@metabase.com
dataset_query:
  database: Sample Database       # Database FK
  type: query
  query:
    source-table:                 # Table FK
    - Sample Database
    - PUBLIC
    - PRODUCTS
visualization_settings: {}
serdes/meta:
- id: f1C68pznmrpN1F5xFDj6d       # nanoid, matches entity_id
  label: products_question        # lowercased name, spaces converted to underscores
  model: Card                     # always Card
```

Card with a native query:

```yaml
name: Products question
entity_id: f1C68pznmrpN1F5xFDj6d    # nanoid
display: table
creator_id: internal@metabase.com
dataset_query:
  database: Sample Database        # Database FK
  type: native
  native:
    query: SELECT * FROM PRODUCTS
    template-tags: {}
visualization_settings: {}
serdes/meta:
- id: f1C68pznmrpN1F5xFDj6d       # nanoid, matches entity_id
  label: products_question        # lowercased name, spaces converted to underscores
  model: Card                     # always Card
```

### Optional properties

```yaml
description: All products                  # string or null
archived: false                            # boolean
archived_directly: false                   # boolean
collection_preview: true                   # boolean
collection_position: null                  # integer or null
query_type: null                           # null, "query", or "native"
type: question                             # "question", "model", or "metric"
enable_embedding: false                    # boolean
embedding_params: null                     # map or null
embedding_type: null                       # null, "sdk", "standalone"
public_uuid: null                          # UUID string or null
metabase_version: v1.58.0-SNAPSHOT         # string or null
card_schema: 23                            # integer, card schema version, should not be changed manually
created_at: '2024-08-28T09:46:24.692002Z'  # ISO 8601 date
database_id: Sample Database               # Database FK, should match the database in dataset_query
table_id:                                  # Table FK, should match source-table in the most nested query
- Sample Database
- PUBLIC
- PRODUCTS
source_card_id: null                       # Card FK, should match source-card in dataset_query
collection_id: M-Q4pcV0qkiyJ0kiSWECl       # Collection FK, entity_id or null for the root collection
dashboard_id: null                         # Dashboard FK, entity_id or null
document_id: null                          # Document FK, entity_id or null
made_public_by_id: null                    # User FK, email or null
parameters: []                             # Native query parameters
parameter_mappings: []                     # Unused, always empty
result_metadata: null                      # Query result columns
```

## Dashboard

A dashboard is a collection of cards arranged in a grid layout. Dashboards contain dashboard cards (`dashcards`), parameters for filtering, and optional tabs for organizing content.

Dashboard parameters are described in the Parameter section.

### Minimal required properties

```yaml
name: Orders Overview
entity_id: Q_jD-f-9clKLFZ2TfUG2h        # nanoid
creator_id: internal@metabase.com
serdes/meta:
- id: Q_jD-f-9clKLFZ2TfUG2h              # nanoid, matches entity_id
  label: orders_overview                  # lowercased name, spaces converted to underscores
  model: Dashboard                        # always Dashboard
```

### Optional properties

```yaml
description: Overview of order metrics             # string or null
archived: false                                    # boolean
archived_directly: false                           # boolean
collection_id: M-Q4pcV0qkiyJ0kiSWECl              # Collection FK, entity_id or null for root
collection_position: null                          # integer or null
position: null                                     # integer or null
auto_apply_filters: true                           # boolean
enable_embedding: false                            # boolean
embedding_params: null                             # map or null
embedding_type: null                               # null, "sdk", "standalone"
made_public_by_id: null                            # User FK, email or null
public_uuid: null                                  # UUID string or null
show_in_getting_started: false                     # boolean
caveats: null                                      # string or null
points_of_interest: null                           # string or null
width: fixed                                       # "fixed" or "full"
initially_published_at: null                       # ISO 8601 date or null
created_at: '2024-08-28T09:46:24.726993Z'          # ISO 8601 date
parameters: []                                     # see Parameter section
tabs: []                                           # dashboard tabs
dashcards: []                                      # see DashboardCard below
```

### DashboardCard

A dashboard card places a card (question) on the dashboard grid. Most dashboard cards reference an existing card via `card_id`, which is the card's `entity_id`.

#### Minimal required properties

```yaml
dashcards:
- entity_id: UkpFcfUZMZt9ehChwnrAO
  card_id: f1C68pznmrpN1F5xFDj6d          # Card FK — entity_id of the referenced card
  row: 0
  col: 0
  size_x: 4
  size_y: 4
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h             # parent Dashboard entity_id
    model: Dashboard
  - id: UkpFcfUZMZt9ehChwnrAO             # this DashboardCard entity_id
    model: DashboardCard
```

#### Example — dashboard with two cards

```yaml
name: Orders Overview
entity_id: Q_jD-f-9clKLFZ2TfUG2h
creator_id: internal@metabase.com
dashcards:
- entity_id: UkpFcfUZMZt9ehChwnrAO
  card_id: f1C68pznmrpN1F5xFDj6d          # "Some Question" card
  row: 0
  col: 0
  size_x: 8
  size_y: 4
  parameter_mappings: []
  series: []
  visualization_settings: {}
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h
    model: Dashboard
  - id: UkpFcfUZMZt9ehChwnrAO
    model: DashboardCard
- entity_id: AlYMOYAhCXhr1VIiH5umt
  card_id: OMuZ0wHe2O5Z_59-cLmn4          # "Series Question A" card
  row: 0
  col: 8
  size_x: 4
  size_y: 4
  parameter_mappings: []
  series: []
  visualization_settings: {}
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h
    model: Dashboard
  - id: AlYMOYAhCXhr1VIiH5umt
    model: DashboardCard
serdes/meta:
- id: Q_jD-f-9clKLFZ2TfUG2h
  label: orders_overview
  model: Dashboard
```

#### Optional properties

```yaml
dashcards:
- entity_id: UkpFcfUZMZt9ehChwnrAO
  card_id: f1C68pznmrpN1F5xFDj6d
  row: 0
  col: 0
  size_x: 4
  size_y: 4
  action_id: null                          # Action FK, entity_id or null
  dashboard_tab_id: null                   # Tab FK or null
  inline_parameters: []                    # inline parameter overrides
  parameter_mappings: []                   # see ParameterMapping below
  series: []                               # see DashboardCardSeries below
  visualization_settings: {}               # display settings
  created_at: '2024-08-28T09:46:24.733Z'   # ISO 8601 date
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h
    model: Dashboard
  - id: UkpFcfUZMZt9ehChwnrAO
    model: DashboardCard
```

### DashboardCardSeries

A series overlays additional cards on the same dashboard card visualization (e.g., multiple lines on one chart).

#### Minimal required properties

```yaml
series:
- card_id: OMuZ0wHe2O5Z_59-cLmn4          # Card FK — entity_id of the series card
  position: 0                              # integer, display order starting at 0
- card_id: XsxiHuzwlGIFNq245HdZC
  position: 1
```

#### Example — dashboard card with series

```yaml
dashcards:
- entity_id: UkpFcfUZMZt9ehChwnrAO
  card_id: f1C68pznmrpN1F5xFDj6d          # primary card
  row: 0
  col: 0
  size_x: 8
  size_y: 4
  series:
  - card_id: OMuZ0wHe2O5Z_59-cLmn4        # first overlay series
    position: 0
  - card_id: XsxiHuzwlGIFNq245HdZC        # second overlay series
    position: 1
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h
    model: Dashboard
  - id: UkpFcfUZMZt9ehChwnrAO
    model: DashboardCard
```

### ParameterMapping

A parameter mapping connects a dashboard parameter to a specific card column or variable. Each mapping lives in the `parameter_mappings` array of a DashboardCard.

The `target` field specifies which column or variable the parameter maps to — see the Parameter target section for the full specification.

#### Properties

```yaml
parameter_mappings:
- card_id: f1C68pznmrpN1F5xFDj6d          # Card FK — entity_id of the mapped card
  parameter_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890  # UUID, matches a parameter's id
  target:                                  # see Parameter target section
  - dimension
  - - field
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - CATEGORY
    - null
```

## Segment

A segment is a saved filter definition in Metabase. Segments allow reusable filters that can be applied across multiple questions and dashboards.

Each segment holds a `definition` that specifies the source table and filter criteria. See the Query section for the query and filter specification.

### Minimal required properties

```yaml
name: Widget products
entity_id: aB3kLmN9pQrStUvWxYz1a   # nanoid
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
- id: aB3kLmN9pQrStUvWxYz1a        # nanoid, matches entity_id
  label: widget_products           # lowercased name, spaces converted to underscores
  model: Segment
```

### Optional properties

```yaml
description: Products in the Widget category          # string or null
archived: false                                       # boolean
created_at: '2024-08-28T09:46:24.692002Z'             # ISO 8601 date
```

## Measure

A measure is a saved aggregation definition in Metabase. Measures allow reusable aggregations that can be applied across multiple questions and dashboards.

Each measure holds a `definition` that specifies the database and aggregation clause. See the Query section for the query specification.

### Minimal required properties

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

### Optional properties

```yaml
description: Sum of all order totals            # string or null
archived: false                                 # boolean
created_at: '2024-08-28T09:46:24.692002Z'       # ISO 8601 date
```

## Transform

A transform generates a table in the database by running a query. Transforms allow materializing query results as persistent database tables.

The `source` wraps a query that produces the data. See the Query section for the query specification. The `target` specifies where the resulting table is written.

### Minimal required properties

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

### Optional properties

```yaml
description: Materialized product summary table    # string or null
collection_id: M-Q4pcV0qkiyJ0kiSWECl               # Collection FK, entity_id or null for the root collection
created_at: '2024-08-28T09:46:24.692002Z'          # ISO 8601 date
```
