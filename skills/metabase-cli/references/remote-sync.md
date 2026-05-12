# Remote sync (representations ↔ instance)

Metabase content (cards, dashboards, transforms, snippets, collections, …) can live in a git repo as YAML and round-trip in and out of a Metabase instance via the `remote-sync` verbs. The instance is configured with a `remote-sync-*` settings block (URL, branch, token, type read-only/read-write); the CLI drives the sync tasks against `/api/ee/remote-sync/*`.

This file covers the import/export workflow. The general flag conventions and auth setup live in `../SKILL.md`. To author content YAML by hand, also load the `metabase-representation-format` skill — it covers the file-tree layout and per-resource YAML shape.

## Adding / removing a directory (collection) to remote sync

The set of directories under sync is governed by which **collections** carry `is_remote_synced: true`. Every collection so flagged serializes to its own folder under `collections/` in the repo; everything outside that set is local-only. The CLI exposes per-collection toggles that route to the underlying bulk endpoint (`PUT /api/ee/remote-sync/settings`):

```bash
metabase remote-sync add-collection    <collection-id> --profile <n> --json
metabase remote-sync remove-collection <collection-id> --profile <n> --json
```

`<collection-id>` is a **positive integer**. The bulk endpoint's schema is `pos-int? → boolean`; nano-id / `root` / `trash` refs (which `collection get` accepts) are not supported here. Get the id from `metabase collection list --profile <n> --json` first.

Both verbs return `{ success: true, task_id?: <id> }`. The optional `task_id` only appears when the toggle triggered a follow-up task (e.g., a finalization import after switching to read-only mode); for a normal add/remove in read-write, expect `{ success: true }` and nothing else.

**Cascade.** A toggle on a parent cascades to every descendant by `location` prefix — `add-collection 4` flips `4` plus every collection nested under it. `remove-collection 4` is the symmetric inverse. There is no per-leaf-only mode.

**Mode prerequisite.** The server rejects toggles while `remote-sync-type` is `:read-only` (the install default). If `metabase remote-sync add-collection 12` returns `Metabase returned 400 … Cannot change synced collections when remote-sync-type is read-only.`, switch first with:

```bash
metabase setting set remote-sync-type '"read-write"' --profile <n>
```

(Mind the inner double quotes — `setting set` parses the value as strict JSON.) The server also rejects switching to `:read-only` while the Remote Sync collection is dirty; export or `--force` import first if you're going the other way.

**Verifying the result.** The CLI's `Collection` schema doesn't yet expose `is_remote_synced`, so `collection get --json` won't show the flag. The pragmatic confirmation paths are:
- `metabase remote-sync is-dirty --profile <n> --json` after editing a card in the now-synced collection — a `true` reading proves it's tracked.
- The Metabase Admin UI's Remote Sync page renders the per-collection toggles.

## Read state before mutating

Always run `status` (or `is-dirty` + `has-remote-changes`) before `import` or `export`. Importing on a dirty instance silently rejects unless you pass `--force`; exporting when the instance is behind the remote pushes a stale state.

```bash
metabase remote-sync status              --profile <n> --json   # → branch, dirty, current task
metabase remote-sync is-dirty            --profile <n> --json   # → {dirty: bool}; instance has unexported changes
metabase remote-sync has-remote-changes  --profile <n> --json   # → {behind: bool}; remote has unimported commits
metabase remote-sync dirty               --profile <n> --json   # → list the dirty objects
metabase remote-sync current-task        --profile <n> --json   # → in-flight task (or idle)
```

**Clean up before exporting.** If you've created entities you intend to delete (a failed transform you're going to retry, a card you authored to test a body shape, a draft dashboard) — do the deletes *before* the first `remote-sync export`. Once committed, the cleanup needs a second commit, and the failed entity stays visible in `git log` forever. For the transform case specifically, prefer `transform update <id>` over `delete + create` so iteration never produces "broken-then-fixed" pairs in git history; see `references/transform.md` "Iterating on a failing transform".

## Import (remote → instance)

```bash
metabase remote-sync import --branch <branch> --profile <n>
# Default flags: --wait, polling --interval 2000 --timeout 600000
```

Pulls the configured branch and applies it to the instance. Polls until the task reaches a terminal state (`succeeded` / `failed`).

| Flag                | Purpose                                                                              |
| ------------------- | ------------------------------------------------------------------------------------ |
| `--branch <name>`   | Defaults to the `remote-sync-branch` setting; override per-call.                     |
| `--no-wait`         | Return as soon as the task is queued; combine with `metabase remote-sync wait` later.       |
| `--force`           | **Discards local Metabase-side dirty changes** (lossy). Confirm with the user first. |
| `--timeout <ms>`    | Polling deadline. Default 600 000.                                                   |
| `--interval <ms>`   | Polling cadence. Default 2 000.                                                      |

Workflow:
1. `remote-sync status` — confirm `dirty: false` (or `--force` is intended).
2. `remote-sync has-remote-changes` — confirm there's actually something to import.
3. `remote-sync import --branch <branch>` — runs to terminal status by default.

### First import on a fresh workspace

After `workspace start --repo …` brings up a brand-new workspace, the repo content **must be applied** before any other work — without it the instance has none of the repo content and subsequent edits will diverge from what's on disk.

The container runs a boot-time auto-import on first start, so in most cases the import has already completed by the time `workspace start --wait` returns. Check `remote-sync status` first — if `current_task.sync_task_type == "import"` with `status == "successful"` and `.branch` matches the host's branch, you're done; skip the explicit call (it's a wasted round-trip). Only run the explicit `remote-sync import` when the auto-import hasn't landed yet.

When you do need the explicit import, the first one on a fresh instance can report `status: conflict` (typically `conflicts: ["Transforms"]`) even when nothing is dirty — the boot-time auto-import sometimes leaves a stale task record that the first explicit import collides with. Retry the same command once; the second call usually succeeds. If it keeps reporting conflict, `remote-sync import --force` is safe in this specific case because the workspace is empty — there's no instance-side work for `--force` to discard. (This is a narrow exception to the usual "confirm with the user before `--force`" rule.)

```bash
HOST_BRANCH=$(git -C <repo-path> symbolic-ref --short HEAD)
SYNC_STATUS=$(metabase remote-sync status --profile <ws-name> --json)
if ! echo "$SYNC_STATUS" | jq -e --arg b "$HOST_BRANCH" \
     '.current_task.sync_task_type == "import" and .current_task.status == "successful" and (.branch == $b)' >/dev/null; then
  metabase remote-sync import --branch "$HOST_BRANCH" --profile <ws-name> --json \
    || metabase remote-sync import --branch "$HOST_BRANCH" --profile <ws-name> --json \
    || metabase remote-sync import --branch "$HOST_BRANCH" --force --profile <ws-name> --json
fi
```

## Export (instance → remote)

```bash
metabase remote-sync export -m "commit message" --branch <branch> --profile <n>
```

Pushes Metabase-side changes back to the configured remote. `-m` is the commit message; without it the server picks a default. Defaults to `--wait`.

| Flag                | Purpose                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| `--branch <name>`   | Push to a specific branch instead of the configured one.                 |
| `-m, --message <s>` | Commit message.                                                          |
| `--force`           | Force-push / overwrite remote. Confirm with the user.                    |
| `--no-wait`         | Don't poll.                                                              |

Workflow:
1. **Branch guard** (below) — confirm the workspace isn't tracking `main`/`master`, or that the user has explicitly accepted exporting to it.
2. `remote-sync is-dirty` — confirm there's something to export.
3. `remote-sync export -m "..."` — pushes and polls.
4. (Optional) `remote-sync status` — verify `dirty: false` after.
5. **Working-tree drift** (below) — if this is a `--repo` bind-mount workspace, the host repo's working tree + index will lag behind the new HEAD. Surface this and offer to realign.

### Branch guard: don't export to main/master without confirmation

Workspace work is conventionally done on a feature branch — exporting to `main` (or `master`) commits team-shared content directly. Before `remote-sync export`, check the tracked branch and if it's `main`/`master`, ask the user whether to switch first.

Reading the current branch:
- For a `--repo` bind-mount workspace, `git -C <repo-path> symbolic-ref --short HEAD` is the most reliable read — that's what the workspace's `remote-sync-branch` was bound to at start time.
- Otherwise: `metabase remote-sync status --profile <n> --json | jq -r '.branch'`.

If the branch is `main` or `master`, prompt with `AskUserQuestion`:

> "The workspace is tracking `<branch>` — exporting commits straight to it. Switch to a feature branch first?"
> 1. **Create a feature branch via the workspace** — agent suggests a name (e.g., `agent/<task>`); run `metabase remote-sync create-branch <name> --profile <n>`. This exports current dirty state to the new branch and switches the workspace's tracked branch to it; subsequent `remote-sync export` calls go to that branch.
> 2. **Switch the host's branch first (bind-mount workspaces)** — `git -C <repo> checkout -b <name>` on the host, then pass `--branch <name>` on the next `remote-sync export` so the export targets the new branch (the workspace's `remote-sync-branch` setting won't auto-update from a host-side checkout).
> 3. **Proceed on `main`/`master`** — explicitly accepted; surface the resulting commit (`git -C <repo> log --oneline -1`) afterwards so the user can amend or revert.

Skip the prompt only if the user's instructions already specified the branch (e.g., they explicitly said "export to main" or named a feature branch). Don't silently default to whatever `remote-sync-branch` happens to point at.

### Post-export: working-tree drift on `--repo` bind-mount workspaces

When the workspace exports against a host bind mount, the in-container serializer writes the new commit object directly into the bind-mounted `.git/` (creating tree/blob objects and advancing the branch ref) but **does not update the host's working tree or index**. After a successful export, the host repo state is:

- HEAD: the new export commit.
- Index: still matches the *previous* HEAD (whatever the user had staged before).
- Working tree: still matches the *previous* HEAD.

`git status` then shows "Changes to be committed" that look like the export's content reverting back — purely a display artifact, not an actual revert. The container does this on purpose to avoid clobbering work-in-progress on the host. **Realigning is *applying* the new HEAD's content to your worktree, not discarding work** — the new commit was written by the exporter, not by your local edits, and your tree/index are stale relative to the new HEAD until you realign.

**Surface this to the user** after an export against a `--repo` workspace — don't leave them staring at a confusing `git status`. Offer to realign.

**Prefer `git restore` over `git reset --hard`.** When the only "changes" are the drift artifact (no real local edits), `git restore` does the same job and isn't classified as a destructive operation by Claude Code's permission system — `git reset --hard` is, and gets blocked even after a user-confirmation dialog:

```bash
git -C <repo> restore --staged --worktree .   # non-destructive; aligns index + working tree to HEAD
```

This is the right default after a `remote-sync export` realignment when the user had nothing else staged. If `git status` shows a mix of drift artifacts and real pending work, fall back to the stash sequence:

```bash
git -C <repo> stash --include-untracked
git -C <repo> restore --staged --worktree .
git -C <repo> stash pop
```

`git reset --hard HEAD` is the canonical equivalent and still valid — but **confirm with the user** before running it, and expect Claude Code to gate it as destructive even after the dialog. `git restore --staged --worktree .` produces the same end-state with less friction.

Or pull in the new files selectively with `git -C <repo> checkout HEAD -- <path>`. Quick check that this is what you're seeing: `git -C <repo> diff --cached HEAD~1 --stat` returns empty (the index matches the parent commit, not the new HEAD).

## Branches

```bash
metabase remote-sync branches --profile <n> --json                 # list remote branches
metabase remote-sync create-branch <name> --profile <n>            # create + switch sync to it
metabase remote-sync stash --profile <n>                           # export current state to a NEW branch
```

`stash` is the safe move when the instance has team work you don't want to lose, but you need to pivot to a different branch (`import` would discard, `export --force` would overwrite). It exports current state to a fresh branch first.

## Polling and cancelling

```bash
metabase remote-sync wait --profile <n>             # block on the in-flight task
metabase remote-sync cancel-task --profile <n>      # cancel the in-flight task
```

Use `wait` after `import --no-wait` / `export --no-wait`. Use `cancel-task` if a remote-sync task hangs and you want to abandon it.

## Don't (remote-sync-specific)

- Don't run `remote-sync import --force` or `remote-sync export --force` without explicit user confirmation. Both are lossy — `--force` import discards instance-side work, `--force` export overwrites the remote branch.
- Don't drive `remote-sync` against a Metabase instance that doesn't have remote-sync configured — every verb returns an error pointing at the missing `remote-sync-*` settings. To check: `metabase setting get remote-sync-url --profile <n> --json`.
- Don't author content directly via `card create` / `transform create` and then assume `remote-sync export` will commit it cleanly — the instance and repo can drift if you mix direct API writes with remote-sync-tracked changes. If you do, follow direct writes immediately with `sync export -m "..."` to keep them in step.
- Don't omit `-m` on `export` if the user wants a meaningful commit message — the default server-generated message is generic.
- Don't `remote-sync export` to `main`/`master` without explicit user confirmation — workspace work is conventionally on a feature branch. See "Branch guard" above.
- Don't pretend the host's `git status` is clean after `remote-sync export` against a `--repo` bind mount — the export advances HEAD but leaves the working tree + index behind. See "Working-tree drift" above.
- Don't reach for `metabase setting set` to mark a collection as remote-synced — that endpoint writes single-key settings, not the bulk `collections` map. Use `metabase remote-sync add-collection <id>` / `metabase remote-sync remove-collection <id>` (see "Adding / removing a directory (collection) to remote sync" above), and remember the toggle cascades to descendants.
