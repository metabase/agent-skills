# Metabase Representation Format

**Version:** 1.0.0

## Overview

Metabase represents user-created content as a tree of YAML files. Each file represents one entity (a collection, card, dashboard, etc.). The format is designed to be **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

This specification covers user-created content entities. Database metadata entities (Database, Table, Field) are synced from connected databases and are outside the scope of this specification; they appear here only as foreign key references within user content.

## Table of Contents

1. [Entity Keys](#entity-keys)
2. [Folder Structure](#folder-structure)
3. [MBQL Query](#mbql-query)
4. [Native Query](#native-query)
5. [Visualization Settings](#visualization-settings)
6. [Click Behavior](#click-behavior)
7. [Parameter](#parameter)
8. [Collection](#collection)
9. [Card](#card)
10. [Dashboard](#dashboard)
11. [Document](#document)
12. [Segment](#segment)
13. [Measure](#measure)
14. [Snippet](#snippet)
15. [Transform](#transform)

---

## Entity Keys

Metabase uses two ways of identifying entities: `entity_id` (NanoID) and natural entity keys.

### NanoID

`entity_id` is a 21-character [NanoID](https://github.com/ai/nanoid) string (alphabet: `A-Za-z0-9_-`). It is the primary portable identifier used in cross-references. Once assigned, it does not change — the entity can be renamed or moved, but the `entity_id` remains stable. Entity IDs must be **unique per entity type** within an instance — no two entities of the same type may share the same `entity_id`.

Generate a NanoID with the `nanoid` CLI:

```sh
npx nanoid
# → LZfXLFzPPR4NNrgjlWDxn
```

Or in Bash:

```bash
head -c 21 /dev/urandom | base64 | tr -dc 'A-Za-z0-9_-' | head -c 21
# → LZfXLFzPPR4NNrgjlWDxn
```

### Foreign Key References

User content entities reference database objects using natural keys:

| Reference | Format | Example |
|-----------|--------|---------|
| Database FK | database name | `"Sample Database"` |
| Table FK | `[database, schema, table]` | `["Sample Database", "PUBLIC", "ORDERS"]` |
| Field FK | `[database, schema, table, field, ...]` | `["Sample Database", "PUBLIC", "ORDERS", "TOTAL"]` |
| Collection FK | entity_id of collection | `"M-Q4pcV0qkiyJ0kiSWECl"` |
| Card FK | entity_id of card | `"f1C68pznmrpN1F5xFDj6d"` |
| Dashboard FK | entity_id of dashboard | `"Q_jD-f-9clKLFZ2TfUG2h"` |
| User FK | email address | `"internal@metabase.com"` |

For schemaless databases, the schema component is `null` (e.g., `["My Database", null, "my_table"]`).

For JSON-unfolded fields, the Field FK extends beyond 4 elements with the nested path: `["Sample Database", "PUBLIC", "EVENTS", "DATA", "user", "name"]` represents the JSON path `DATA.user.name`.

### SerDes Meta

Every entity includes a `serdes/meta` array that encodes the entity's identity path. Each entry contains an `id` and `model` field. Entities identified by NanoID also include a `label` (slugified name).

```yaml
serdes/meta:
- id: NDzkGoTCdRcaRyt7GOepg
  label: my_entity_name
  model: Card
```

---

## Folder Structure

**Important:** Metabase ignores directory structure when importing — all collection relationships are determined solely by each entity's `collection_id` field. The layout below is how Metabase represents user content when exporting; it mirrors the collection hierarchy on disk for readability, but only `collection_id` is authoritative.

Metabase only checks for importable YAML files in these top-level directories: `collections/`, `databases/` (only `segments/` and `measures/` subdirectories), `python_libraries/` (also accepted as `python-libraries/`), and `transforms/`. Files outside these directories are ignored during import.

Collections are organized by namespace. The `main` namespace holds regular content (cards, dashboards, etc.), `snippets` holds SQL snippet collections, and `transforms` holds transform entities. Subcollections must set `parent_id` to the entity_id of their parent collection. All entity types within a collection are stored flat in the same folder — there are no `cards/`, `dashboards/` subdirectories.

```
export-root/
├── settings.yaml
├── collections/
│   ├── main/                               # Main namespace (regular content)
│   │   ├── {slug}.yaml                     # Entities in root collection
│   │   ├── {collection_slug}.yaml          # Collection definition (sibling of its folder)
│   │   └── {collection_slug}/              # Collection contents
│   │       ├── {card_slug}.yaml            # Cards, dashboards, documents, etc.
│   │       ├── {dashboard_slug}.yaml       #   — all flat in the same folder
│   │       ├── {child_slug}.yaml           # Child collection definition
│   │       └── {child_slug}/              # Child collection contents
│   │           └── ...
│   ├── snippets/                           # Snippets namespace
│   │   ├── {snippet_slug}.yaml             # Snippets in root snippet collection
│   │   ├── {collection_slug}.yaml          # Snippet collection definition
│   │   └── {collection_slug}/              # Snippet collection contents
│   │       └── {snippet_slug}.yaml
│   └── transforms/                         # Transforms namespace
│       └── {transform_slug}.yaml
├── databases/
│   └── {database_slug}/
│       ├── {database_slug}.yaml
│       ├── schemas/
│       │   └── {schema_slug}/
│       │       └── tables/
│       │           └── {table_slug}/
│       │               ├── {table_slug}.yaml
│       │               ├── segments/
│       │               │   └── {slug}.yaml
│       │               └── measures/
│       │                   └── {slug}.yaml
│       └── tables/                         # Schemaless databases
│           └── {table_slug}/
│               ├── {table_slug}.yaml
│               ├── segments/
│               │   └── {slug}.yaml
│               └── measures/
│                   └── {slug}.yaml
├── python_libraries/
│   └── {slug}.yaml
└── transforms/                             # Transform jobs and tags
    ├── transform_jobs/
    │   └── {slug}.yaml
    └── transform_tags/
        └── {slug}.yaml
```

### Path Construction Rules

- Entity files are named `{slug}.yaml` where slug is the slugified entity name (lowercase, spaces to underscores).
- Collection hierarchy is reflected in directory nesting within a namespace.
- A collection's definition file (`{slug}.yaml`) is placed **outside** its folder, as a sibling: e.g., `main/my_collection.yaml` defines the collection whose contents live in `main/my_collection/`.
- All entity types within a collection (cards, dashboards, documents, etc.) are stored flat in the same folder — no type-specific subdirectories.
- Collections are partitioned by namespace: `main/` for regular content, `snippets/` for SQL snippets, `transforms/` for transforms.

### Entity Ownership and Containers

> **Critical:** Every entity's logical position in the collection hierarchy is determined **exclusively** by its `collection_id` field, not the folder structure on disk. The folder layout is for human organization only; Metabase imports entities based solely on their `collection_id`. **An entity without `collection_id` (or with `collection_id: null`) will appear in the root collection.** If you want a card, dashboard, document, snippet, or transform to be inside a specific collection, you **must** set its `collection_id` to the `entity_id` of that collection. Cards nested under a dashboard or document **must also** set `collection_id` to match the `collection_id` of their parent dashboard or document. Similarly, subcollections **must** set `parent_id` to the `entity_id` of their parent collection — without `parent_id`, a collection is treated as a root-level collection regardless of its position in the directory tree.

Dashboards and documents act as **containers** for cards: a card with `dashboard_id` set is owned by that dashboard, and a card with `document_id` set is owned by that document. Container-owned cards behave as if the dashboard or document were a subcollection:

- **`collection_id`** (**required for all collection items**) — Places the entity in a collection. `null` or omitted means root collection. **Must always be set** to place an entity in a specific collection. Even when `dashboard_id` or `document_id` is set, `collection_id` **must** be set and must match the `collection_id` of the parent dashboard or document.
- **`dashboard_id`** — Nests the card under a dashboard. The card should only be used within that dashboard. To reuse a card outside its dashboard, unset `dashboard_id` and place it directly in a collection.
- **`document_id`** — Nests the card under a document. Same semantics as `dashboard_id`: the card should only be used within that document.

When a dashboard or document moves collections, all cards nested under it move too. A card should never have both `dashboard_id` and `document_id` set.

On disk, cards nested under a dashboard or document are placed in a subfolder matching the parent's slug (e.g., `my_dashboard/card.yaml` as a sibling of `my_dashboard.yaml`, within the same collection folder).

- Segments and measures live under their table's directory in the `databases/` tree.
- Database, schema, and table folder names are slugified (e.g., `test-data (h2)` becomes `test_data__h2_`).
- Slashes in names are escaped as `__SLASH__`, backslashes as `__BACKSLASH__`.

---

## MBQL Query

MBQL (Metabase Query Language) queries are constructed via the graphical query editor. Prefer MBQL queries when possible since they are portable across database engines. Use native queries when something is not supported in MBQL.

### Structure

```yaml
"lib/type": mbql/query
database: Sample Database     # Database FK
stages:
- "lib/type": mbql.stage/mbql
  source-table:               # Table FK
  - Sample Database
  - PUBLIC
  - PRODUCTS
```

This is equivalent to `SELECT * FROM PUBLIC.PRODUCTS`.

### Source Table

`source-table` specifies a physical table as the data source using a **Table FK** (array).

```yaml
source-table:
- Sample Database
- PUBLIC
- PRODUCTS
```

### Source Card

`source-card` specifies a saved card (question or model) as the data source using its **Card entity_id** (string). Fields from the card's results are referenced by column name (string) rather than a Field FK:

```yaml
"lib/type": mbql/query
database: Sample Database
stages:
- "lib/type": mbql.stage/mbql
  source-card: f1C68pznmrpN1F5xFDj6d    # entity_id of a saved card
  filters:
  - - ">"
    - {}
    - - field
      - base-type: type/Float
      - PRICE
    - 50
```

### Stages (multi-stage queries)

A query can have multiple stages, where each stage operates on the results of the previous one. Stages are a flat array — there is no nesting. Fields from a previous stage's results are referenced by column name (string) rather than a Field FK. Stages can be stacked to arbitrary depth.

```yaml
"lib/type": mbql/query
database: Sample Database
stages:
- "lib/type": mbql.stage/mbql
  source-table:
  - Sample Database
  - PUBLIC
  - ORDERS
  aggregation:
  - - count
    - "lib/uuid": 11111111-1111-1111-1111-111111111111
  breakout:
  - - field
    - temporal-unit: month
    - - Sample Database
      - PUBLIC
      - ORDERS
      - CREATED_AT
- "lib/type": mbql.stage/mbql
  filters:
  - - ">"
    - {}
    - - field
      - base-type: type/Integer
      - count
    - 10
```

This is equivalent to `SELECT * FROM (SELECT DATE_TRUNC('month', CREATED_AT), COUNT(*) AS count FROM ORDERS GROUP BY 1) WHERE count > 10`.

### Field References

Fields are referenced using a `field` clause with options as the second argument and a Field FK as the third:

```yaml
- field
- {}                          # field options (always a map, never null)
- - Sample Database           # database name
  - PUBLIC                    # schema (null for schemaless)
  - ORDERS                   # table name
  - TOTAL                    # field name
```

Field options (second argument) is always a map (use `{}` when no options are needed):

| Option | Type | Description |
|--------|------|-------------|
| `base-type` | string | Base type hint (e.g., `type/Float`, `type/Integer`) |
| `temporal-unit` | string | Temporal bucketing unit (see [Temporal Bucketing](#temporal-bucketing)) |
| `join-alias` | string | Alias of the join this field belongs to |
| `binning` | map | Binning strategy (see [Binning](#binning)) |
| `source-field` | array | Implicit join: FK field reference in the source table (see below) |
| `source-field-name` | string | Implicit join: FK field by name, for multi-stage queries |
| `source-field-join-alias` | string | Implicit join: join-alias when the FK table is explicitly joined |

#### Implicit Joins

Fields from a related table can be referenced without an explicit `joins` clause by specifying how to traverse the foreign key relationship. This is called an **implicit join**.

Use `source-field` to specify the FK field in the source table that links to the target table:

```yaml
# Get PRODUCTS.TITLE via ORDERS.PRODUCT_ID (implicit join)
- field
- source-field:
  - Sample Database
  - PUBLIC
  - ORDERS
  - PRODUCT_ID
- - Sample Database
  - PUBLIC
  - PRODUCTS
  - TITLE
```

The `source-field` value is a raw Field FK (`[database, schema, table, field]`), not a field clause.

For **multi-stage queries** (when `source-card` is set), additionally set `source-field-name` to reference the FK column by its string name in the previous stage's results. This is needed when the source query returns multiple fields that are both the same FK:

```yaml
- field
- source-field:
  - Sample Database
  - PUBLIC
  - ORDERS
  - PRODUCT_ID
  source-field-name: PRODUCT_ID
- - Sample Database
  - PUBLIC
  - PRODUCTS
  - TITLE
```

When the source (FK) table is itself joined via an explicit `joins` clause, use `source-field-join-alias` to disambiguate which join the FK field comes from. The value must match the `alias` of the corresponding join:

```yaml
- field
- source-field:
  - Sample Database
  - PUBLIC
  - ORDERS
  - PRODUCT_ID
  source-field-join-alias: Joined Orders
- - Sample Database
  - PUBLIC
  - PRODUCTS
  - TITLE
```

Expression references use the `expression` keyword:

```yaml
- expression
- {}
- Profit
```

Aggregation references use the `aggregation` keyword with a UUID that matches the `lib/uuid` of the referenced aggregation clause:

```yaml
- aggregation
- {}
- "11111111-1111-1111-1111-111111111111"
```

### Fields

Restricts which columns are included in the results. Each item is a `field` or `expression` reference:

```yaml
fields:
- - field
  - {}
  - - Sample Database
    - PUBLIC
    - ORDERS
    - TOTAL
- - field
  - {}
  - - Sample Database
    - PUBLIC
    - ORDERS
    - CREATED_AT
- - expression
  - {}
  - Profit
```

When `fields` is omitted, all columns are included. If `fields` is present and the stage has `expressions`, every expression must be included in `fields` as an `expression` reference:

```yaml
fields:
- - field
  - {}
  - - Sample Database
    - PUBLIC
    - ORDERS
    - TOTAL
- - expression
  - {}
  - Profit
expressions:
- - "-"
  - "lib/expression-name": Profit
  - - field
    - {}
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
  - - field
    - {}
    - [Sample Database, PUBLIC, ORDERS, TAX]
```

### Joins

Joins combine data from multiple tables. Each join has its own `stages` array (defining the joined data source) and a `conditions` array (one or more join conditions):

```yaml
joins:
- stages:
  - "lib/type": mbql.stage/mbql
    source-table:
    - Sample Database
    - PUBLIC
    - PRODUCTS
  conditions:
  - - =
    - {}
    - - field
      - {}
      - - Sample Database
        - PUBLIC
        - ORDERS
        - PRODUCT_ID
    - - field
      - {}
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - ID
  alias: Products
  strategy: left-join
  fields: all
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `stages` | array | Yes | Array of stage objects defining the joined data source |
| `conditions` | array | Yes | Array of join conditions, each a filter clause |
| `alias` | string | Yes | Join alias (used in field references) |
| `strategy` | string | Yes | `"left-join"`, `"right-join"`, `"inner-join"`, `"full-join"` |
| `fields` | any | No | `"all"`, `"none"`, or list of field clauses |

Joined fields are referenced with a `join-alias` option:

```yaml
- field
- join-alias: Products
- - Sample Database
  - PUBLIC
  - PRODUCTS
  - TITLE
```

### Expressions

Computed columns defined as an array of clauses. Each expression operator's options map includes `lib/expression-name` to name the resulting column:

```yaml
expressions:
- - "-"
  - "lib/expression-name": Profit
  - - field
    - {}
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
  - - field
    - {}
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TAX
```

See [Expression Operators](#expression-operators) for the full operator reference.

### Filters

`filters` is an array of filter clauses that restrict which rows are included. Multiple clauses are implicitly ANDed together. To use OR logic, include an explicit `[or, {}, ...]` clause as one of the array items.

```yaml
filters:
- - <operator>
  - {}
  - <column reference>
  - <value>
```

Multiple filter clauses (implicitly ANDed):

```yaml
filters:
- - ">="
  - {}
  - - field
    - {}
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
  - 10
- - "<"
  - {}
  - - field
    - {}
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
  - 100
```

To use OR, place an explicit `or` clause as an item in the array:

```yaml
filters:
- - or
  - {}
  - - =
    - {}
    - - field
      - {}
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - CATEGORY
    - Widget
  - - =
    - {}
    - - field
      - {}
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - CATEGORY
    - Gadget
```

See [Filter Operators](#filter-operators) for the full operator reference.

### Breakouts

Breakouts group results by columns (like `GROUP BY`):

```yaml
breakout:
- - field
  - temporal-unit: month
  - - Sample Database
    - PUBLIC
    - ORDERS
    - CREATED_AT
```

### Aggregations

Aggregations compute summary values. Multiple aggregations can be combined. When an aggregation is referenced elsewhere (e.g., in `order-by` or a later stage), its options map must include a `lib/uuid`:

```yaml
aggregation:
- - count
  - {}
- - sum
  - {}
  - - field
    - base-type: type/Float
    - - Sample Database
      - PUBLIC
      - ORDERS
      - TOTAL
```

See [Aggregation Functions](#aggregation-functions) for the full reference.

### Order By

```yaml
order-by:
- - asc                        # "asc" or "desc"
  - {}
  - - field
    - {}
    - - Sample Database
      - PUBLIC
      - PRODUCTS
      - PRICE
```

Sort by aggregation result (using the UUID from the aggregation's `lib/uuid`):

```yaml
order-by:
- - desc
  - {}
  - - aggregation
    - {}
    - "11111111-1111-1111-1111-111111111111"
```

### Limit

```yaml
limit: 10
```

### Temporal Bucketing

The `temporal-unit` field option groups a datetime column into time buckets. This is commonly used in breakouts to group results by month, quarter, etc.

**Bucketing units:** `default`, `millisecond`, `second`, `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year`.

**Extraction units** (return an integer component): `minute-of-hour`, `hour-of-day`, `day-of-week`, `day-of-week-iso`, `day-of-month`, `day-of-year`, `week-of-year`, `week-of-year-iso`, `month-of-year`, `quarter-of-year`, `year-of-era`, `second-of-minute`.

```yaml
# Breakout by month
breakout:
- - field
  - temporal-unit: month
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]

# Breakout by day of week
breakout:
- - field
  - temporal-unit: day-of-week
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
```

Bucketing units truncate the datetime (e.g., `month` groups `2024-03-15` into `2024-03-01`). Extraction units extract a numeric component (e.g., `day-of-week` returns 1–7).

### Binning

The `binning` field option groups a numeric or coordinate column into bins. This is commonly used in breakouts for histograms or geographic grids.

Three strategies are available:

| Strategy | Properties | Description |
|----------|-----------|-------------|
| `num-bins` | `num-bins` (integer) | Split into a fixed number of equal-width bins |
| `bin-width` | `bin-width` (number) | Each bin has a fixed width |
| `default` | — | Let Metabase choose an appropriate binning |

```yaml
# 10 equal bins
breakout:
- - field
  - binning:
      strategy: num-bins
      num-bins: 10
  - [Sample Database, PUBLIC, PRODUCTS, PRICE]

# Bins of width 25
breakout:
- - field
  - binning:
      strategy: bin-width
      bin-width: 25
  - [Sample Database, PUBLIC, PRODUCTS, PRICE]
```

---

### Filter Operators

#### Logical

| Operator | Arguments | Description |
|----------|-----------|-------------|
| `and` | 2+ boolean clauses | Logical AND |
| `or` | 2+ boolean clauses | Logical OR |
| `not` | 1 boolean clause | Logical NOT |

```yaml
# AND
- and
- {}
- - ">"
  - {}
  - - field
    - {}
    - [Sample Database, PUBLIC, PRODUCTS, PRICE]
  - 50
- - "!="
  - {}
  - - field
    - {}
    - [Sample Database, PUBLIC, PRODUCTS, CATEGORY]
  - Doohickey
```

#### Comparison

| Operator | Arguments | Description |
|----------|-----------|-------------|
| `=` | 2+ comparable values | Equals (multi-value = IN) |
| `!=` | 2+ comparable values | Not equals (multi-value = NOT IN) |
| `<` | 2 orderable values | Less than |
| `>` | 2 orderable values | Greater than |
| `<=` | 2 orderable values | Less than or equal |
| `>=` | 2 orderable values | Greater than or equal |
| `between` | expr, min, max | Inclusive range check |
| `inside` | lat, lon, lat-max, lon-min, lat-min, lon-max | Geographic bounding box |

```yaml
# Equals
- =
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, CATEGORY]
- Widget

# Multi-value equals (IN)
- =
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, CATEGORY]
- Widget
- Gadget
- Gizmo

# Between
- between
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, PRICE]
- 10
- 100

# Inside (bounding box)
- inside
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, LATITUDE]
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, LONGITUDE]
- 40.8    # north latitude
- -74.1   # west longitude
- 40.6    # south latitude
- -73.9   # east longitude
```

#### Null / Empty

| Operator | Arguments | Description |
|----------|-----------|-------------|
| `is-null` | 1 expression | Is NULL |
| `not-null` | 1 expression | Is not NULL |
| `is-empty` | 1 string expression | Is NULL or empty string |
| `not-empty` | 1 string expression | Is not NULL and not empty string |

```yaml
- is-null
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, DISCOUNT]

- not-empty
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, EMAIL]
```

#### String

All string filter operators accept a `case-sensitive` option (default: `true`). They are N-ary — multiple values are combined with OR. The options map is always in the **second position** (after the operator, before the field).

| Operator | Arguments | Description |
|----------|-----------|-------------|
| `contains` | 2+ string values | Contains substring |
| `does-not-contain` | 2+ string values | Does not contain substring |
| `starts-with` | 2+ string values | Starts with prefix |
| `ends-with` | 2+ string values | Ends with suffix |

```yaml
# Single value, case-insensitive
- contains
- case-sensitive: false
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, TITLE]
- widget

# Multiple values (empty options)
- starts-with
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, NAME]
- John
- Jane

# Multiple values, case-insensitive
- starts-with
- case-sensitive: false
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, NAME]
- John
- Jane
- Charlie
```

#### Temporal

| Operator | Arguments | Description |
|----------|-----------|-------------|
| `time-interval` | temporal-field, n, unit | Relative time interval. `n` can be an integer, `current`, `last`, or `next`. |
| `relative-time-interval` | temporal-field, value, bucket, offset-value, offset-bucket | Relative interval with offset |

**Valid units** for `time-interval` and `relative-time-interval`: `millisecond`, `second`, `minute`, `hour`, `day`, `week`, `month`, `quarter`, `year` (truncation units only).

```yaml
# Last 30 days
- time-interval
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- -30
- day

# Current month
- time-interval
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- current
- month

# Last 30 days, offset by 1 month
- relative-time-interval
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- -30
- day
- -1
- month
```

#### Segment Reference

Reference a saved segment by entity_id:

```yaml
- segment
- {}
- aB3kLmN9pQrStUvWxYz1a
```

---

### Aggregation Functions

#### Basic

| Function | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `count` | none or 1 expression | integer | Count rows (with arg: count non-NULL) |
| `sum` | 1 numeric | numeric | Sum of values |
| `avg` | 1 numeric | float | Average |
| `min` | 1 orderable | same type | Minimum value |
| `max` | 1 orderable | same type | Maximum value |
| `distinct` | 1 expression | integer | Count of distinct values |

```yaml
# Count all rows
aggregation:
- - count
  - {}

# Sum with field
aggregation:
- - sum
  - {}
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]

# Multiple aggregations
aggregation:
- - count
  - {}
- - avg
  - {}
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
```

#### Cumulative

| Function | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `cum-count` | none or 1 expression | integer | Running count |
| `cum-sum` | 1 numeric | numeric | Running sum |

```yaml
aggregation:
- - cum-sum
  - {}
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
```

#### Statistical

| Function | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `stddev` | 1 numeric | float | Standard deviation |
| `var` | 1 numeric | float | Variance |
| `median` | 1 numeric | numeric | Median value |
| `percentile` | numeric, p (0.0–1.0) | numeric | Percentile value |

```yaml
# 90th percentile
aggregation:
- - percentile
  - {}
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
  - 0.9
```

#### Conditional

| Function | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `count-where` | 1 boolean clause | integer | Count rows matching condition |
| `sum-where` | numeric, boolean clause | numeric | Sum where condition is true |
| `distinct-where` | expression, boolean clause | integer | Count distinct where condition is true |
| `share` | 1 boolean clause | float (0–1) | Proportion of rows matching condition |

```yaml
# Count where
aggregation:
- - count-where
  - {}
  - - ">"
    - {}
    - - field
      - {}
      - [Sample Database, PUBLIC, ORDERS, TOTAL]
    - 100

# Share
aggregation:
- - share
  - {}
  - - =
    - {}
    - - field
      - {}
      - [Sample Database, PUBLIC, PRODUCTS, CATEGORY]
    - Widget
```

#### Named Aggregations

Aggregations can have a custom display name by setting `display-name` and/or `name` directly in the aggregation clause's options:

```yaml
aggregation:
- - sum
  - display-name: Total Revenue
    name: total_revenue
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
```

#### Metric and Measure References

A `metric` clause references a saved metric (a card with `type: metric`) by its entity_id:

```yaml
aggregation:
- - metric
  - {}
  - f1C68pznmrpN1F5xFDj6d           # entity_id of a metric card
```

A `measure` clause references a saved measure by its entity_id. Measures can reference other measures but cannot reference metrics:

```yaml
aggregation:
- - measure
  - {}
  - xK7mPqR2sT4uVwXyZ9a1b           # entity_id of a saved measure
```

---

### Expression Operators

#### Arithmetic

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `+` | 2+ numeric (or temporal + interval) | numeric / temporal | Addition |
| `-` | 1+ numeric (or temporal − interval) | numeric / interval | Subtraction (unary = negation) |
| `*` | 2+ numeric | numeric | Multiplication |
| `/` | 2+ numeric | float | Division (always returns float) |

**Note:** The `-` operator must be quoted as `"-"` in YAML when it appears as the first element of a list, to avoid being parsed as a list indicator.

```yaml
# Subtraction: TOTAL - TAX
expressions:
- - "-"
  - "lib/expression-name": Profit
  - - field
    - {}
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
  - - field
    - {}
    - [Sample Database, PUBLIC, ORDERS, TAX]

# Date arithmetic: CREATED_AT + 7 days
expressions:
- - +
  - "lib/expression-name": Due Date
  - - field
    - {}
    - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
  - - interval
    - {}
    - 7
    - day
```

#### Math Functions

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `abs` | 1 numeric | same type | Absolute value |
| `ceil` | 1 numeric | integer | Round up to integer |
| `floor` | 1 numeric | integer | Round down to integer |
| `round` | 1 numeric | integer | Round to nearest integer |
| `power` | base, exponent | numeric | Raise to power |
| `sqrt` | 1 numeric | float | Square root |
| `exp` | 1 numeric | float | Exponential (e^x) |
| `log` | 1 numeric | float | Natural logarithm |

```yaml
# Absolute value
- abs
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, DISCOUNT]

# Power
- power
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, RATING]
- 2

# Square root
- sqrt
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, PRICE]
```

#### String Functions

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `concat` | 2+ expressions | text | Concatenate strings |
| `substring` | str, start, length? | text | Extract substring (1-indexed) |
| `replace` | str, find, replace | text | Replace all occurrences |
| `regex-match-first` | str, regex | text | Extract first regex match |
| `split-part` | str, delimiter, position | text | Split and get Nth part |
| `trim` | 1 string | text | Trim whitespace (both ends) |
| `ltrim` | 1 string | text | Trim leading whitespace |
| `rtrim` | 1 string | text | Trim trailing whitespace |
| `upper` | 1 string | text | Convert to uppercase |
| `lower` | 1 string | text | Convert to lowercase |
| `length` | 1 string | integer | String length |
| `host` | 1 string (URL) | text | Extract host from URL |
| `domain` | 1 string (URL) | text | Extract domain from URL |
| `subdomain` | 1 string (URL) | text | Extract subdomain from URL |
| `path` | 1 string (URL) | text | Extract path from URL |

```yaml
# Concat
- concat
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, NAME]
- " <"
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, EMAIL]
- ">"

# Substring (characters 1-3)
- substring
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, TITLE]
- 1
- 3

# Replace
- replace
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, EMAIL]
- "@example.com"
- "@company.com"

# Regex match
- regex-match-first
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, EMAIL]
- "^[^@]+"

# Domain from URL
- domain
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PEOPLE, SOURCE]
```

#### Temporal Functions

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `now` | none | datetime | Current date and time |
| `today` | none | date | Today's date |
| `interval` | amount, unit | interval | Create a temporal interval |
| `datetime-add` | temporal, amount, unit | temporal | Add interval to date/time |
| `datetime-subtract` | temporal, amount, unit | temporal | Subtract interval from date/time |
| `datetime-diff` | datetime1, datetime2, unit | integer | Difference between two dates |
| `convert-timezone` | temporal, target-tz, source-tz? | temporal | Convert timezone |
| `get-year` | 1 temporal | integer | Extract year |
| `get-quarter` | 1 temporal | integer | Extract quarter (1–4) |
| `get-month` | 1 temporal | integer | Extract month (1–12) |
| `get-day` | 1 temporal | integer | Extract day of month |
| `get-hour` | 1 temporal | integer | Extract hour (0–23) |
| `get-minute` | 1 temporal | integer | Extract minute (0–59) |
| `get-second` | 1 temporal | integer | Extract second (0–59) |
| `get-day-of-week` | temporal, mode? | integer | Day of week. Mode: `iso` (Mon=1), `us` (Sun=1), `instance` |
| `get-week` | temporal, mode? | integer | Week number. Mode: `iso`, `us`, `instance` |
| `temporal-extract` | temporal, unit, mode? | integer | Generic extraction (see units below) |
| `month-name` | 1 integer (1–12) | text | Month name from number |
| `quarter-name` | 1 integer (1–4) | text | Quarter name from number |
| `day-name` | 1 integer | text | Day name from number |

Interval units for `datetime-add`, `datetime-subtract`: `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`, `second`, `millisecond`.

Difference units for `datetime-diff`: `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`, `second`.

Extraction units for `temporal-extract`: `year-of-era`, `quarter-of-year`, `month-of-year`, `week-of-year-iso`, `week-of-year-us`, `week-of-year-instance`, `day-of-month`, `day-of-week`, `day-of-week-iso`, `hour-of-day`, `minute-of-hour`, `second-of-minute`.

```yaml
# Add 7 days
- datetime-add
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- 7
- day

# Difference in months
- datetime-diff
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- - now
  - {}
- month

# Extract year
- get-year
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]

# Convert timezone
- convert-timezone
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, CREATED_AT]
- America/New_York
- UTC
```

#### Type Conversion

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `integer` | string or numeric | integer | Convert to integer |
| `float` | string | float | Convert to float |
| `text` | 1 expression | text | Convert to text |

```yaml
- integer
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, PRODUCTS, PRICE]
```

#### Conditional

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `case` | pairs of [condition, value], optional default expression | value type | Conditional expression (if/then/else). The default value is supplied as a 4th positional argument. |
| `if` | same as `case` | value type | Alias for `case` |
| `coalesce` | 2+ expressions | first non-null type | First non-null value |

```yaml
# Case expression
expressions:
- - case
  - "lib/expression-name": Price Tier
  - - - - ">"
        - {}
        - - field
          - {}
          - [Sample Database, PUBLIC, PRODUCTS, PRICE]
        - 100
      - Premium
    - - - "<="
        - {}
        - - field
          - {}
          - [Sample Database, PUBLIC, PRODUCTS, PRICE]
        - 20
      - Budget
  - Standard  # default (4th positional arg)

# Coalesce
- coalesce
- {}
- - field
  - {}
  - [Sample Database, PUBLIC, ORDERS, DISCOUNT]
- 0
```

#### Window Functions

Window functions can only be used inside the `aggregation` clause.

| Operator | Arguments | Returns | Description |
|----------|-----------|---------|-------------|
| `offset` | expression, n | same type | Value from n rows before (negative) or after (positive). |

```yaml
aggregation:
- - sum
  - {}
  - - field
    - base-type: type/Float
    - [Sample Database, PUBLIC, ORDERS, TOTAL]
- - offset
  - {}
  - - sum
    - {}
    - - field
      - base-type: type/Float
      - [Sample Database, PUBLIC, ORDERS, TOTAL]
  - -1
```

---

## Native Query

Native queries use plain SQL with Metabase template tags for dynamic values.

### Structure

```yaml
"lib/type": mbql/query
database: Sample Database
stages:
- "lib/type": mbql.stage/native
  native: SELECT * FROM PRODUCTS
  template-tags: {}
```

### Template Tags

Template tags are placeholders in native SQL queries (`{{tag_name}}`) that become interactive filters or dynamic references. They are defined in the `template-tags` map, where each key must match the tag's `name` property.

#### Common Properties

All template tags share these properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Tag type: `text`, `number`, `date`, `boolean`, `dimension`, `temporal-unit`, `card`, `snippet`, `table` |
| `name` | string | Yes | Tag name — must match the key in `template-tags` and the `{{name}}` in the SQL |
| `id` | string | Yes | UUID identifier |
| `display-name` | string | Yes | Label shown in the UI |

---

### `text`

A string variable. Metabase wraps the value in single quotes in the compiled SQL.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `default` | string | No | Default value |
| `required` | boolean | No | Whether a value must be provided |

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
      required: true
```

Compiled SQL (value `Widget`): `SELECT * FROM PRODUCTS WHERE CATEGORY = 'Widget'`

---

### `number`

A numeric variable. The value is inserted as-is (no quoting).

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `default` | number | No | Default value |
| `required` | boolean | No | Whether a value must be provided |

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

Compiled SQL (value `50`): `SELECT * FROM PRODUCTS WHERE PRICE > 50`

---

### `date`

A date variable. The value is wrapped in single quotes.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `default` | string | No | Default date value (ISO format) |
| `required` | boolean | No | Whether a value must be provided |

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

Compiled SQL (value `2024-01-01`): `SELECT * FROM ORDERS WHERE CREATED_AT > '2024-01-01'`

---

### `boolean`

A boolean variable. Metabase replaces the tag with `1 = 1` (true) or `1 <> 1` (false). When no value is provided, defaults to `1 = 1`.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `default` | boolean | No | Default value |
| `required` | boolean | No | Whether a value must be provided |

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

Compiled SQL (true): `SELECT * FROM PRODUCTS WHERE 1 = 1`
Compiled SQL (false): `SELECT * FROM PRODUCTS WHERE 1 <> 1`

---

### `dimension`

A field filter that maps a template tag to a specific database field. Metabase generates smart filter widgets (date pickers, category dropdowns) and replaces the tag with the appropriate SQL expression. The tag must be used in a `WHERE` clause context.

When no value is provided, the entire `WHERE {{tag}}` clause is omitted (the query runs unfiltered).

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `dimension` | array | Yes | Field clause: `[field, options, Field FK]` (see [Field References](#field-references)) |
| `widget-type` | string | Yes | Filter widget type — any value from [Parameter Types](#parameter-types) |
| `default` | any | No | Default filter value |
| `required` | boolean | No | Whether a value must be provided |
| `options` | map | No | Options appended to the generated filter clause (e.g., `{case-sensitive: false}`) |

```yaml
native:
  query: "SELECT * FROM PRODUCTS WHERE {{category_filter}}"
  template-tags:
    category_filter:
      type: dimension
      name: category_filter
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Category
      dimension:
      - field
      - {}
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - CATEGORY
      widget-type: string/=
      default: null
```

Compiled SQL (`widget-type: string/=`, value `Widget`): `SELECT * FROM PRODUCTS WHERE CATEGORY = 'Widget'`

Compiled SQL (`widget-type: date/range`, value `2024-01-01~2024-12-31`): `SELECT * FROM ORDERS WHERE CREATED_AT >= '2024-01-01' AND CREATED_AT < '2025-01-01'`

---

### `temporal-unit`

A temporal grouping variable. Metabase replaces the tag with a `DATE_TRUNC(unit, column)` expression. The user selects a temporal granularity (month, quarter, year, etc.) from a dropdown.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `dimension` | array | Yes | Field clause: `[field, options, Field FK]` — the temporal column to group |
| `default` | string | No | Default temporal unit (e.g., `month`) |
| `alias` | string | No | Overrides the SQL column name used inside the generated expression. By default Metabase uses the column name from `dimension` (e.g., `CREATED_AT`). When the SQL uses a table alias, set `alias` to match so the generated expression references the correct name. |

Without `alias` — Metabase uses the column name from `dimension` (`CREATED_AT`):

```yaml
native:
  query: "SELECT {{created_at}} AS created_at, COUNT(*) FROM ORDERS GROUP BY {{created_at}}"
  template-tags:
    created_at:
      type: temporal-unit
      name: created_at
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Created At
      default: month
      dimension:
      - field
      - {}
      - - Sample Database
        - PUBLIC
        - ORDERS
        - CREATED_AT
```

Compiled SQL (value `month`): `SELECT DATE_TRUNC('month', CREATED_AT) AS created_at, COUNT(*) FROM ORDERS GROUP BY DATE_TRUNC('month', CREATED_AT)`

With `alias` — when the query uses a table alias (`o`), set `alias` so the generated expression uses `o.CREATED_AT` instead of the fully-qualified column name:

```yaml
native:
  query: "SELECT {{created_at}} AS created_at, COUNT(*) FROM ORDERS o GROUP BY {{created_at}}"
  template-tags:
    created_at:
      type: temporal-unit
      name: created_at
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Created At
      default: month
      alias: o.CREATED_AT
      dimension:
      - field
      - {}
      - - Sample Database
        - PUBLIC
        - ORDERS
        - CREATED_AT
```

Compiled SQL (value `month`): `SELECT DATE_TRUNC('month', o.CREATED_AT) AS created_at, COUNT(*) FROM ORDERS o GROUP BY DATE_TRUNC('month', o.CREATED_AT)`

---

### `card`

Reference a saved card (question) as a CTE subquery using `{{#<numeric_id>-<slug>}}` syntax. The SQL template uses the card's numeric ID; the `card-id` property stores the card's entity_id (NanoID) for portability. Metabase replaces the tag with the card's query wrapped in a `WITH` clause.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `card-id` | string | Yes | Card FK (entity_id of the referenced card) |

Note: `default` and `required` are not applicable for card tags.

```yaml
native:
  query: "SELECT * FROM {{#42-products_question}} WHERE PRICE > 50"
  template-tags:
    "#42-products_question":
      type: card
      name: "#42-products_question"
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Products Question
      card-id: f1C68pznmrpN1F5xFDj6d
```

Compiled SQL (assuming the card's query is `SELECT * FROM PUBLIC.PRODUCTS`):

```sql
WITH products_question AS (SELECT * FROM PUBLIC.PRODUCTS)
SELECT * FROM products_question WHERE PRICE > 50
```

---

### `snippet`

Reference a reusable SQL snippet using `{{snippet: Snippet Name}}` syntax. Metabase replaces the tag with the snippet's SQL content inline.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `snippet-name` | string | Yes | Name of the snippet |
| `snippet-id` | string | No | Snippet FK (entity_id of the snippet) |

Note: `default` and `required` are not applicable for snippet tags.

```yaml
native:
  query: "SELECT * FROM ORDERS WHERE {{snippet: Active Order Filter}}"
  template-tags:
    "snippet: Active Order Filter":
      type: snippet
      name: "snippet: Active Order Filter"
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: "Snippet: Active Order Filter"
      snippet-name: Active Order Filter
      snippet-id: xK7mPqR2sT4uVwXyZ9a1b
```

Compiled SQL (snippet content: `STATUS = 'active' AND TOTAL > 0`):

```sql
SELECT * FROM ORDERS WHERE STATUS = 'active' AND TOTAL > 0
```

---

### `table`

Reference a table dynamically. The user selects a table from a dropdown and Metabase replaces the tag with the fully qualified table name.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `table-id` | array | Yes | Table FK `[database, schema, table]` |
| `emit-alias` | boolean | No | Whether to emit the table name as an alias |

```yaml
native:
  query: "SELECT * FROM {{source_table}}"
  template-tags:
    source_table:
      type: table
      name: source_table
      id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
      display-name: Source Table
      table-id:
      - Sample Database
      - PUBLIC
      - PRODUCTS
```

Compiled SQL (with `PUBLIC.PRODUCTS` selected): `SELECT * FROM PUBLIC.PRODUCTS`

---

## Visualization Settings

Visualization settings control how query results are displayed. They are stored in the `visualization_settings` field of Cards and DashboardCards. DashboardCard visualization settings override the card's own settings and can additionally include click behaviors.

### Common Settings

| Setting | Type | Description |
|---------|------|-------------|
| `column_settings` | map | Per-column formatting keyed by column reference string |
| `"dashcard.background"` | boolean | Show/hide dashcard background (dashcards only) |

### Graph Settings

Apply to `line`, `bar`, `area`, `combo`, `scatter`, `waterfall`, `row`, `boxplot` displays.

| Setting | Type | Description |
|---------|------|-------------|
| `"graph.show_values"` | boolean | Show values on data points |
| `"graph.label_values_frequency"` | string | Value label frequency: `"fit"`, `"all"` |
| `"graph.show_stack_values"` | string | `"total"`, `"individual"`, `"all"` |
| `"graph.x_axis.title_text"` | string | X-axis title |
| `"graph.x_axis.scale"` | string | `"ordinal"`, `"histogram"`, `"timeseries"`, `"linear"`, `"pow"`, `"log"` |
| `"graph.x_axis.axis_enabled"` | boolean/string | `true`, `false`, `"compact"`, `"rotate-45"`, `"rotate-90"` |
| `"graph.y_axis.title_text"` | string | Y-axis title |
| `"graph.y_axis.scale"` | string | `"linear"`, `"pow"`, `"log"` |
| `"graph.y_axis.auto_range"` | boolean | Auto-scale Y axis |
| `"graph.y_axis.min"` | number | Y-axis minimum (when auto_range is false) |
| `"graph.y_axis.max"` | number | Y-axis maximum |
| `"graph.show_goal"` | boolean | Show goal line |
| `"graph.goal_value"` | number | Goal line value |
| `"graph.goal_label"` | string | Goal line label |
| `"graph.show_trendline"` | boolean | Show trend line |
| `"graph.dimensions"` | array | Dimension column names |
| `"graph.metrics"` | array | Metric column names |
| `"graph.series_order"` | array | Series display order |
| `"graph.max_categories_enabled"` | boolean | Limit number of categories |
| `"graph.max_categories"` | number | Maximum categories shown |
| `"graph.other_category_aggregation_fn"` | string | `"sum"`, `"avg"`, `"min"`, `"max"` |
| `"stackable.stack_type"` | string | `null`, `"stacked"`, `"normalized"` |

### Series Settings

Per-series overrides keyed by series name:

```yaml
series_settings:
  Revenue:
    display: line
    color: "#509EE3"
    "line.style": solid           # "solid", "dashed", "dotted"
    "line.size": normal           # "S", "M", "L"
    "line.interpolate": linear    # "linear", "cardinal", "step-before", "step-after"
    "line.missing": interpolate   # "interpolate", "zero", "none"
    "line.marker_enabled": true
    axis: left                    # "left", "right"
    show_series_values: true
```

### Table Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"table.columns"` | array | Column order and visibility — each entry: `{name, enabled}` |
| `"table.column_formatting"` | array | Conditional formatting rules |
| `"table.cell_column"` | string | Column to use for cell values (in pivot mode) |
| `"table.pivot"` | boolean | Enable pivot mode |
| `"table.pivot_column"` | string | Column to pivot on |

### Conditional Formatting

Each rule in `"table.column_formatting"`:

```yaml
table.column_formatting:
- columns:
  - Total
  type: single                    # "single" or "range"
  operator: ">"                   # "=", "!=", "<", ">", "<=", ">=", "is-null", "not-null"
  value: 100
  color: "#84BB4C"
  highlight_row: false
- columns:
  - Rating
  type: range
  colors:
  - "#ED6E6E"
  - "#F9CF48"
  - "#84BB4C"
  min_type: custom                # "min", "max", "custom"
  min_value: 1
  max_type: custom
  max_value: 5
```

### Pivot Table Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"pivot_table.column_split"` | object | `{rows: [...column_names], columns: [...column_names], values: [...column_names]}` |
| `"pivot_table.collapsed_rows"` | object | `{rows: [...collapsed_keys], value: []}` |
| `"pivot_table.show_row_totals"` | boolean | Show row totals |
| `"pivot_table.show_column_totals"` | boolean | Show column totals |

### Pie Chart Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"pie.dimension"` | string | Dimension column |
| `"pie.metric"` | string | Metric column |
| `"pie.show_legend"` | boolean | Show legend |
| `"pie.show_total"` | boolean | Show total in center |
| `"pie.percent_visibility"` | string | `"off"`, `"legend"`, `"inside"`, `"both"` |
| `"pie.slice_threshold"` | number | Minimum percentage to show as separate slice |
| `"pie.colors"` | object | Color map keyed by dimension value |

### Scalar / Number Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"scalar.field"` | string | Field to display |
| `"scalar.switch_positive_negative"` | boolean | Invert positive/negative colors |
| `"scalar.compact_primary_number"` | string | `"auto"`, `"yes"`, `"no"` |

### Smart Scalar Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"scalar.comparisons"` | array | Comparison definitions (see below) |

Comparison types:

```yaml
scalar.comparisons:
- id: comp1
  type: previousPeriod            # vs. previous time period
- id: comp2
  type: previousValue             # vs. previous value
- id: comp3
  type: periodsAgo                # vs. N periods ago
  value: 12
- id: comp4
  type: staticNumber              # vs. fixed number
  value: 1000
  label: Target
```

### Gauge Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"gauge.segment_colors"` | array | Segment colors |
| `"gauge.segments"` | array | Gauge segments with `min`, `max`, `color`, `label` |

### Map Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"map.type"` | string | `"region"`, `"pin"`, `"grid"` |
| `"map.latitude_column"` | string | Latitude column name |
| `"map.longitude_column"` | string | Longitude column name |
| `"map.metric_column"` | string | Metric column for coloring |
| `"map.region"` | string | Region map identifier |
| `"map.colors"` | array | Color scale |
| `"map.zoom"` | number | Initial zoom level |
| `"map.center_latitude"` | number | Center latitude |
| `"map.center_longitude"` | number | Center longitude |
| `"map.pin_type"` | string | `"tiles"`, `"markers"`, `"heat"` |

### Funnel Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"funnel.dimension"` | string | Dimension column |
| `"funnel.metric"` | string | Metric column |
| `"funnel.type"` | string | `"funnel"` or `"bar"` |
| `"funnel.rows"` | array | Row order definitions |

### Waterfall Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"waterfall.increase_color"` | string | Color for increases |
| `"waterfall.decrease_color"` | string | Color for decreases |
| `"waterfall.total_color"` | string | Color for total bar |
| `"waterfall.show_total"` | boolean | Show total bar |

### Sankey Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"sankey.source"` | string | Source column |
| `"sankey.target"` | string | Target column |
| `"sankey.value"` | string | Value column |
| `"sankey.node_align"` | string | `"left"`, `"right"`, `"center"`, `"justify"` |
| `"sankey.show_edge_labels"` | boolean | Show labels on edges |

### BoxPlot Settings

| Setting | Type | Description |
|---------|------|-------------|
| `"boxplot.whisker_type"` | string | `"min-max"`, `"tukey"`, `"percentile"` |
| `"boxplot.points_mode"` | string | `"none"`, `"outliers"`, `"all"` |
| `"boxplot.show_mean"` | boolean | Show mean marker |

### Column Settings

Per-column formatting stored in `column_settings`, keyed by column name (e.g., `["name","COLUMN_NAME"]`):

```yaml
column_settings:
  '["name","TOTAL"]':
    number_style: currency
    currency: USD
    currency_style: symbol        # "symbol", "code", "name"
    number_separators: ".,"       # decimal + thousands separator
    decimals: 2
    scale: 1                      # multiply values by this factor
    prefix: ""
    suffix: ""
    column_title: "Total Revenue"
  '["name","CREATED_AT"]':
    date_style: "MMMM D, YYYY"   # moment.js format
    date_separator: "/"
    date_abbreviate: false
    time_enabled: null            # null, "minutes", "seconds", "milliseconds"
    time_style: "h:mm A"         # "HH:mm", "h:mm A", etc.
  '["name","EMAIL"]':
    view_as: link                 # "link", "image", "email", "auto"
    link_text: "Send email"
    link_url: "mailto:{{value}}"
```

### Virtual Card Settings

For dashcards with `card_id: null`:

```yaml
# Heading
visualization_settings:
  virtual_card:
    display: heading
  text: "Section Title"

# Text (markdown)
visualization_settings:
  virtual_card:
    display: text
  text: "**Bold** and _italic_ markdown content"

# Text with parameter placeholders. Each `{{name}}` is wired to a dashboard
# parameter through `parameter_mappings` on the dashcard, with target
# `[text-tag, name]`. At render time the placeholder is replaced with the
# parameter's current value.
visualization_settings:
  virtual_card:
    display: text
  text: "Showing results for {{product_category}}"

# Link (URL)
visualization_settings:
  virtual_card:
    display: link
  link:
    url: "https://example.com"

# Link (entity reference)
visualization_settings:
  virtual_card:
    display: link
  link:
    entity:
      id: f1C68pznmrpN1F5xFDj6d
      model: question              # "question", "dashboard", "collection", "database", "table"

# iFrame
visualization_settings:
  virtual_card:
    display: iframe
  iframe: '<iframe src="https://example.com/embed"></iframe>'

# Placeholder
visualization_settings:
  virtual_card:
    display: placeholder
```

---

## Click Behavior

Click behaviors define what happens when a user clicks on a dashboard card or a specific column within a table. They are stored in `visualization_settings.click_behavior` on dashcards, or per-column in `visualization_settings.column_settings[column].click_behavior`.

### Click Behavior Types

| Type | Description |
|------|-------------|
| `actionMenu` | Default drill-through menu (no explicit config needed) |
| `crossfilter` | Filter the dashboard using the clicked value |
| `link` | Navigate to a URL, question, or dashboard |

### Crossfilter

Maps clicked column values to dashboard parameters to filter other cards:

```yaml
click_behavior:
  type: crossfilter
  parameterMapping:
    a1b2c3d4-uuid-of-param:
      id: a1b2c3d4-uuid-of-param
      source:
        id: CATEGORY
        name: Category
        type: column
      target:
        id: a1b2c3d4-uuid-of-param
        type: parameter
```

### Link to URL

Navigate to an arbitrary URL. Supports template variables:

- `{{column_name}}` — value of the clicked row's column
- `{{filter:parameter_name}}` — dashboard parameter value

```yaml
click_behavior:
  type: link
  linkType: url
  linkTemplate: "https://example.com/orders/{{ORDER_ID}}?status={{filter:status}}"
  linkTextTemplate: "View Order {{ORDER_ID}}"
```

### Link to Dashboard

Navigate to another dashboard, optionally mapping values to the target dashboard's parameters:

```yaml
click_behavior:
  type: link
  linkType: dashboard
  targetId: Q_jD-f-9clKLFZ2TfUG2h     # entity_id of target dashboard
  parameterMapping:
    target-param-uuid:
      id: target-param-uuid
      source:
        id: USER_ID
        name: User ID
        type: column
      target:
        id: target-param-uuid
        type: parameter
```

### Link to Question

Navigate to another question/card:

```yaml
click_behavior:
  type: link
  linkType: question
  targetId: f1C68pznmrpN1F5xFDj6d     # entity_id of target card
  parameterMapping:
    target-dimension:
      id: target-dimension
      source:
        id: PRODUCT_ID
        name: Product ID
        type: column
      target:
        id: target-dimension
        type: dimension
        dimension:
        - dimension
        - - field
          - {}
          - - Sample Database
            - PUBLIC
            - PRODUCTS
            - ID
```

### Parameter Mapping Structure

Each entry in `parameterMapping`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Parameter ID or dimension reference |
| `source` | object | Where the value comes from |
| `source.id` | string | Column name or parameter ID |
| `source.name` | string | Display name |
| `source.type` | string | `"column"` or `"parameter"` |
| `target` | object | Where the value goes |
| `target.id` | string | Target parameter ID or dimension |
| `target.type` | string | `"parameter"`, `"dimension"`, or `"variable"` |
| `target.dimension` | array | Parameter target (same format as dashboard parameter mapping targets — see [Parameter Targets](#parameter-targets)) |

---

## Parameter

A parameter is a filter control on a dashboard or card. Parameters are not standalone entities — they are embedded in the `parameters` array of their parent.

On **dashboards**, parameters define filter controls shown at the top of the dashboard. They are wired to card columns via `parameter_mappings` on each dashcard.

On **cards**, parameters are typically empty `[]` for MBQL queries. For native queries, they expose template tag variables as filter controls.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier within the dashboard or card. UUIDs are recommended, but any unique non-empty string is accepted (e.g., `9d9cddd4`). |
| `name` | string | Yes | Display name |
| `slug` | string | Yes | URL-friendly identifier |
| `type` | string | Yes | Filter widget type (see below) |
| `default` | any | No | Default value |
| `required` | boolean | No | Whether a value is required |
| `sectionId` | string | No | Parameter section grouping |
| `temporal_units` | array | No | Allowed temporal units (for `temporal-unit` type) |
| `values_query_type` | string | No | `"list"`, `"search"`, or `"none"` — controls how values are fetched |
| `values_source_type` | string | No | `null`, `"card"`, or `"static-list"` — where values come from |
| `values_source_config` | map | No | Source configuration (see below) |

### Values Source Configuration

When `values_source_type` is `"static-list"`, the config provides inline values:

```yaml
values_source_type: static-list
values_source_config:
  values:
  - [1, "One"]
  - [2, "Two"]
```

When `values_source_type` is `"card"`, the config references a card:

```yaml
values_source_type: card
values_source_config:
  card_id: f1C68pznmrpN1F5xFDj6d
  value_field:
  - field
  - {}
  - - Sample Database
    - PUBLIC
    - PRODUCTS
    - ID
  label_field:
  - field
  - {}
  - - Sample Database
    - PUBLIC
    - PRODUCTS
    - TITLE
```

| Property | Type | Description |
|----------|------|-------------|
| `values` | array | Static list of `[value, label]` pairs (for `static-list`) |
| `card_id` | string | Card entity_id to source values from (for `card`) |
| `value_field` | array | Field clause for extracting values from card results |
| `label_field` | array | Field clause for extracting display labels from card results |

### Parameter Types

| Type | Description |
|------|-------------|
| `string/=` | String equals |
| `string/!=` | String not equals |
| `string/contains` | String contains |
| `string/does-not-contain` | String does not contain |
| `string/starts-with` | String starts with |
| `string/ends-with` | String ends with |
| `number/=` | Number equals |
| `number/!=` | Number not equals |
| `number/>=` | Number greater than or equal |
| `number/<=` | Number less than or equal |
| `number/between` | Number between |
| `date/single` | Single date |
| `date/range` | Date range |
| `date/month-year` | Month and year |
| `date/quarter-year` | Quarter and year |
| `date/relative` | Relative date (e.g., "last 7 days") |
| `date/all-options` | All date filter options |
| `boolean/=` | Boolean equals |
| `temporal-unit` | Temporal unit selector |
| `none` | No filter widget (unconfigured) |

### sectionId

The `sectionId` property restricts which columns are available for mapping in the UI. It is optional — when omitted, Metabase infers it from the parameter type.

| sectionId | Available columns | Typical parameter types |
|-----------|-------------------|------------------------|
| `string` | Text columns | `string/=`, `string/!=`, `string/contains`, etc. |
| `number` | Numeric columns | `number/=`, `number/!=`, `number/between`, etc. |
| `date` | Date/time columns | `date/single`, `date/range`, `date/relative`, etc. |
| `boolean` | Boolean columns | `boolean/=` |
| `temporal-unit` | Temporal unit selector | `temporal-unit` |
| `id` | Only PK and FK columns | `number/=` or `string/=` with `sectionId: id` |
| `location` | Only location columns (country, city, etc.) | `string/=` with `sectionId: location` |

Use `sectionId: id` to make a `number/=` or `string/=` parameter map only to primary key and foreign key columns. Use `sectionId: location` to restrict mapping to location-typed columns.

### Parameter Targets

Parameter targets specify which column or variable a parameter maps to. The outer wrapper is `dimension`, `variable`, or `text-tag`:

- **`dimension`** — for MBQL column references (`field`, `expression`) and for native template tags of type `dimension` or `temporal-unit`
- **`variable`** — for native template tags of type `text`, `number`, `date`, or `boolean`
- **`text-tag`** — for placeholders inside text/heading virtual cards (see [Virtual Card Settings](#virtual-card-settings))

An optional third element `{stage-number: N}` or `null` can specify which query stage the target belongs to (0 = first stage).

**Important:** Field and expression references inside parameter targets use **legacy format** (`[field, Field-FK, null-or-options]`, `[expression, name]`), not pMBQL format. This differs from references inside `dataset_query.stages`, which use pMBQL format (`[field, options, Field-FK]`).

**MBQL — field reference:**

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

**MBQL — multi-stage field reference (column name, not Field FK):**

```yaml
target:
- dimension
- - field
  - CATEGORY
  - null
- stage-number: 1
```

**MBQL — expression reference:**

```yaml
target:
- dimension
- - expression
  - Profit
```

**Native — field filter (`dimension`) or time grouping (`temporal-unit`) template tag:**

```yaml
target:
- dimension
- - template-tag
  - category_filter
```

**Native — other template tags (`text`, `number`, `date`, `boolean`):**

```yaml
target:
- variable
- - template-tag
  - min_price
```

**Text card placeholder:**

```yaml
target:
- text-tag
- product_category
```

---

## Collection

A collection is a folder-like container for organizing cards, dashboards, and other entities. Collection hierarchy is reflected in the directory structure.

> **Critical:** Subcollections **must** set `parent_id` to the `entity_id` of their parent collection. Without `parent_id`, a collection is treated as a root-level collection regardless of where its file is located on disk. All items inside a collection (cards, dashboards, documents, etc.) **must** set their `collection_id` to that collection's `entity_id` to appear within it.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Collection name |
| `entity_id` | string | Yes | NanoID identifier |
| `serdes/meta` | array | Yes | Identity path with `model: Collection` |
| `description` | string | No | Description |
| `slug` | string | No | URL-friendly name |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `archived_directly` | boolean | No | Archived directly vs. inherited |
| `type` | string | No | `null` or `"instance-analytics"` |
| `namespace` | string | No | `null`, `"transforms"`, or `"snippets"` |
| `authority_level` | string | No | `null` or `"official"` |
| `parent_id` | string | No | Collection FK (entity_id of parent). **Must** be set for subcollections; `null`/omitted = root-level collection |
| `personal_owner_id` | string | No | User FK (email) for personal collections |
| `is_sample` | boolean | No | Sample collection flag |
| `created_at` | string | No | ISO 8601 timestamp |

### Example

**Root collection:**

```yaml
name: Minimal
entity_id: cOlMiNiMaL000ExAmPlx2
slug: minimal
serdes/meta:
- id: cOlMiNiMaL000ExAmPlx2
  label: minimal
  model: Collection
```

**Subcollection** (with `parent_id`):

```yaml
name: Reports
entity_id: cOlRePorTs000ExAmPlx2
parent_id: cOlMiNiMaL000ExAmPlx2
serdes/meta:
- id: cOlRePorTs000ExAmPlx2
  label: reports
  model: Collection
```

---

## Card

A card represents a Question, Model, or Metric in Metabase. Cards are the primary way to save and share queries. Each card holds a `dataset_query` — see [MBQL Query](#mbql-query) and [Native Query](#native-query).

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Card name |
| `entity_id` | string | Yes | NanoID identifier |
| `display` | string | Yes | Visualization type (see below) |
| `creator_id` | string | Yes | User FK (email) |
| `dataset_query` | object | Yes | Query definition — MBQL or native |
| `visualization_settings` | map | Yes | Display settings (can be empty `{}`) |
| `serdes/meta` | array | Yes | Identity path with `model: Card` |
| `description` | string | No | Description |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `archived_directly` | boolean | No | Archived directly vs. inherited |
| `type` | string | No | `"question"`, `"model"`, or `"metric"` |
| `collection_id` | string | No | Collection FK (entity_id). **Set this to place the card in a collection**; `null`/omitted = root collection. When `dashboard_id` or `document_id` is set, must match the parent's `collection_id` |
| `collection_position` | integer | No | Position within collection |
| `collection_preview` | boolean | No | Show preview in collection (default: `true`) |
| `dashboard_id` | string | No | Dashboard FK (entity_id). Card's `collection_id` must match the dashboard's `collection_id` |
| `document_id` | string | No | Document FK (entity_id). Card's `collection_id` must match the document's `collection_id` |
| `database_id` | string | No | Database FK (database name). Only included when not derivable from `dataset_query` (e.g., empty query); re-derived from the query on import when present. |
| `parameters` | array | No | Card parameters (see [Parameter](#parameter)) |
| `parameter_mappings` | array | No | Unused, always empty `[]` |
| `result_metadata` | array | No | Query result column metadata |
| `enable_embedding` | boolean | No | Embedding enabled |
| `embedding_params` | map | No | Embedding parameter config |
| `embedding_type` | string | No | `null`, `"sdk"`, `"standalone"` |
| `public_uuid` | string | No | Public sharing UUID |
| `made_public_by_id` | string | No | User FK (email) |
| `metabase_version` | string | No | Metabase version that created the card |
| `card_schema` | integer | No | Internal card schema version |
| `created_at` | string | No | ISO 8601 timestamp |

### Display Types

`table`, `bar`, `line`, `area`, `row`, `pie`, `scalar`, `smartscalar`, `combo`, `pivot`, `funnel`, `map`, `scatter`, `waterfall`, `progress`, `gauge`, `object`, `list`, `heading`, `text`, `link`, `iframe`, `action`, `sankey`, `boxplot`, `number`.

### Card Parameters

Card parameters define what filter inputs the card accepts. For MBQL queries, `parameters` is typically empty `[]`. For native queries, card parameters expose template tag variables as filter controls with the same shape as dashboard parameters (see [Parameter](#parameter)).

### Example

```yaml
name: Products question
entity_id: f1C68pznmrpN1F5xFDj6d
display: table
creator_id: internal@metabase.com
type: question
dataset_query:
  "lib/type": mbql/query
  database: Sample Database
  stages:
  - "lib/type": mbql.stage/mbql
    source-table:
    - Sample Database
    - PUBLIC
    - PRODUCTS
visualization_settings: {}
collection_id: M-Q4pcV0qkiyJ0kiSWECl
parameters: []
parameter_mappings: []
serdes/meta:
- id: f1C68pznmrpN1F5xFDj6d
  label: products_question
  model: Card
```

---

## Dashboard

A dashboard is a collection of cards arranged in a grid layout. Dashboards contain dashboard cards (`dashcards`), parameters for filtering, and optional tabs.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Dashboard name |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `serdes/meta` | array | Yes | Identity path with `model: Dashboard` |
| `description` | string | No | Description |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `archived_directly` | boolean | No | Archived directly vs. inherited |
| `collection_id` | string | No | Collection FK (entity_id). **Set this to place the dashboard in a collection**; `null`/omitted = root collection |
| `collection_position` | integer | No | Position within collection |
| `position` | integer | No | Display position |
| `auto_apply_filters` | boolean | No | Auto-apply filter changes (default: `true`) |
| `width` | string | No | `"fixed"` or `"full"` |
| `enable_embedding` | boolean | No | Embedding enabled |
| `embedding_params` | map | No | Embedding parameter config |
| `embedding_type` | string | No | `null`, `"sdk"`, `"standalone"` |
| `public_uuid` | string | No | Public sharing UUID |
| `made_public_by_id` | string | No | User FK (email) |
| `show_in_getting_started` | boolean | No | Show in getting started (default: `false`) |
| `caveats` | string | No | Known limitations |
| `points_of_interest` | string | No | Noteworthy features |
| `initially_published_at` | string | No | ISO 8601 timestamp |
| `parameters` | array | No | Dashboard filter parameters (see [Parameter](#parameter)) |
| `tabs` | array | No | Dashboard tabs (see below) |
| `dashcards` | array | No | Dashboard cards (see below) |
| `created_at` | string | No | ISO 8601 timestamp |

### Dashboard Grid

The dashboard uses a 24-column grid. Cards are positioned using `col` (0–23) and `row` (0+) with sizes `size_x` and `size_y` in grid units. Cards cannot overlap. Constraint: `col + size_x <= 24`.

Default card sizes by visualization type:

| Display | Default (w × h) | Minimum (w × h) |
|---------|-----------------|-----------------|
| `table`, `list`, `pivot`, `object` | 12 × 9 | 4 × 3 (list: 12 × 6) |
| `bar`, `line`, `area`, `row`, `scatter`, `combo`, `funnel`, `progress`, `boxplot` | 12 × 6 | 4 × 3 |
| `pie` | 12 × 8 | 4 × 3 |
| `waterfall` | 14 × 6 | 4 × 3 |
| `sankey` | 16 × 10 | 4 × 3 |
| `map`, `gauge` | 12 × 6 | 4 × 3 |
| `iframe` | 12 × 8 | 4 × 3 |
| `scalar`, `smartscalar` | 6 × 3 | 2 × 2 |
| `number` | 6 × 3 | 2 × 2 |
| `heading` | 24 × 1 | 1 × 1 |
| `text` | 12 × 3 | 1 × 1 |
| `link` | 8 × 1 | 1 × 1 |
| `action` | 4 × 1 | 1 × 1 |

### Dashboard Tabs

Tabs organize dashboard content into separate pages. Each dashcard can be assigned to a tab via `dashboard_tab_id`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID identifier |
| `name` | string | Yes | Tab name |
| `position` | integer | Yes | Display order (ascending) |

Deleting a tab deletes all dashcards assigned to it.

### Dashboard Parameters

Dashboard parameters define filter controls that appear at the top of the dashboard. They are wired to specific card columns via `parameter_mappings` on each dashcard. See [Parameter](#parameter) for the full schema.

### DashboardCard

A dashboard card places a card (question) on the dashboard grid. Most dashboard cards reference an existing card via `card_id`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID identifier |
| `card_id` | string | No | Card FK (entity_id), `null` for virtual cards (text, heading, link, iframe, placeholder) |
| `row` | integer | Yes | Grid row position (0+) |
| `col` | integer | Yes | Grid column position (0–23) |
| `size_x` | integer | Yes | Width in grid units (1–24) |
| `size_y` | integer | Yes | Height in grid units (1+) |
| `serdes/meta` | array | Yes | Identity path: Dashboard → DashboardCard |
| `dashboard_tab_id` | string | No | Tab entity_id, `null` for untabbed |
| `inline_parameters` | array | No | List of parameter UUIDs to display directly on this dashcard |
| `parameter_mappings` | array | No | Parameter-to-card mappings (see below) |
| `series` | array | No | Overlay series (see below) |
| `visualization_settings` | map | No | Display settings |
| `created_at` | string | No | ISO 8601 timestamp |

### ParameterMapping

Connects a dashboard parameter to a specific card column or variable. Each mapping lives in the `parameter_mappings` array of a DashboardCard. The `target` field specifies which column or variable the parameter maps to — see [Parameter Targets](#parameter-targets).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `card_id` | string | No | Card FK (entity_id). Omit for mappings on virtual cards (e.g., text-tag placeholders). |
| `parameter_id` | string | Yes | Matches a dashboard parameter's `id` |
| `target` | array | Yes | Parameter target |

### DashboardCardSeries

Overlays additional cards on the same dashboard card visualization (e.g., multiple lines on one chart).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `card_id` | string | Yes | Card FK (entity_id of the series card) |
| `position` | integer | Yes | Display order (starting at 0) |

### Example

```yaml
name: Orders Overview
entity_id: Q_jD-f-9clKLFZ2TfUG2h
creator_id: internal@metabase.com
width: fixed
auto_apply_filters: true
parameters:
- id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  name: Category
  slug: category
  type: string/=
tabs:
- entity_id: tAb1dEntIdHere1234x5
  name: Overview
  position: 0
- entity_id: tAb2dEntIdHere1234x5
  name: Details
  position: 1
dashcards:
- entity_id: UkpFcfUZMZt9ehChwnrAO
  card_id: f1C68pznmrpN1F5xFDj6d
  dashboard_tab_id: tAb1dEntIdHere1234x5
  row: 0
  col: 0
  size_x: 12
  size_y: 6
  parameter_mappings:
  - card_id: f1C68pznmrpN1F5xFDj6d
    parameter_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    target:
    - dimension
    - - field
      - - Sample Database
        - PUBLIC
        - PRODUCTS
        - CATEGORY
      - null
  series:
  - card_id: OMuZ0wHe2O5Z_59-cLmn4
    position: 0
  visualization_settings: {}
  serdes/meta:
  - id: Q_jD-f-9clKLFZ2TfUG2h
    model: Dashboard
  - id: UkpFcfUZMZt9ehChwnrAO
    model: DashboardCard
serdes/meta:
- id: Q_jD-f-9clKLFZ2TfUG2h
  label: orders_overview
  model: Dashboard
```

---

## Document

A document is a rich-text page that can contain prose, headings, lists, embedded cards/queries, and references to other entities. Documents use a [ProseMirror](https://prosemirror.net/)-compatible tree structure stored as JSON.

Cards can be nested under a document via `card.document_id`, similar to how cards nest under dashboards. Embedded cards appear inline within the document content as `cardEmbed` nodes.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Document name (1-254 characters) |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `document` | object | Yes | ProseMirror AST (see Document Nodes below) |
| `serdes/meta` | array | Yes | Identity path with `model: Document` |
| `content_type` | string | No | Always `"application/json+vnd.prose-mirror"` |
| `description` | string | No | Description |
| `collection_id` | string | No | Collection FK (entity_id). **Set this to place the document in a collection**; `null`/omitted = root collection |
| `collection_position` | integer | No | Position within collection |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `archived_directly` | boolean | No | Archived directly vs. inherited |
| `public_uuid` | string | No | Public sharing UUID |
| `made_public_by_id` | string | No | User FK (email) |
| `view_count` | integer | No | Number of times viewed |
| `created_at` | string | No | ISO 8601 timestamp |

### Document Nodes

The `document` field contains a recursive tree of nodes. The root node is always `type: doc`.

#### Node Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Node type name (see Node Types below) |
| `content` | array | No | Child nodes (recursive) |
| `attrs` | map | No | Node-specific attributes (see Node Types below) |
| `text` | string | No | Text content (only for `text` nodes) |
| `marks` | array | No | Inline formatting marks (only for `text` nodes) |

#### Mark Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Mark type: `bold`, `italic`, `code`, `link`, `underline`, `strike` |
| `attrs` | map | No | Mark attributes (e.g., `href` for `link` marks) |

#### Node Types

**Block nodes (no attrs):**

| Node Type | Description |
|-----------|-------------|
| `doc` | Root node |
| `paragraph` | Text block |
| `blockquote` | Quoted text |
| `codeBlock` | Code block |
| `bulletList` | Unordered list (contains `listItem` nodes) |
| `orderedList` | Ordered list (contains `listItem` nodes) |
| `listItem` | List item (contains paragraphs or other blocks) |
| `table` | Data table (contains `tableRow` nodes) |
| `tableRow` | Table row (contains `tableCell` or `tableHeader` nodes) |
| `tableCell` | Table cell |
| `tableHeader` | Table header cell |

**Block nodes (with attrs):**

| Node Type | Description | Required Attributes |
|-----------|-------------|---------------------|
| `heading` | Heading block | `level` (integer 1–6) |
| `image` | Image embed | `src` (string). Optional: `alt`, `title` |
| `cardEmbed` | Embedded card/query | `id` (card reference path, see below). Optional: `name` |
| `smartLink` | Reference to another entity | `entityId` (entity reference path), `model` (string) |

**Inline nodes:**

| Node Type | Required Fields | Description |
|-----------|-----------------|-------------|
| `text` | `text` (string) | Inline text content. May have `marks` for formatting. |
| `hardBreak` | — | Line break within a paragraph |

#### Card Embed Reference Format

The `id` attribute of a `cardEmbed` node is a **serdes path** — an array with exactly one entry containing `model: Card` and the card's entity_id:

```yaml
- type: cardEmbed
  attrs:
    id:
    - model: Card
      id: h5F2EjHsRd73Dqqh8sAtd
    name: My Card
```

The `smartLink` node uses the same path format for `entityId`, but the `model` can be any entity type (card, dashboard, collection, table, etc.).

### Example

```yaml
name: Product Analysis Report
entity_id: dOc1PrOdAnAlYsIsRpTx2
creator_id: internal@metabase.com
document:
  type: doc
  content:
  - type: heading
    attrs:
      level: 1
    content:
    - type: text
      text: Product Analysis Report
  - type: paragraph
    content:
    - type: text
      text: "Overview of product performance metrics."
  - type: cardEmbed
    attrs:
      id:
      - model: Card
        id: h5F2EjHsRd73Dqqh8sAtd
      name: Basic Aggregations
  - type: bulletList
    content:
    - type: listItem
      content:
      - type: paragraph
        content:
        - type: text
          text: Revenue increased 15% quarter over quarter
    - type: listItem
      content:
      - type: paragraph
        content:
        - type: text
          text: Widget category remains the top performer
content_type: "application/json+vnd.prose-mirror"
collection_id: null
serdes/meta:
- id: dOc1PrOdAnAlYsIsRpTx2
  label: product_analysis_report
  model: Document
```

---

## Segment

A segment is a saved filter definition. Segments allow reusable filters that can be applied across multiple questions and dashboards.

Each segment holds a `definition` that specifies the source table and filter criteria. See [MBQL Query](#mbql-query) for filter syntax.

Segments are stored under their table's directory: `databases/{db_slug}/schemas/{schema_slug}/tables/{table_slug}/segments/`.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Segment name |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `definition` | object | Yes | Filter definition with `"lib/type": mbql/query`, `database`, and `stages` containing `source-table` and `filters` |
| `serdes/meta` | array | Yes | Identity path with `model: Segment` |
| `table_id` | array | No | Table FK `[database, schema, table]`. Only included when not derivable from `definition` (e.g., empty or broken definition); re-derived from the definition on import when present. |
| `description` | string | No | Description |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `created_at` | string | No | ISO 8601 timestamp |

### Example

```yaml
name: Widget products
entity_id: aB3kLmN9pQrStUvWxYz1a
creator_id: internal@metabase.com
definition:
  "lib/type": mbql/query
  database: Sample Database
  stages:
  - "lib/type": mbql.stage/mbql
    source-table:
    - Sample Database
    - PUBLIC
    - PRODUCTS
    filters:
    - - =
      - {}
      - - field
        - {}
        - - Sample Database
          - PUBLIC
          - PRODUCTS
          - CATEGORY
      - Widget
serdes/meta:
- id: aB3kLmN9pQrStUvWxYz1a
  label: widget_products
  model: Segment
```

---

## Measure

A measure is a saved aggregation definition. Measures allow reusable aggregations that can be applied across multiple questions and dashboards.

Each measure holds a `definition` that specifies the database and aggregation clause. See [MBQL Query](#mbql-query) for aggregation syntax.

Measures are stored under their table's directory: `databases/{db_slug}/schemas/{schema_slug}/tables/{table_slug}/measures/`.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Measure name |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `definition` | object | Yes | Aggregation definition with `"lib/type": mbql/query`, `database`, and `stages` containing `source-table` and exactly one `aggregation`. Measures cannot use `filters`. |
| `serdes/meta` | array | Yes | Identity path with `model: Measure` |
| `table_id` | array | No | Table FK `[database, schema, table]`. Only included when not derivable from `definition` (e.g., empty or broken definition); re-derived from the definition on import when present. |
| `description` | string | No | Description |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `created_at` | string | No | ISO 8601 timestamp |

### Example

```yaml
name: Total revenue
entity_id: xK7mPqR2sT4uVwXyZ9a1b
creator_id: internal@metabase.com
definition:
  "lib/type": mbql/query
  database: Sample Database
  stages:
  - "lib/type": mbql.stage/mbql
    source-table:
    - Sample Database
    - PUBLIC
    - ORDERS
    aggregation:
    - - sum
      - {}
      - - field
        - base-type: type/Float
        - - Sample Database
          - PUBLIC
          - ORDERS
          - TOTAL
serdes/meta:
- id: xK7mPqR2sT4uVwXyZ9a1b
  label: total_revenue
  model: Measure
```

---

## Snippet

A snippet is a reusable SQL fragment that can be referenced in native queries using `{{snippet: Snippet Name}}`. Snippets are stored under `collections/snippets/`, organized by snippet collection hierarchy.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Snippet name (used in `{{snippet: Name}}` references) |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `content` | string | Yes | SQL content of the snippet |
| `serdes/meta` | array | Yes | Identity path with `model: NativeQuerySnippet` |
| `description` | string | No | Description |
| `archived` | boolean | No | Whether archived (default: `false`) |
| `collection_id` | string | No | Collection FK (entity_id). **Set this to place the snippet in a snippet collection**; `null`/omitted = root snippet collection |
| `template_tags` | map | No | Template tag definitions (usually empty `{}`) |
| `created_at` | string | No | ISO 8601 timestamp |

### Example

```yaml
name: Active Order Filter
entity_id: xK7mPqR2sT4uVwXyZ9a1b
creator_id: internal@metabase.com
content: "STATUS = 'active' AND TOTAL > 0"
description: Filter for active orders with positive totals
archived: false
collection_id: Y6d4QwJgGKw-X1tRh3ir2
template_tags: {}
serdes/meta:
- id: xK7mPqR2sT4uVwXyZ9a1b
  label: active_order_filter
  model: NativeQuerySnippet
```

---

## Transform

A transform generates a table in the database by running a query or Python script. Transforms allow materializing results as persistent database tables. Transform entities are stored under `collections/transforms/`. Transform jobs and tags are stored separately under the top-level `transforms/` directory.

The `source` defines how data is produced — either an MBQL/native query (`type: query`) or a Python script (`type: python`). The `target` specifies where the resulting table is written.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Transform name |
| `entity_id` | string | Yes | NanoID identifier |
| `creator_id` | string | Yes | User FK (email) |
| `source_database_id` | string | Yes | Database FK (database name) |
| `source` | object | Yes | Source definition — query or Python (see below) |
| `target` | object | Yes | Target table: `database` (Database FK), `type` (`"table"`), `schema`, `name` |
| `serdes/meta` | array | Yes | Identity path with `model: Transform` |
| `description` | string | No | Description |
| `collection_id` | string | No | Collection FK (entity_id). **Set this to place the transform in a collection**; `null`/omitted = root collection |
| `tags` | array | No | Transform tags (see below) |
| `created_at` | string | No | ISO 8601 timestamp |

### Query Source

When `source.type` is `query`, the source wraps an MBQL or native query. See [MBQL Query](#mbql-query) for query syntax.

```yaml
source:
  type: query
  query:
    "lib/type": mbql/query
    database: Sample Database
    stages:
    - "lib/type": mbql.stage/mbql
      source-table:
      - Sample Database
      - PUBLIC
      - PRODUCTS
```

### Python Source

When `source.type` is `python`, the source contains a Python script that receives source tables as pandas DataFrames and must return a DataFrame as the result.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `"python"` |
| `body` | string | Yes | Python source code |
| `source-tables` | array | Yes | Source tables available to the script |
| `source-database` | string | No | Database FK (database name) |
| `source-incremental-strategy` | object | No | Incremental execution strategy |

Each entry in `source-tables`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alias` | string | Yes | Variable name for the table in Python |
| `database_id` | string | Yes | Database FK (database name) |
| `schema` | string | No | Schema name |
| `table` | string | No | Table name |
| `table_id` | integer | No | Metabase table ID |

```yaml
source:
  type: python
  body: |-
    import pandas as pd
    def transform(products):
        return products.groupby('CATEGORY').agg(
            count=('ID', 'count'),
            avg_price=('PRICE', 'mean')
        ).reset_index()
  source-tables:
  - alias: products
    database_id: Sample Database
    schema: PUBLIC
    table: PRODUCTS
  source-database: Sample Database
```

Python libraries (see [PythonLibrary](#pythonlibrary)) are available as imports within the script.

### Transform Tags

Tags categorize transforms for scheduling and organization. Each tag association on a transform references a TransformTag by its entity_id:

```yaml
tags:
- entity_id: TUtH6I5SqautNtUZoZ6Ti
  position: 0
  tag_id: hourlyhourlyhourlyxxx        # entity_id of the TransformTag
  serdes/meta:
  - id: TUtH6I5SqautNtUZoZ6Ti
    model: TransformTransformTag
```

### TransformTag

A transform tag is a label for categorizing transforms. Tags can be built-in (`hourly`, `daily`, `weekly`, `monthly`) or custom. Stored in `transforms/transform_tags/`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID identifier |
| `name` | string | Yes | Tag name (e.g., `"hourly"`, `"custom-etl"`) |
| `serdes/meta` | array | Yes | Identity path with `model: TransformTag` |
| `built_in_type` | string | No | Built-in category: `"hourly"`, `"daily"`, `"weekly"`, `"monthly"`, or `null` for custom |
| `created_at` | string | No | ISO 8601 timestamp |

### TransformJob

A transform job is a scheduled task that executes transforms matching specific tags. Stored in `transforms/transform_jobs/`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID identifier |
| `name` | string | Yes | Job name (e.g., `"Hourly job"`) |
| `schedule` | string | Yes | Cron expression (e.g., `"0 0 * * * ? *"`) |
| `serdes/meta` | array | Yes | Identity path with `model: TransformJob` |
| `description` | string | No | Human-readable description |
| `built_in_type` | string | No | Built-in category: `"hourly"`, `"daily"`, `"weekly"`, `"monthly"`, or `null` for custom |
| `ui_display_type` | string | No | `"cron/builder"` or `null` |
| `job_tags` | array | No | Tag associations (see below) |
| `created_at` | string | No | ISO 8601 timestamp |

Each entry in `job_tags` connects the job to a TransformTag:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID of this job-tag association |
| `tag_id` | string | Yes | TransformTag entity_id |
| `position` | integer | Yes | Ordering position |
| `serdes/meta` | array | Yes | Identity path with `model: TransformJobTransformTag` |

```yaml
job_tags:
- entity_id: BPhRX8sTqcG5tZrXKeQuP
  position: 0
  tag_id: mXacguzCHQ5bBhqQPt3kd        # entity_id of the "daily" tag
  serdes/meta:
  - id: BPhRX8sTqcG5tZrXKeQuP
    model: TransformJobTransformTag
```

A job can reference multiple tags. Transforms tagged with any of the job's tags will be executed when the job runs.

### PythonLibrary

A shared Python source file available to transforms. Stored in `python_libraries/`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | NanoID identifier |
| `path` | string | Yes | Python file path (e.g., `"common.py"`) |
| `source` | string | Yes | Python source code |
| `serdes/meta` | array | Yes | Identity path with `model: PythonLibrary` |
| `created_at` | string | No | ISO 8601 timestamp |

### Example

```yaml
name: Product summary
entity_id: rT5vWxYz1aBcDeFgHiJkL
creator_id: internal@metabase.com
source_database_id: Sample Database
source:
  type: query
  query:
    "lib/type": mbql/query
    database: Sample Database
    stages:
    - "lib/type": mbql.stage/mbql
      source-table:
      - Sample Database
      - PUBLIC
      - PRODUCTS
target:
  database: Sample Database
  type: table
  schema: PUBLIC
  name: product_summary
collection_id: M-Q4pcV0qkiyJ0kiSWECl
serdes/meta:
- id: rT5vWxYz1aBcDeFgHiJkL
  label: product_summary
  model: Transform
```

---

## Version History

- **1.0.0**: Initial release
  - Entity key system (NanoID and foreign key references)
  - Folder structure specification with namespace-based collection layout
  - Collection, Card, Dashboard, Document, Segment, Measure, Snippet, Transform, TransformJob, TransformTag, PythonLibrary

---

## License

See LICENSE file for details.
