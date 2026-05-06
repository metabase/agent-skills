# metabase-cli (skill)

Drives a Metabase instance from the terminal via the official `metabase` CLI: auth/profiles, list/get/create/update/run on every resource, content search, remote-sync, Enterprise workspaces, API keys, entity-id translation.

## Files

- `SKILL.md` — always loaded. Covers auth (the human logs in, the agent uses the profile), the four flag conventions, output flags, body-input precedence, a per-group "Resources at a glance" reference, and a pointer at `metabase __manifest` (the hidden machine-readable inventory of every command).
- `references/workspace.md` — full workspace lifecycle (Enterprise): create, provision, start/stop/restart/remove, child credentials → child profile, diagnose tree. Read when the user touches `metabase workspace …`.
- `references/transform.md` — transform create-and-run flow with a working native-SQL JSON body template, run-with-wait pattern, inspection verbs. Read when authoring or running a transform.
- `references/sync.md` — remote-sync workflow (import/export/branches/stash/dirty checks), with safety rules around the lossy `--force` flags. Read when the user is moving content between Metabase and a git repo.

The reference files are loaded on demand by the agent — `SKILL.md` tells it when. The split exists so a one-shot CLI task ("list cards in prod") doesn't pay the token cost for workspace or transform or sync detail it'll never use.

## How the agent should think about this

1. Default first move: `metabase auth status --json`. If no profile, ask the human to log in — never run `auth login` for them.
2. Default reference for "how does this command work?": `metabase __manifest | jq '.commands[] | select(.command == "<name>")'`. Faster and more complete than scraping `--help`.
3. When the task touches workspaces / transforms / sync, load the matching reference file before constructing commands. The references go beyond the at-a-glance examples.
