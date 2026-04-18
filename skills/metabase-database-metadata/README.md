# metabase-database-metadata (skill)

This skill ships a local snapshot of the Metabase Database Metadata specification as `spec.md`, sitting next to `SKILL.md`. The SKILL references that bundled file directly, so an agent loading this skill never has to fetch the spec on its own.

## Refreshing the bundled spec

When the upstream format changes, refresh the bundled copy by running this from inside the skill folder:

```sh
npx @metabase/database-metadata extract-spec --file ./spec.md
```

Commit the regenerated `spec.md` alongside `SKILL.md`.

## Files

- `SKILL.md` — the skill itself. Read by the agent.
- `spec.md` — the v1 specification of the Metabase Database Metadata Format. Agent reads this on demand when it needs details beyond what `SKILL.md` summarizes (full type hierarchy, coercion strategies, exact folder-path rules, etc.).
