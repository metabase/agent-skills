# metabase-representation-format (skill)

This skill ships a local snapshot of the Metabase Representation Format specification and its JSON Schemas:

- `spec.md` — the v1 specification.
- `schemas/` — YAML JSON Schemas, one per entity.

Both live next to `SKILL.md`, and the SKILL references them directly so an agent loading this skill never has to fetch the spec or the schemas on its own.

## Refreshing the bundled spec and schemas

When the upstream format changes, refresh the bundled copies by running these from inside the skill folder:

```sh
npx @metabase/representations extract-spec --file ./spec.md
npx @metabase/representations extract-schema --folder ./schemas
```

Commit the regenerated files alongside `SKILL.md`.

## Files

- `SKILL.md` — the skill itself. Read by the agent.
- `spec.md` — specification (entity shapes, MBQL/native query form, folder structure, etc.). Agent reads this on demand when it needs detail beyond what `SKILL.md` summarizes.
- `schemas/` — per-entity JSON Schemas used by `validate-schema` and as structural references for agent edits.
