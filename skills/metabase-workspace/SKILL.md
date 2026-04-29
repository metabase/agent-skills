---
name: metabase-workspace
description: Help the user run a local "developer instance" of Metabase backed by a Workspace exported from a production Metabase instance. Workspaces give hard isolation — queries and edits never touch the real data warehouse, which is ideal for safe iteration and agent-driven coding. Use when the user asks to "set up a workspace", "configure a workspace", "start/stop the dev instance", "spin up Metabase locally", or after they download a fresh `config.yml` and want to recreate the local container.
model: opus
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

## What this skill does

A **Workspace** is a managed sandbox attached to a production Metabase instance. It carves out an isolated schema (and a database user scoped to it) so that queries written against the workspace can be saved, edited, and re-run without ever modifying the real warehouse. The user's main Metabase instance hosts the workspace; a separate **developer instance** — a local Docker container — connects to that same isolated schema and serves as the safe place to iterate.

This skill manages that local developer instance: it makes sure the credentials and config file are in place, the right things are gitignored, and the container is started/stopped/recreated correctly. It does **not** create the workspace itself — that happens in the production instance UI.

## Setup is split between the production instance and this repo

Before this skill can do anything useful, the user must have done the production-side setup. Confirm they have:

1. **Created a Workspace** in the production instance: `Data Studio → Workspaces → New workspace`, added the databases the workspace should expose, and **downloaded the `config.yml`** for that workspace.
2. **Configured git-sync** on the production instance so that this repo is the workspace's synced target.

If either is missing, stop and ask the user to complete it first — the skill cannot generate `config.yml` itself.

## Variables the local container needs

The container reads two things from the host:

- **`MB_PREMIUM_EMBEDDING_TOKEN`** — the EE license token. Sensitive.
- **`MB_CONFIG_FILE_PATH`** — the **host** path to `config.yml` (the file the user downloaded). Defaults to `./config.yml` at the repo root if the user hasn't placed it elsewhere.

Both values live in `.env` at the repo root. Both `.env` and the `config.yml` it points to **must be gitignored** — they contain the EE token and the bundled database credentials, neither of which can be safely committed.

> Never `Read` or `cat` the `.env` file. Never echo or print its contents. Always source it inside a single `bash` command and reference the variables from there. The skill checks for the presence of keys with `grep -q`, never by reading values.

## When the user asks to set up / configure / start

Run the steps below in order. Stop and ask the user to fix any check that fails before continuing.

### Step 1 — Confirm `config.yml` is present

Check that the configured config file exists. If `.env` already defines `MB_CONFIG_FILE_PATH`, source it and check that path; otherwise default to `./config.yml`.

```bash
( set -a; [ -f .env ] && source .env; set +a;
  path="${MB_CONFIG_FILE_PATH:-./config.yml}";
  test -f "$path" && echo "OK: $path" || echo "MISSING: $path" )
```

If missing, ask the user:

> I don't see the workspace `config.yml`. Go to the production Metabase instance → `Data Studio → Workspaces → <your workspace>`, click **Download config file**, and save it to `<repo-root>/config.yml` (or another location and tell me the path). Let me know when it's in place.

### Step 2 — Ensure `.env` exists with the required keys

Check that `.env` exists and has both `MB_PREMIUM_EMBEDDING_TOKEN` and `MB_CONFIG_FILE_PATH`. Use grep — do not read values.

```bash
[ -f .env ] && echo "env-present" || echo "env-missing"
grep -q '^MB_PREMIUM_EMBEDDING_TOKEN=' .env 2>/dev/null && echo "has-token" || echo "no-token"
grep -q '^MB_CONFIG_FILE_PATH='        .env 2>/dev/null && echo "has-path"  || echo "no-path"
```

- If `.env` is missing: create `.env.template` with placeholders (do **not** write the real `.env` for them — they need to fill in the EE token themselves), and ask the user to copy it:
  ```env
  MB_PREMIUM_EMBEDDING_TOKEN=
  MB_CONFIG_FILE_PATH=./config.yml
  ```
  Tell them: *"I created `.env.template`. Copy it to `.env` and fill in `MB_PREMIUM_EMBEDDING_TOKEN` from your Metabase license. Adjust `MB_CONFIG_FILE_PATH` if `config.yml` lives elsewhere. Let me know when done."*
- If `.env` exists but a key is missing, ask the user to add it (don't insert it for them — you don't know the token value).
- If both keys are present, continue.

### Step 3 — Ensure both files are gitignored

Read the repo's `.gitignore` (creating it empty if missing) and confirm both `.env` and the configured `config.yml` path (or default `./config.yml`) are ignored.

If either is not ignored, **ask before modifying** `.gitignore`:

> `.env` and/or `config.yml` aren't in `.gitignore`. They contain your EE token and database credentials — committing them would leak both. Shall I add them?

Only edit `.gitignore` after the user confirms. Use the user-supplied `MB_CONFIG_FILE_PATH` when adding the entry — if it's outside the repo, just warn instead of silently ignoring nothing.

### Step 4 — Start the developer instance

Use a fixed container name (`metabase-workspace-dev`) so subsequent start/stop/recreate commands can find it.

If a container with that name already exists, decide what to do:

```bash
docker ps -a --filter "name=^metabase-workspace-dev$" --format '{{.Status}}'
```

- **Empty output** → no container, run a fresh one (below).
- **Starts with `Up `** → already running. Tell the user the URL (`http://localhost:3000`) and stop. Don't restart anything.
- **Starts with `Exited`** → previously stopped. `docker start metabase-workspace-dev`.

To run a fresh container, source `.env` and exec docker in **one** command so the secrets stay in env vars and never reach the conversation:

```bash
( set -a; source .env; set +a;
  docker run -d -p 3000:3000 \
    --name metabase-workspace-dev \
    -v "$MB_CONFIG_FILE_PATH:/config.yml" \
    -e MB_CONFIG_FILE_PATH=/config.yml \
    -e MB_PREMIUM_EMBEDDING_TOKEN \
    metabase/metabase-enterprise:latest )
```

Note `-e MB_PREMIUM_EMBEDDING_TOKEN` (no value) — this passes through the host env var without exposing it on the command line.

After the command returns, tell the user the container is starting and that Metabase will be available at `http://localhost:3000` once boot finishes. Suggest `docker logs -f metabase-workspace-dev` if they want to watch progress.

### Step 5 — Boot may fail if databases aren't reachable

The container connects to the workspace's databases on startup. If they aren't reachable from the user's machine, the container will exit shortly after starting. Watch for this:

```bash
sleep 5
docker ps --filter "name=^metabase-workspace-dev$" --format '{{.Status}}'
```

If the container is no longer in `docker ps` (or shows `Exited`), tail the logs and tell the user:

> The container exited. The most common cause is that one of the databases listed in `config.yml` isn't reachable from your machine — VPN, firewall, or the database hostname only resolving inside production. Please verify connectivity to the databases your workspace exposes, then ask me to start it again.

Don't auto-retry — let the user fix it and re-trigger.

## When the user asks to stop

Just stop the container; don't remove it. The user may want to restart it later with the same config.

```bash
docker stop metabase-workspace-dev
```

If they explicitly say "remove the container", "delete it", or "tear it down", then also `docker rm` it.

## When the user downloads a new `config.yml`

Whenever the workspace's database list, schemas, or the workspace name itself changes in production, the user re-downloads `config.yml`. To pick that up, the local container has to be **fully recreated** — `docker restart` is not enough because the config is read once at boot and the bundled database credentials may have rotated.

Confirm with the user before destroying the existing container, then:

```bash
docker stop metabase-workspace-dev 2>/dev/null
docker rm   metabase-workspace-dev 2>/dev/null
```

…then run the fresh-container command from Step 4 again.

## What the user can ask, and what you do

| Phrase the user might say                                     | Action                                                          |
|---------------------------------------------------------------|-----------------------------------------------------------------|
| "set up a workspace", "configure a workspace", "set up the dev instance" | Walk through Steps 1–5 in order.                                |
| "start the workspace / dev instance"                           | Skip ahead to Step 4 (assume Steps 1–3 already passed; verify briefly). |
| "stop the workspace / dev instance"                            | `docker stop` it.                                               |
| "I downloaded a new config.yml"                                | Confirm, then full recreate.                                    |
| "remove / delete the dev instance"                             | `docker stop && docker rm`. Don't touch `.env` or `config.yml`. |

Never proactively run any of the docker commands at session start — only when the user asks.
