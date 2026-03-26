---
name: metabase-serialization-format
description: Generate and understand Metabase serialized YAML data for export/import across instances
allowed-tools: Read, Write, Edit, Grep, Glob
---

## Overview

Metabase serialization (SerDes) exports instance configuration as a tree of YAML files. Each file represents one entity (a collection, card, dashboard, database definition, etc.). The format is designed to be **portable** across Metabase instances: numeric database IDs are replaced with human-readable names and entity IDs.

## Folder structure

See [folder_structure.md](./common/folder_structure.md) for the export directory layout and path construction rules.

## Entity identifiers

Metabase uses 2 ways of identifying entities: by `entity_id` (nanoid) and natural entity keys. See [id.md](./common//id.md) for the format specification.

## Entities

- Card [card.md](./entities/card.md).
- Segment [segment.md](./entities/segment.md).
- Measure [measure.md](./entities/measure.md).
