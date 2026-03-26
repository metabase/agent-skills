# Folder Structure

Metabase serialization exports instance configuration as a tree of YAML files under an export root directory.

## Folder Structure

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

## Path construction rules

- **Collection hierarchy is reflected in directory nesting.** A child collection folder lives inside its parent collection folder.
- **Entity files are named `{entity_id}_{label}.yaml`** where label is the slugified name.
- **Entity type subdirectories use lowercase plural model names**: `cards/`, `dashboards/`, `timelines/`, `transforms/`, `metabots/`, `documents/`, `channels/`.
- **Database/table/field paths use actual names** (not entity_ids), since these entities are identified by name.
- **FieldValues and FieldUserSettings** are stored alongside the field file with `___fieldvalues` and `___fieldusersettings` suffixes.
- **Slashes in names** are escaped as `__SLASH__` and backslashes as `__BACKSLASH__`.
