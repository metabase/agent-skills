# metabase-cli (skill)

Discovery stub for the [`@metabase/cli`](https://www.npmjs.com/package/@metabase/cli) skill bundle. The agent loads workflow content at runtime via `mb skills get`, so instructions always match the installed CLI version.

## Install

```bash
npm i -g @metabase/cli                                                # CLI itself
npx skills add metabase/agent-skills --skill metabase-cli             # this stub
```

Or, in Claude Code, install both the stub and the marketplace entry directly from the CLI repo:

```
/plugin marketplace add metabase/mb-cli
/plugin install metabase-cli@metabase
```

One install path is enough — both resolve to the same `mb skills get` runtime fetch.

## Files

- `SKILL.md` — frontmatter (trigger phrases) + a redirect at `mb skills get core`.
