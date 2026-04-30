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

The container reads two things from the host's `.env`:

- **`MB_PREMIUM_EMBEDDING_TOKEN`** — the EE license token. Sensitive.
- **`MB_CONFIG_FILE_PATH`** — the **host** path to `config.yml` (the file the user downloaded). Defaults to `./config.yml` at the repo root if the user hasn't placed it elsewhere.

Both `.env` and the `config.yml` it points to **must be gitignored** — they contain the EE token and the bundled database credentials, neither of which can be safely committed.

> Never `Read` or `cat` the `.env` file. Never echo or print its contents. Always source it inside a single `bash` command and reference the variables from there. The skill checks for the presence of keys with `grep -q`, never by reading values.

The remote-sync settings are **not** in `.env`. They're set directly in the docker-run script:

- `MB_REMOTE_SYNC_URL` — always `file:///workspace/.git` (the repo is mounted into the container at `/workspace`).
- `MB_REMOTE_SYNC_BRANCH` — captured at start time from `git rev-parse --abbrev-ref HEAD`. If the user switches branches and wants the dev instance to follow, recreate the container.
- `MB_REMOTE_SYNC_TYPE` — left unset. Metabase defaults to `:read-only`, which is what we want; the dev instance reads from the local repo and never pushes back.

Auto-import is intentionally **not** enabled. The user pulls new commits manually from the dev-instance UI (see the iteration section below) — that keeps imports under their control and avoids surprise sync runs while they're editing.

### Important: committing changes and pulling them into the dev instance

Git-sync reads from the repo's `.git` folder, not the working tree, and this skill leaves auto-import off — so a change is **invisible to the dev instance until two things happen**:

1. The change is committed on the branch the container was started against.
2. The user manually pulls it from the dev-instance UI: **Admin → Settings → Remote sync → click "Pull changes now"**.

Typical iteration cycle:

```sh
# edit files in your editor
git add <files>
git commit -m "iterate"
# then in the dev instance UI: Admin → Settings → Remote sync → "Pull changes now"
```

If the user reports "I changed X but the dev instance doesn't see it", check (in order):
1. Did they commit?
2. Are they on the same branch the container was started against?
3. Did they click "Pull changes now" in the dev instance after committing?

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

Two keys this skill expects in `.env`:

| Key | Source |
|---|---|
| `MB_PREMIUM_EMBEDDING_TOKEN` | user-supplied (license) |
| `MB_CONFIG_FILE_PATH` | user-supplied (path to `config.yml`) |

Check presence with grep — do not read values:

```bash
[ -f .env ] && echo "env-present" || echo "env-missing"
grep -q '^MB_PREMIUM_EMBEDDING_TOKEN=' .env 2>/dev/null && echo "has-token" || echo "no-token"
grep -q '^MB_CONFIG_FILE_PATH='        .env 2>/dev/null && echo "has-path"  || echo "no-path"
```

**If `.env` is missing**, create `.env.template` (do **not** write the real `.env` for them — they need to fill in the EE token themselves):

```env
MB_PREMIUM_EMBEDDING_TOKEN=
MB_CONFIG_FILE_PATH=./config.yml
```

Tell them: *"I created `.env.template`. Copy it to `.env` and fill in `MB_PREMIUM_EMBEDDING_TOKEN` from your Metabase license. Adjust `MB_CONFIG_FILE_PATH` if `config.yml` lives elsewhere. Let me know when done."*

If `.env` exists but a key is missing, ask the user to add it — you don't have the values. Continue once both keys are present.

### Step 3 — Ensure both files are gitignored

Read the repo's `.gitignore` (creating it empty if missing) and confirm both `.env` and the configured `config.yml` path (or default `./config.yml`) are ignored.

If either is not ignored, **ask before modifying** `.gitignore`:

> `.env` and/or `config.yml` aren't in `.gitignore`. They contain your EE token and database credentials — committing them would leak both. Shall I add them?

Only edit `.gitignore` after the user confirms. Use the user-supplied `MB_CONFIG_FILE_PATH` when adding the entry — if it's outside the repo, just warn instead of silently ignoring nothing.

### Step 4 — Start the developer instance

Use a fixed container name (`metabase-workspace`) so subsequent start/stop/recreate commands can find it.

If a container with that name already exists, decide what to do:

```bash
docker ps -a --filter "name=^metabase-workspace$" --format '{{.Status}}'
```

- **Empty output** → no container, run a fresh one (below).
- **Starts with `Up `** → already running. Skip to Step 5 to wait for `/api/health` and tell the user the URL.
- **Starts with `Exited`** → previously stopped. `docker start metabase-workspace`, then go to Step 5.

The container needs to see the host repo so it can git-sync from the local `.git` folder. Mount the repo read-only at `/workspace`, and pin the sync branch to whatever is currently checked out:

```bash
( set -a; source .env; set +a;
  branch=$(git rev-parse --abbrev-ref HEAD);
  if [ -z "$branch" ] || [ "$branch" = "HEAD" ]; then
    echo "Could not determine current git branch (detached HEAD?)" >&2; exit 1;
  fi;
  docker run -d -p 3000:3000 \
    --name metabase-workspace \
    -v "$MB_CONFIG_FILE_PATH:/config.yml" \
    -v "$PWD:/workspace:ro" \
    -e MB_CONFIG_FILE_PATH=/config.yml \
    -e MB_PREMIUM_EMBEDDING_TOKEN \
    -e MB_REMOTE_SYNC_URL=file:///workspace/.git \
    -e MB_REMOTE_SYNC_BRANCH="$branch" \
    metabase/metabase-enterprise:latest )
```

Notes:
- `-e MB_PREMIUM_EMBEDDING_TOKEN` (no value) passes through the host env var without exposing it on the command line.
- `MB_REMOTE_SYNC_TYPE` is intentionally not set — Metabase defaults to `:read-only`, which is what this skill wants.
- `MB_REMOTE_SYNC_BRANCH` is captured fresh from `git rev-parse` at start time. If the user switches branches later, the container won't follow until it's recreated (see the recreate section).
- The bind mount uses `:ro` because the dev instance never pushes back.

After the command returns, tell the user the container started and is booting. Suggest `docker logs -f metabase-workspace` if they want to watch progress, then go to Step 5.

### Step 5 — Wait until the instance is actually ready

Container start ≠ Metabase ready. The instance does app-DB migrations, applies `config.yml` (which can take seconds for warehouses with many tables), and only then begins serving real traffic. Poll Metabase's own readiness endpoint, `GET /api/health`:

- While booting it returns **`503`** with `{"status": "initializing", "progress": 0..1}`.
- Once ready it returns **`200`** with `{"status": "ok"}`.
- If the app DB connection fails it returns `503` with a different `status` message.

Poll for up to ~3 minutes, surfacing progress occasionally so the user knows things are moving:

```bash
deadline=$(( $(date +%s) + 180 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  resp=$(curl -fsS -o /tmp/mb-health.json -w '%{http_code}' http://localhost:3000/api/health 2>/dev/null || echo "000")
  if [ "$resp" = "200" ]; then
    echo "ready"; cat /tmp/mb-health.json; echo; break
  fi
  status=$(docker inspect -f '{{.State.Status}}' metabase-workspace 2>/dev/null || echo "missing")
  if [ "$status" != "running" ]; then
    echo "container-$status"; break
  fi
  echo "waiting... http=$resp $(cat /tmp/mb-health.json 2>/dev/null)"
  sleep 5
done
```

Branches:
- **`ready`** → tell the user *"The dev instance is ready at http://localhost:3000."* Done.
- **`container-exited` / `container-missing`** → the container died during boot. The most common cause is that one of the databases in `config.yml` isn't reachable from the user's machine (VPN, firewall, or the hostname only resolves inside the production network). Run `docker logs --tail 100 metabase-workspace` and tell the user:

  > The container exited during boot. Check that the databases your workspace exposes are reachable from this machine, then ask me to start it again.

- **Loop hit the deadline** → still 503 after 3 minutes. Don't keep waiting; tell the user to check `docker logs -f metabase-workspace`.

Don't auto-retry on failure — let the user fix the underlying issue and re-trigger.

## When the user asks to stop

Just stop the container; don't remove it. The user may want to restart it later with the same config.

```bash
docker stop metabase-workspace
```

If they explicitly say "remove the container", "delete it", or "tear it down", then also `docker rm` it.

## When the dev instance needs to be recreated

`docker restart` is not enough — the workspace config and the synced branch are both read once at boot. Recreate when:

- The user re-downloads `config.yml` (workspace databases / schemas / name changed in production).
- The user has switched git branches and wants the dev instance to follow.

Confirm with the user before destroying the existing container, then:

```bash
docker stop metabase-workspace 2>/dev/null
docker rm   metabase-workspace 2>/dev/null
```

…then run the fresh-container command from Step 4 again — it will pick up the current `git rev-parse --abbrev-ref HEAD` automatically.

## What the user can ask, and what you do

| Phrase the user might say                                     | Action                                                          |
|---------------------------------------------------------------|-----------------------------------------------------------------|
| "set up a workspace", "configure a workspace", "set up the dev instance" | Walk through Steps 1–5 in order.                                |
| "start the workspace / dev instance"                           | Skip ahead to Step 4 (assume Steps 1–3 already passed; verify briefly). |
| "stop the workspace / dev instance"                            | `docker stop` it.                                               |
| "I downloaded a new config.yml"                                | Confirm, then full recreate.                                    |
| "remove / delete the dev instance"                             | `docker stop && docker rm`. Don't touch `.env` or `config.yml`. |

Never proactively run any of the docker commands at session start — only when the user asks.
