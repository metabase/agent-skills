# Metabase Database Metadata Format

**Version:** 1.0.0

## Overview

Metabase database metadata is a read-only snapshot of databases, tables, and fields that have been synced from a connected data source. This specification describes the **default** format for exporting that metadata to disk: one YAML file per database, and one YAML file per table with its fields nested inside.

The format is designed to be **portable** and **reviewable**: numeric IDs are omitted or replaced with human-readable natural keys (database name, `[database, schema, table]` tuples, etc.). Files can be diffed, grepped, and edited by hand.

The raw `metadata.json` is a single flat JSON document with `databases`, `tables`, and `fields` arrays, optimized for transport rather than reading. It can be arbitrarily large — tens or hundreds of megabytes on warehouses with many tables — and is not intended for direct consumption. Tools and humans should read the extracted YAML tree under `databases/` instead, where each entity lives in its own small file.

## Table of Contents

1. [Entity Keys](#entity-keys)
2. [Field Types](#field-types)
3. [Folder Structure](#folder-structure)
4. [Database](#database)
5. [Table](#table)
6. [Field](#field)

---

## Entity Keys

Database objects are referenced using natural keys instead of numeric IDs.

| Reference | Format | Example |
|-----------|--------|---------|
| Database FK | database name | `"Sample Database"` |
| Table FK | `[database, schema, table]` | `["Sample Database", "PUBLIC", "ORDERS"]` |
| Field FK | `[database, schema, table, field, ...]` | `["Sample Database", "PUBLIC", "ORDERS", "TOTAL"]` |

For schemaless databases, the schema component is `null` (e.g., `["My Database", null, "my_table"]`).

For JSON-unfolded fields, the Field FK extends beyond 4 elements with the nested path: `["Sample Database", "PUBLIC", "EVENTS", "DATA", "user", "name"]` represents the JSON path `DATA.user.name`.

Numeric primary keys (`id`) are not emitted. Each entity is identified by its position in the folder tree and by the natural-key foreign keys on child entities.

---

## Field Types

Each field has four type attributes that describe the column at different layers: `database_type` (the native SQL type), `base_type` (the matching Metabase type), `effective_type` (the type after any coercion), and `semantic_type` (the business-domain role). An optional `coercion_strategy` defines the rule that produces `effective_type` from `base_type`.

### `database_type`

The native SQL type reported by the database driver, verbatim (e.g., `BIGINT`, `VARCHAR`, `DOUBLE PRECISION`, `TIMESTAMP WITH TIME ZONE`, `JSONB`). This value is **database-specific**: the same logical type can appear with different spellings across engines (`INT4` vs `INTEGER`, `CHARACTER VARYING` vs `VARCHAR`, `DOUBLE` vs `DOUBLE PRECISION`). Metabase uses `database_type` for informational purposes and when generating native SQL; it is not portable across engines.

`database_type` always maps deterministically to a `base_type` for a given driver — see the table below for typical pairings.

### `base_type`

The raw Metabase type that matches the column's native database type. This is what the driver reports the column as (e.g., a Postgres `BIGINT` → `type/BigInteger`, `VARCHAR` → `type/Text`, `DOUBLE PRECISION` → `type/Float`).

`base_type` is always one of the types below and never a semantic type like `type/PK`.

Common base types (selected from the type hierarchy):

| Base type | Meaning | Typical native types |
|-----------|---------|----------------------|
| `type/Boolean` | Boolean | `BOOLEAN`, `BIT` |
| `type/Integer` | Signed integer | `INTEGER`, `INT`, `SMALLINT` |
| `type/BigInteger` | Wide integer | `BIGINT` |
| `type/Float` | Binary floating-point | `DOUBLE`, `REAL`, `FLOAT` |
| `type/Decimal` | Fixed-precision decimal | `DECIMAL`, `NUMERIC` |
| `type/Text` | Variable-length text | `VARCHAR`, `TEXT`, `CHARACTER` |
| `type/UUID` | UUID (a `type/Text` subtype) | `UUID` |
| `type/Date` | Date without time | `DATE` |
| `type/Time` | Time of day | `TIME` |
| `type/TimeWithLocalTZ` | Time stored at UTC | `TIME WITH TIME ZONE` |
| `type/DateTime` | Local date-time (no offset) | `TIMESTAMP`, `DATETIME` |
| `type/DateTimeWithLocalTZ` | Date-time stored at UTC | `TIMESTAMP WITH TIME ZONE` |
| `type/Instant` | Absolute point in time | (see coercion strategies) |
| `type/Structured` | JSON/structured payload | `JSON`, `JSONB` |
| `type/*` | Unknown / fallback | — |

### `effective_type`

The type Metabase actually treats the column as when running queries. If no coercion is applied, `effective_type` equals `base_type` and is omitted from the YAML. It is emitted only when coercion changes the type.

For example: a `VARCHAR` column whose `base_type` is `type/Text` but that stores ISO-8601 timestamps would have `effective_type: type/DateTime` and `coercion_strategy: Coercion/ISO8601->DateTime`.

### `coercion_strategy`

An optional rule that tells Metabase how to convert `base_type` → `effective_type` at query time. Absent unless coercion is configured.

Built-in coercion strategies:

| Strategy | `base_type` | `effective_type` |
|----------|-------------|------------------|
| `Coercion/UNIXSeconds->DateTime` | `type/Integer`, `type/Decimal` | `type/Instant` |
| `Coercion/UNIXMilliSeconds->DateTime` | `type/Integer`, `type/Decimal` | `type/Instant` |
| `Coercion/UNIXMicroSeconds->DateTime` | `type/Integer`, `type/Decimal` | `type/Instant` |
| `Coercion/UNIXNanoSeconds->DateTime` | `type/Integer`, `type/Decimal` | `type/Instant` |
| `Coercion/ISO8601->Date` | `type/Text` | `type/Date` |
| `Coercion/ISO8601->Time` | `type/Text` | `type/Time` |
| `Coercion/ISO8601->DateTime` | `type/Text` | `type/DateTime` |
| `Coercion/YYYYMMDDHHMMSSString->Temporal` | `type/Text` | `type/DateTime` |
| `Coercion/DateTime->Date` | `type/DateTime` | `type/Date` |

### `semantic_type`

An optional label describing how the column is used in the business domain. Semantic types sit in a separate hierarchy (rooted at `Semantic/*` or `Relation/*`) and don't affect how values are read or converted — they drive UI choices (icons, default visualizations, filter widgets) and some analytical behavior (e.g., auto-binning for `type/Category`).

Common semantic types, grouped by purpose:

| Group | Semantic types |
|-------|----------------|
| Relations | `type/PK`, `type/FK` |
| Identity / labels | `type/Name`, `type/Title`, `type/Description`, `type/Comment` |
| Categorization | `type/Category`, `type/Enum`, `type/Source`, `type/Product`, `type/Company`, `type/Subscription` |
| Geography | `type/City`, `type/State`, `type/Country`, `type/ZipCode`, `type/Latitude`, `type/Longitude`, `type/IPAddress` |
| Contact | `type/Email`, `type/URL`, `type/ImageURL`, `type/AvatarURL` |
| Money / numeric | `type/Currency`, `type/Price`, `type/Cost`, `type/Income`, `type/Discount`, `type/GrossMargin`, `type/Percentage`, `type/Share`, `type/Score`, `type/Quantity`, `type/Duration` |
| Temporal roles | `type/CreationTimestamp`, `type/CreationDate`, `type/JoinTimestamp`, `type/CancelationTimestamp`, `type/DeletionTimestamp`, `type/UpdatedTimestamp`, `type/Birthdate` |
| Other | `type/User`, `type/Structured` |

`semantic_type` is always compatible with `effective_type` (or `base_type` when no coercion is in play) — e.g., `type/Latitude` only makes sense on `type/Float`, `type/Email` only on `type/Text`.

---

## Folder Structure

By convention, metadata is extracted under a `.metadata/databases/` directory, with each database occupying its own folder. The exporter itself doesn't enforce this location; it writes the tree below into whatever folder the caller passes.

```
.metadata/
└── databases/
    └── {database}/
        ├── {database}.yaml
        ├── schemas/
        │   └── {schema}/
        │       └── tables/
        │           └── {table}.yaml
        └── tables/                         # Schemaless databases
            └── {table}.yaml
```

### Path Construction Rules

- Database, schema, and table names are used verbatim as folder and file names. Case and spaces are preserved (e.g. `Sample Database/`, `PUBLIC/`, `ORDERS.yaml`).
- Only characters that are invalid in paths are escaped: `/` becomes `__SLASH__`, `\` becomes `__BACKSLASH__`.
- A database's YAML file (`{name}.yaml`) lives at the root of its folder.
- Tables are nested under `schemas/{schema}/tables/{table}.yaml` when the database has schemas, or directly under `tables/{table}.yaml` for schemaless databases.
- A table's YAML file embeds all of its fields inline — there is no separate file per field.

---

## Database

A `Database` entry describes a connected data source (e.g., a Postgres or MySQL instance). Only identifying information is included; connection details are not part of this format.

The database YAML file lives at `databases/{slug}/{slug}.yaml`.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Database name (unique, used as the Database FK) |
| `engine` | string | Yes | Database engine (e.g., `postgres`, `mysql`, `h2`, `bigquery-cloud-sdk`) |

### Example

```yaml
name: Sample Database
engine: postgres
```

---

## Table

A `Table` entry describes a single physical table (or view) within a database. Its fields are nested directly in the same YAML file.

The table YAML file lives at `databases/{db_slug}/schemas/{schema_slug}/tables/{table_slug}.yaml` (or `databases/{db_slug}/tables/{table_slug}.yaml` for schemaless databases).

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Table name in the database |
| `db_id` | string | Yes | Database FK (database name) |
| `fields` | array | Yes | Array of [Field](#field) entries belonging to this table |
| `schema` | string | No | Schema name; omitted for schemaless databases |
| `description` | string | No | Human-readable description |

### Example

```yaml
name: ORDERS
db_id: Sample Database
schema: PUBLIC
description: Confirmed Sample Company orders for a product, from a user.
fields:
  - name: ID
    base_type: type/BigInteger
    database_type: BIGINT
    semantic_type: type/PK
  - name: TOTAL
    description: The total billed amount.
    base_type: type/Float
    database_type: DOUBLE PRECISION
```

---

## Field

A `Field` entry describes a single column. Fields are nested inline inside their [Table](#table); there is no separate field file.

A field's table is implied by its position in the enclosing table's `fields` array, so `table_id` is not emitted on nested fields. Only `parent_id` appears when the field is a child of another field (e.g., JSON-unfolded nested columns).

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Column name in the database |
| `database_type` | string | Yes | Native database type (e.g., `INTEGER`, `VARCHAR`) |
| `base_type` | string | Yes | Metabase type matching the native type. See [Field Types](#field-types) |
| `description` | string | No | Human-readable description |
| `effective_type` | string | No | Type after coercion; omitted when equal to `base_type`. See [Field Types](#field-types) |
| `coercion_strategy` | string | No | Coercion rule applied at query time. See [Field Types](#field-types) |
| `semantic_type` | string | No | Business-domain label (e.g., `type/PK`, `type/Email`). See [Field Types](#field-types) |
| `parent_id` | array | No | Field FK of the parent field, for nested/JSON-unfolded columns |
| `fk_target_field_id` | array | No | Field FK of the referenced primary-key column, for fields with `semantic_type: type/FK` |

### Example

```yaml
name: CREATED_AT
description: The order creation timestamp.
base_type: type/Text
database_type: TEXT
effective_type: type/DateTime
semantic_type: type/CreationTimestamp
coercion_strategy: Coercion/ISO8601->DateTime
```

### Nested Fields

JSON-unfolded columns use `parent_id` to reference the enclosing field:

```yaml
name: name
base_type: type/Text
database_type: TEXT
parent_id:
  - Sample Database
  - PUBLIC
  - EVENTS
  - DATA
  - user
```

