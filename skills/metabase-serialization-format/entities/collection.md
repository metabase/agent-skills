# Collection

A collection is a folder-like container for organizing cards, dashboards, and other entities in Metabase. Collection hierarchy is reflected in the directory structure of the export.

## Minimal required properties

```yaml
name: Marketing Analytics                  # string
entity_id: M-Q4pcV0qkiyJ0kiSWECl           # nanoid
serdes/meta:
- id: M-Q4pcV0qkiyJ0kiSWECl                # nanoid, matches entity_id
  label: marketing_analytics               # lowercased name, spaces converted to underscores
  model: Collection
```

## Optional properties

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
