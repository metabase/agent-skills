# metabase-representation-format

Skill for working with the Metabase Representation Format — a YAML-based serialization format for Metabase content.

## Setup

This skill requires the specification and schema files from the [`@metabase/representations`](https://github.com/metabase/representations) package. Copy them into this skill folder:

```sh
# From the representations repo (or a local clone at ~/Work/representations)
cp ~/Work/representations/core-spec/v1/spec.md skills/metabase-representation-format/spec.md
cp -r ~/Work/representations/core-spec/v1/schemas skills/metabase-representation-format/schemas
```

After copying, the skill folder should look like:

```
skills/metabase-representation-format/
├── SKILL.md          # Skill definition (already present)
├── README.md         # This file
├── spec.md           # Full specification (copy from representations repo)
└── schemas/          # JSON Schema definitions (copy from representations repo)
    ├── card.yaml
    ├── collection.yaml
    ├── dashboard.yaml
    ├── document.yaml
    ├── measure.yaml
    ├── python_library.yaml
    ├── segment.yaml
    ├── snippet.yaml
    ├── transform.yaml
    ├── transform_job.yaml
    ├── transform_tag.yaml
    └── common/
        ├── id.yaml
        ├── parameter.yaml
        ├── query.yaml
        ├── ref.yaml
        └── temporal_bucketing.yaml
```
