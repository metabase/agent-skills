# metabase-representation-format (skill)

This skill ships a local snapshot of the Metabase Representation Format specification as `spec.md`, next to `SKILL.md`. The SKILL references it directly so an agent loading this skill never has to fetch the spec on its own.

## Refreshing the bundled spec

When the upstream format changes, refresh the bundled copy by running this from inside the skill folder:

```sh
npx @metabase/representations extract-spec --file ./spec.md
```

Commit the regenerated file alongside `SKILL.md`.

## Files

- `SKILL.md` — the skill itself. Read by the agent.
- `spec.md` — specification (entity shapes, MBQL/native query form, folder structure, etc.). Agent reads this on demand when it needs detail beyond what `SKILL.md` summarizes.
