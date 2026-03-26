---
name: metabase-serialization-format
description: Generate and understand Metabase serialized YAML data for export/import across instances
allowed-tools: Read, Write, Edit, Grep, Glob
---

## Overview

Metabase serialization (SerDes) exports instance configuration as a tree of YAML files. Each file represents one entity (a collection, card, dashboard, database definition, etc.). The format is designed to be **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

## Entity identifiers

Metabase uses 2 ways of identifying entities: by `entity_id` (nanoid) and natural entity keys.

### Entity IDs

`entity_id` is saved with each entity and should not change after it was created. The entity can be renamed, moved to a different collection, but as long as its `entity_id` remains the same, Metabase will understand that it's the same entity. 

`entity_id` is a 21-character [NanoID](https://github.com/ai/nanoid) string like `NDzkGoTCdRcaRyt7GOepg`. This is the primary portable identifier used in cross-references.

Generate a NanoID in Python:
```python
from nanoid import generate
generate()  # => 'NDzkGoTCdRcaRyt7GOepg'
```

NanoID alphabet: `A-Za-z0-9_-` (64 chars, 21 chars long).

### Natural entity keys

Some entities use natural keys instead of NanoIDs:
- **Database**: identified by `name` (e.g., `"Sample Database"`)
- **Schema**: identified by name within a database
- **Table**: identified by `[database_name, schema, table_name]` (e.g., `["Sample Database", "PUBLIC", "ORDERS"]`)
- **Field**: identified by `[database_name, schema, table_name, field_name]`
- **Setting**: identified by setting key
- **Glossary**: identified by `term`

## Entities

- Card [card.md](./entities/card.md).
