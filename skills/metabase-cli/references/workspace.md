# Workspaces (Enterprise)

A **workspace** is a child Metabase instance bound to a parent's databases. Local lifecycle is `metabase workspace <verb>`; the parent is reached via a profile (the parent's profile — typically `prod` / `staging`). Each provisioned database gets a per-workspace isolation schema on the warehouse, and the QP rewrites references from canonical names (`public.foo`) to that isolation schema (`mb__isolation_<hash>_<ws-id>.foo`) on the fly. Cards, transforms, and queries authored in the workspace target canonical names; the rewrite is invisible to the author.

This file covers the full lifecycle. The general flag conventions, auth setup, and output flags live in `../SKILL.md`; load that first.

## Always ask about Remote Sync before starting

Before running `metabase workspace start`, **ask the user how they want Remote Sync wired**. The bind mount is set at container-create time — you cannot add it later without a recreate, so this decision belongs at start time. Use `AskUserQuestion` with three options:

> "How should I wire Remote Sync for this workspace?"
> 1. **Current directory** — bind-mount the directory you're running Claude from (`pwd`) as `file:///mnt/repo` and set the workspace to remote-sync against it (read-write). Pick this when the conversation is happening inside the sync repo.
> 2. **Custom path** — you specify a different host directory; same wiring as option 1.
> 3. **No sync** — start the workspace without a repo bind mount; you can configure remote-sync against a remote URL later via `setting set`.

Default-suggest option 1 if the current working directory looks like a git repo (a `.git/` is present). Otherwise default-suggest option 3 and let the user volunteer a path.

Map the answer to flags on `workspace start`:

| Choice           | Flags to add to `workspace start`                                                  |
| ---------------- | ---------------------------------------------------------------------------------- |
| Current directory| `--repo "$(pwd)"`                                                                  |
| Custom path      | `--repo <path>`                                                                    |
| No sync          | (omit `--repo` — no bind mount, no remote-sync settings injected)                  |

The `--repo` flag (a) bind-mounts the host path into the container at `/mnt/repo`, and (b) injects three settings into the workspace's config.yml at boot: `remote-sync-url=file:///mnt/repo`, `remote-sync-branch=<HEAD>`, `remote-sync-type=read-write`. The branch defaults to the current branch of the host repo (read via `git -C <path> symbolic-ref --short HEAD`); override with `--repo-branch <name>`. Switch to read-only with `--repo-mode read-only` (also makes the bind mount read-only).

Do not skip this question — silently picking "no sync" loses the user's repo context, and silently picking "current directory" pushes work into a repo they didn't intend.

## Branch guard before `--repo`

When the user picks a `--repo` option (current dir or custom path), check the host's branch before `workspace start`. `--repo` reads `git -C <path> symbolic-ref --short HEAD` and injects it as the workspace's `remote-sync-branch` setting; that branch then becomes the default target for every subsequent `remote-sync import` and `remote-sync export`. If the host is on `main` (or `master`), every export commits straight to it — usually not what the user wants for ephemeral workspace work.

```bash
HOST_BRANCH=$(git -C <repo-path> symbolic-ref --short HEAD)
```

If `HOST_BRANCH` is `main` or `master`, ask the user via `AskUserQuestion`:

> "The host repo is on `<branch>` — the workspace will track and export to that branch by default. Switch to a feature branch first?"
> 1. **Create + checkout a feature branch on the host** — agent suggests a name (e.g., `agent/<task>`); run `git -C <repo-path> checkout -b <name>` then proceed with `workspace start --repo …` so the workspace tracks `<name>`.
> 2. **Pin the workspace to a specific branch** — pass `--repo-branch <name>` on `workspace start` to override host HEAD. The branch must exist **locally** in the bind-mounted host repo before `workspace start` (create it first with `git -C <repo-path> branch <name>` or `git -C <repo-path> checkout -b <name>`); it does **not** need to exist on `origin`. Local-only branches are fine — the workspace never pushes, and the remote side gets created on the user's first `git push` later.
> 3. **Proceed on `main`/`master`** — explicitly accepted; downstream `remote-sync export` will commit to that branch unless overridden per-call.

Skip this question only when the user's instructions already named the branch (e.g., they explicitly asked to work against `main`). The same guard applies later at `remote-sync export` time — see `references/remote-sync.md` "Branch guard".

## Quick start (copy-pasteable, end-to-end)

When a parent profile + license are in place, this whole sequence runs in one go. Replace the four shell vars; pick whether to bind-mount a sync repo with `REPO_FLAGS` per the question above.

```bash
PARENT=<parent>                              # e.g. prod — the parent profile name
WS_NAME=<ws-name>                            # e.g. my_nice_ws — also reused as the child profile name
DB_ID=<db-id>                                # parent database id from `metabase database list --profile $PARENT --json`
SCHEMAS=<schema1,schema2>                    # comma-separated; no "all" wildcard
REPO_FLAGS=(--repo "$(pwd)")                 # OR (--repo /path/to/sync-repo) OR () for no sync

# 0. Branch guard (only when REPO_FLAGS is non-empty). If the host repo is on
#    main/master, ask the user before continuing — see "Branch guard before --repo"
#    above. Skip when REPO_FLAGS is () (no sync = no branch).
if [ ${#REPO_FLAGS[@]} -gt 0 ]; then
  HOST_BRANCH=$(git -C "$(pwd)" symbolic-ref --short HEAD)
  case "$HOST_BRANCH" in main|master) ;; # ask user; not auto-resolvable
  esac
fi

# 1. Create empty workspace, capture id
WS_ID=$(metabase workspace create --name "$WS_NAME" --profile "$PARENT" --json | jq -r '.id')

# 2. Provision a database into it (blocks on :provisioned)
metabase workspace database provision "$WS_ID" \
  --database-id "$DB_ID" \
  --schemas "$SCHEMAS" \
  --wait \
  --profile "$PARENT"

# 3. Start the child container, block on state=running.
#    With REPO_FLAGS set, the child boots already wired to the local repo:
#    bind-mounted at /mnt/repo, remote-sync-url=file:///mnt/repo, branch from HEAD.
metabase workspace start "$WS_ID" --wait --profile "$PARENT" "${REPO_FLAGS[@]}"

# 4. Save the child's API key as its own profile (use the workspace name as profile name).
#    This is the documented exception to "the agent doesn't run auth login" — the child
#    key was minted by the parent the human authorized, and reading it via
#    `workspace credentials` is the supported path.
WS_URL=$(metabase workspace url "$WS_ID" --profile "$PARENT" --json | jq -r '.url')
WS_API_KEY=$(metabase workspace credentials "$WS_ID" --profile "$PARENT" --json | jq -r '.api_key')
printf '%s' "$WS_API_KEY" | metabase auth login \
  --url "$WS_URL" \
  --api-key-stdin \
  --profile "$WS_NAME" \
  --json

# 5. Smoke test: list child databases
metabase database list --profile "$WS_NAME" --json

# 6. (If REPO_FLAGS was set) Verify sync is wired:
metabase setting get remote-sync-url --profile "$WS_NAME" --json    # → "file:///mnt/repo"
metabase remote-sync status --profile "$WS_NAME" --json                    # → branch, dirty, current task

# 7. (If REPO_FLAGS was set) Ensure the repo has been applied to the fresh workspace.
#    The container's boot-time auto-import usually handles this on its own, so check
#    `remote-sync status` first — if `current_task` already shows a successful `import` for
#    the current branch, skip the explicit call (it's a no-op round-trip).
#    Only when the auto-import hasn't landed yet do you need an explicit import.
#    The first explicit import on a fresh instance can spuriously report
#    `status: conflict` (stale task state from the boot-time import); retry once,
#    then `--force` is safe because the workspace is empty (nothing to lose).
#    Skipping the import entirely is *not* safe — without it the instance has none
#    of the repo content and subsequent edits will diverge.
HOST_BRANCH=$(git -C "$(pwd)" symbolic-ref --short HEAD)
SYNC_STATUS=$(metabase remote-sync status --profile "$WS_NAME" --json)
if ! echo "$SYNC_STATUS" | jq -e --arg b "$HOST_BRANCH" \
     '.current_task.sync_task_type == "import" and .current_task.status == "successful" and (.branch == $b)' >/dev/null; then
  metabase remote-sync import --branch "$HOST_BRANCH" --profile "$WS_NAME" --json \
    || metabase remote-sync import --branch "$HOST_BRANCH" --profile "$WS_NAME" --json \
    || metabase remote-sync import --branch "$HOST_BRANCH" --force --profile "$WS_NAME" --json
fi
```

After step 5, drive the child via `metabase <verb> --profile $WS_NAME` for everything (cards, transforms, queries, …). To author a transform on the workspace, see `references/transform.md`. To use the sync flow (import host commits, export instance changes), see `references/remote-sync.md`.

## Setup (steps in order)

### 1. Parent profile

```bash
metabase auth status --profile <parent> --json
```

If a profile is missing or expired, **stop and ask the operator** to run, themselves:

> Please run `metabase auth login --url <parent-base-url> --profile <parent>` from your terminal and tell me the profile name when you're done.

Don't run `auth login` for them and don't suggest a URL — they pick. Verify with `metabase auth status --profile <parent> --json` once they confirm. If multiple parent profiles exist and the user hasn't named one, use `AskUserQuestion` to disambiguate.

### 2. License

```bash
metabase license status --profile <parent> --json
```

If `present: false`, ask the operator to run, themselves:

```bash
echo "<your-token>" | metabase license set --profile <parent>
```

A workspace child cannot start without a parent license — it inherits feature gates from the parent.

### 3. Find or create a workspace

```bash
metabase workspace list --profile <parent> --json
```

- Empty → create one (below).
- One workspace → use its `id`. Surface name + id to the user.
- Multiple → `AskUserQuestion`.

Create:

```bash
metabase workspace create --name "<descriptive-name>" --profile <parent> --json
```

Note the returned `id`. The workspace is empty; you must provision at least one database before `start` will succeed.

### 4. Provision databases

A workspace needs at least one provisioned database. Source databases come from the parent.

```bash
metabase database list --profile <parent> --json
```

For each source database, decide which schemas to expose. Enumerate the schemas the parent already syncs for that database:

```bash
metabase table list --db-id <db-id> --profile <parent> --json \
  | jq -r '[.data[].schema] | unique | .[]'
```

Provision (one db per call; `--schemas` is required, no "all" wildcard):

```bash
metabase workspace database provision <ws-id> \
  --database-id <db-id> \
  --schemas <schema1>,<schema2> \
  --wait \
  --profile <parent>
```

`--wait` blocks until status is `provisioned`. Repeat per source database.

Verify all are ready:

```bash
metabase workspace list --profile <parent> --full --json \
  | jq '.data[] | select(.id==<ws-id>) | .databases'
```

Every entry's `status` must be `provisioned`.

## Start

Before running `start`, ask the user about Remote Sync (see "Always ask about Remote Sync before starting" at the top of this file). The bind mount is decided at container-create time and cannot be added later without recreate.

### Pick a free port up front

Despite the `--port` flag's "auto-shifts up if taken" hint, in practice `workspace start` fails with `docker start failed for metabase-workspace-<id>` when the host port is occupied — typically by a stale workspace container from a prior session. **List local containers first** and pass an explicit free `--port`:

```bash
metabase workspace ps --profile <parent>          # → currently-running workspace containers + their host ports
docker ps --filter "name=metabase-workspace" \
  --format "{{.Names}}\t{{.Ports}}\t{{.Status}}"  # also surfaces stopped containers
```

If 3000 is taken, pass e.g. `--port 3322`. The child's URL in `workspace credentials` and `workspace url` reflects the chosen port automatically.

```bash
# No sync:
metabase workspace start <ws-id> --wait --profile <parent>

# With sync against the current directory:
metabase workspace start <ws-id> --repo "$(pwd)" --wait --profile <parent>

# With sync against a custom path, branch override, read-only:
metabase workspace start <ws-id> --repo /path/to/repo --repo-branch dev --repo-mode read-only --wait --profile <parent>
```

`--wait` blocks until `state: "running"`. Don't omit it for interactive bring-up — without it the next step (saving credentials as a child profile) races the container's HTTP listener and you'll get spurious connection errors.

| Flag                  | Purpose                                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--port <n>`          | Host port (default 3000; **does not** auto-shift reliably — pass an explicit free port if 3000 might be taken).        |
| `--wait`              | Block until `/api/health` reports ready before returning.                                                              |
| `--no-pull`           | Skip `docker pull` (image already present).                                                                            |
| `--no-metadata`       | Skip the warehouse metadata export.                                                                                    |
| `--force`             | Recreate even if a container for this workspace exists. Preserves the app db.                                          |
| `--timeout <ms>`      | Per-phase readiness deadline (default 240000). Covers the post-create config-consumption wait and (with `--wait`) the `/api/health` probe. Bump if the first cold boot exceeds the default — image pull + JVM startup can stretch on slow disks/networks. |
| `--repo <host-path>`  | Bind-mount a host directory at `/mnt/repo` and inject `remote-sync-url=file:///mnt/repo` into config.yml.              |
| `--repo-branch <name>`| `remote-sync-branch` value. Default: current branch of the host repo (`git symbolic-ref --short HEAD`).                |
| `--repo-mode <mode>`  | `read-write` (default) or `read-only`. Also flips the bind mount's mount mode.                                         |

**Notes on `--repo`:**
- `--repo` is honored only on container create. To change the mount on an existing container you must `start --force` (which recreates), passing `--repo` again. The app db volume persists, so users/sessions/saved questions survive.
- The host path must be a directory and must already exist. The CLI does not create or initialize a git repo for you.
- For `--repo-branch` auto-detection, the path needs to be a git repo (a `.git/` ancestor); otherwise pass `--repo-branch` explicitly.
- The `--repo-branch` value must name a branch that already exists **locally** in the host repo. Local-only branches (never pushed to `origin`) are fine — the workspace operates against the bind-mounted working tree, never pushes anywhere itself, and the remote side is created on the user's first `git push` later. If the branch doesn't exist locally yet, create it before `workspace start`: `git -C <repo-path> branch <name>` (or `checkout -b <name>` if you also want to switch HEAD).
- File-permission gotcha (Linux only): the Metabase container runs as uid 2000 by default; the host directory must be writable by that uid for `remote-sync export` to succeed. macOS Docker Desktop / OrbStack / Colima handle this via their file-sharing layer.

## Interact with a running workspace

`url` and `credentials` both return JSON envelopes. Extract fields with `jq`:

```bash
metabase workspace url <ws-id> --profile <parent> --json
# → {"workspace_id": ..., "url": "http://localhost:3000"}

metabase workspace credentials <ws-id> --profile <parent> --json
# → {"email": ..., "password": ..., "api_key": ...}
```

Save the child's API key as its own named profile. **Always pipe the key on stdin** (the CLI rejects `--api-key "$VAR"`).

```bash
WS_URL=$(metabase workspace url <ws-id> --profile <parent> --json | jq -r '.url')
WS_API_KEY=$(metabase workspace credentials <ws-id> --profile <parent> --json | jq -r '.api_key')
printf '%s' "$WS_API_KEY" | metabase auth login \
  --url "$WS_URL" \
  --api-key-stdin \
  --profile <ws-name> \
  --json
```

Convention: use the workspace name as the profile name (`my_nice_ws` workspace → `my_nice_ws` profile). Then drive the child with the same CLI verbs:

```bash
metabase database list  --profile <ws-name> --json
metabase card list      --profile <ws-name> --json
metabase transform list --profile <ws-name> --json
```

To create and run a transform in the workspace, load `references/transform.md`. The `<db-id-in-child>` referenced there comes from `metabase database list --profile <ws-name> --json` — the child re-numbers databases independently of the parent.

## Open the UI

```
http://localhost:<port>                                # default 3000; honors `--port` from `workspace start`
http://localhost:<port>/admin/transforms/<transform-id>
```

Log in with the **admin email + password** from `workspace credentials` (the API key authenticates as a synthetic api-key user, not as the admin — many UI screens hide content from the api-key user).

**Don't open the URL before `state: "running"`** — the Metabase setup wizard will hijack it and create a fresh app db, bypassing the workspace bring-up.

## Lifecycle

| User intent                            | Command                                                       |
| -------------------------------------- | ------------------------------------------------------------- |
| List local workspace containers        | `metabase workspace ps --profile <parent>`                    |
| Tail logs                              | `metabase workspace logs <ws-id> --tail 200 --profile <parent>` |
| Follow logs                            | `metabase workspace logs <ws-id> --follow --profile <parent>` |
| Read admin email/password/API key      | `metabase workspace credentials <ws-id> --profile <parent> --json` |
| Stop (preserves app db)                | `metabase workspace stop <ws-id> --profile <parent>`          |
| Restart                                | `metabase workspace start <ws-id> --force --wait --profile <parent>` |
| Remove container + app db              | `metabase workspace remove <ws-id> --yes --profile <parent>`  |
| Remove container, keep app db          | `metabase workspace remove <ws-id> --keep-volume --yes --profile <parent>` |

The supported restart path is `stop` + `start --force` (or `start --force` directly). The app db volume persists across `stop`/`start` cycles, so users/sessions/saved questions survive. `remove`, `start --force`, and `stop` are destructive enough to confirm before running unless the user explicitly asked for them.

## Diagnose

Pick the symptom.

### `start` succeeds but the database isn't visible in the UI

```bash
metabase workspace logs <ws-id> --tail 300 --profile <parent> | grep -iE "advanced-config|workspace|error"
```

| Log signal                                                       | Cause                                                                | Fix                                                                                                                       |
| ---------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `Spec assertion failed ... :input ... :output`                   | Parent emits keys the child's spec doesn't accept (server-side).     | File against the parent. Not a CLI issue.                                                                                 |
| `Connection refused` / `unknown host` against the warehouse host | Container can't reach the source DB.                                 | Source DB credentials configured on the parent use a host that doesn't resolve from inside docker. Use a routable hostname. |
| `Invalid token` / `License expired`                              | EE license bad or unset on the parent (forwarded into the child).    | Re-set on the parent: `metabase license set` (operator pastes).                                                           |

### `workspace credentials` returns values that don't authenticate

Symptom: right after `workspace start`, the API key returned by `metabase workspace credentials <ws-id>` is rejected by the child (`Unauthenticated` on `/api/user/current`, or `Invalid or unauthorized API key` from `metabase auth login --skip-verify` followed by any verb). The admin password from the same response also fails (`did not match stored password`). The values inside the container's `/mw-config/credentials.json` match what the parent reports, but the child's app db has different state.

This is a parent↔child credential drift bug — the parent's record for the workspace can desync from the child's app db, especially after a rapid `start` → `start --force` sequence on the same port. **`start --force` alone does not fix it** (the volume persists across the recreate; the api-key already exists from the prior init and the new credentials.json is ignored).

Recovery (works reliably):

```bash
metabase workspace remove <ws-id> --yes --profile <parent>     # destroys container + volume; keeps parent record + provisioned dbs
metabase workspace start  <ws-id> --port <fresh-port> --wait --profile <parent>  # different port from the bad attempt
metabase workspace credentials <ws-id> --profile <parent> --json | jq -r '.api_key' \
  | xargs -I{} curl -s -H "x-api-key: {}" http://localhost:<fresh-port>/api/user/current   # smoke check
```

Why "different port": empirically, restarting on the same port after the drifted attempt can cling to the same broken state; switching ports forces a clean parent-side handoff. If you must reuse the original port, `workspace remove --yes` plus a brief pause (a few seconds) before `start` increases the success rate.

`workspace remove --yes` is destructive — it drops the container *and* the app db volume — but in the bring-up window (before any user content has been imported) there's nothing to lose. The provisioned-database records on the parent survive the remove and don't need to be re-created.

### Container exited shortly after `start`

```bash
metabase workspace ps --profile <parent>
```

`Exited (137)` → OOM. Bump Docker host memory to ≥ 6 GB.
- Colima: `colima stop && colima start --memory 6 --cpu 2`
- Docker Desktop: Settings → Resources → Memory.

Then `metabase workspace start <ws-id> --force --wait --profile <parent>`.

### `Endpoint not found — is this a Metabase instance?`

The parent doesn't expose `/api/ee/workspace-manager/*`. Either:
- Parent is OSS (no EE).
- Parent has no license, or license lacks the workspace feature.
- Parent is on a Metabase version that predates workspaces.

Confirm the URL points at the right instance with `metabase auth status --profile <parent> --json`. If the URL is correct, the parent simply lacks the workspace feature — pick a different instance.

### `workspace has no databases — provision at least one before starting`

`metabase workspace list --profile <parent> --full --json` will show the workspace with `databases: []`. Run a `provision` (step 4) and retry.

### `workspace ... is not ready: database X=provisioning`

Provisioning is async on the parent. Re-run the original `provision` with `--wait`, or poll:

```bash
metabase workspace list --profile <parent> --full --json \
  | jq '.data[] | select(.id==<ws-id>) | .databases[] | {database_id, status}'
```

### Workspace UI demands the setup wizard

You opened the URL before health passed and walked through the wizard, which created a fresh app db and bypassed the workspace bring-up. `metabase workspace remove <ws-id> --yes --profile <parent>` then `start --wait` again. Don't open the URL before `state: "running"`.

### `git status` on the host shows confusing "staged changes" after `remote-sync export`

The in-container exporter writes the new commit object directly into the bind-mounted `.git/` and advances HEAD, but does not update the host's working tree or index. The host then shows the export's content as "Changes to be committed" reverting to the prior commit — display artifact, not a real revert. The non-destructive realignment is `git -C <repo> restore --staged --worktree .` (only touches paths that disagree with HEAD; refuses on unmerged paths; does not move HEAD). See `references/remote-sync.md` "Working-tree drift on `--repo` bind-mount workspaces" for the full decision tree (when to stash first, when `reset --hard` is acceptable).

## Don't (workspace-specific)

- Don't run raw `docker` commands against the workspace container — use the `metabase workspace` subcommands. They wrap the right labels, volumes, network, and lifecycle hooks.
- Don't open the workspace URL before `state: "running"` — the setup wizard will hijack it.
- Don't try to share an API key across workspaces — each child mints its own. Save credentials per-workspace under a profile named after the workspace.
- Don't write the workspace's isolation schema (`mb__isolation_<hash>_<ws-id>`) into transform/card SQL or `target.schema`. Author against the **canonical** schema (e.g. `public`); the QP rewrites at execution time. Hard-coding the isolation prefix breaks portability across workspaces and bypasses the rewrite contract.
- Don't run `workspace start` without first asking the user about Remote Sync (current dir / custom path / no sync). The bind mount is set at create time; "I'll add it after start" is not supported.
- Don't run `workspace start --repo <path>` when the host repo is on `main`/`master` without first asking the user (see "Branch guard before `--repo`"). The host's HEAD becomes the workspace's `remote-sync-branch`, so every subsequent export targets `main` by default.
