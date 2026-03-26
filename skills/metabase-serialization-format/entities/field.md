# Field

A field represents a column in a database table. Field entities are synced from the connected database and should not be edited by hand.

Fields use `[database, schema, table, field_name]` as identifier.

## Minimal required properties

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

## Optional properties

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

## FieldValues

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

## FieldUserSettings

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
