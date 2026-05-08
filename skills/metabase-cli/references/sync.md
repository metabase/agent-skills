# Remote sync (representations ↔ instance)

Metabase content (cards, dashboards, transforms, snippets, collections, …) can live in a git repo as YAML and round-trip in and out of a Metabase instance via the `sync` verbs. The instance is configured with a `remote-sync-*` settings block (URL, branch, token, type read-only/read-write); the CLI drives the sync tasks against `/api/ee/remote-sync/*`.

This file covers the import/export workflow. The general flag conventions and auth setup live in `../SKILL.md`. To author content YAML by hand, also load the `metabase-representation-format` skill — it covers the file-tree layout and per-resource YAML shape.

## Read state before mutating

Always run `status` (or `is-dirty` + `has-remote-changes`) before `import` or `export`. Importing on a dirty instance silently rejects unless you pass `--force`; exporting when the instance is behind the remote pushes a stale state.

```bash
metabase sync status              --profile <n> --json   # → branch, dirty, current task
metabase sync is-dirty            --profile <n> --json   # → {dirty: bool}; instance has unexported changes
metabase sync has-remote-changes  --profile <n> --json   # → {behind: bool}; remote has unimported commits
metabase sync dirty               --profile <n> --json   # → list the dirty objects
metabase sync current-task        --profile <n> --json   # → in-flight task (or idle)
```

**Clean up before exporting.** If you've created entities you intend to delete (a failed transform you're going to retry, a card you authored to test a body shape, a draft dashboard) — do the deletes *before* the first `sync export`. Once committed, the cleanup needs a second commit, and the failed entity stays visible in `git log` forever. For the transform case specifically, prefer `transform update <id>` over `delete + create` so iteration never produces "broken-then-fixed" pairs in git history; see `references/transform.md` "Iterating on a failing transform".

## Import (remote → instance)

```bash
metabase sync import --branch <branch> --profile <n>
# Default flags: --wait, polling --interval 2000 --timeout 600000
```

Pulls the configured branch and applies it to the instance. Polls until the task reaches a terminal state (`succeeded` / `failed`).

| Flag                | Purpose                                                                              |
| ------------------- | ------------------------------------------------------------------------------------ |
| `--branch <name>`   | Defaults to the `remote-sync-branch` setting; override per-call.                     |
| `--no-wait`         | Return as soon as the task is queued; combine with `metabase sync wait` later.       |
| `--force`           | **Discards local Metabase-side dirty changes** (lossy). Confirm with the user first. |
| `--timeout <ms>`    | Polling deadline. Default 600 000.                                                   |
| `--interval <ms>`   | Polling cadence. Default 2 000.                                                      |

Workflow:
1. `sync status` — confirm `dirty: false` (or `--force` is intended).
2. `sync has-remote-changes` — confirm there's actually something to import.
3. `sync import --branch <branch>` — runs to terminal status by default.

### First import on a fresh workspace

After `workspace start --repo …` brings up a brand-new workspace, **always run a `sync import`** — without it the instance never picks up the repo content, and subsequent edits will diverge from what's on disk.

The first import on a fresh instance often reports `status: conflict` (typically `conflicts: ["Transforms"]`) even when nothing is dirty. The boot-time auto-import leaves a stale task record that the first explicit import collides with. Retry the same command once; the second call usually succeeds. If it keeps reporting conflict, `sync import --force` is safe in this specific case because the workspace is empty — there's no instance-side work for `--force` to discard. (This is a narrow exception to the usual "confirm with the user before `--force`" rule.)

```bash
metabase sync import --branch <branch> --profile <ws-name> --json \
  || metabase sync import --branch <branch> --profile <ws-name> --json \
  || metabase sync import --branch <branch> --force --profile <ws-name> --json
```

## Export (instance → remote)

```bash
metabase sync export -m "commit message" --branch <branch> --profile <n>
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
2. `sync is-dirty` — confirm there's something to export.
3. `sync export -m "..."` — pushes and polls.
4. (Optional) `sync status` — verify `dirty: false` after.
5. **Working-tree drift** (below) — if this is a `--repo` bind-mount workspace, the host repo's working tree + index will lag behind the new HEAD. Surface this and offer to realign.

### Branch guard: don't export to main/master without confirmation

Workspace work is conventionally done on a feature branch — exporting to `main` (or `master`) commits team-shared content directly. Before `sync export`, check the tracked branch and if it's `main`/`master`, ask the user whether to switch first.

Reading the current branch:
- For a `--repo` bind-mount workspace, `git -C <repo-path> symbolic-ref --short HEAD` is the most reliable read — that's what the workspace's `remote-sync-branch` was bound to at start time.
- Otherwise: `metabase sync status --profile <n> --json | jq -r '.branch'`.

If the branch is `main` or `master`, prompt with `AskUserQuestion`:

> "The workspace is tracking `<branch>` — exporting commits straight to it. Switch to a feature branch first?"
> 1. **Create a feature branch via the workspace** — agent suggests a name (e.g., `agent/<task>`); run `metabase sync create-branch <name> --profile <n>`. This exports current dirty state to the new branch and switches the workspace's tracked branch to it; subsequent `sync export` calls go to that branch.
> 2. **Switch the host's branch first (bind-mount workspaces)** — `git -C <repo> checkout -b <name>` on the host, then pass `--branch <name>` on the next `sync export` so the export targets the new branch (the workspace's `remote-sync-branch` setting won't auto-update from a host-side checkout).
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

This is the right default after a `sync export` realignment when the user had nothing else staged. If `git status` shows a mix of drift artifacts and real pending work, fall back to the stash sequence:

```bash
git -C <repo> stash --include-untracked
git -C <repo> restore --staged --worktree .
git -C <repo> stash pop
```

`git reset --hard HEAD` is the canonical equivalent and still valid — but **confirm with the user** before running it, and expect Claude Code to gate it as destructive even after the dialog. `git restore --staged --worktree .` produces the same end-state with less friction.

Or pull in the new files selectively with `git -C <repo> checkout HEAD -- <path>`. Quick check that this is what you're seeing: `git -C <repo> diff --cached HEAD~1 --stat` returns empty (the index matches the parent commit, not the new HEAD).

## Branches

```bash
metabase sync branches --profile <n> --json                 # list remote branches
metabase sync create-branch <name> --profile <n>            # create + switch sync to it
metabase sync stash --profile <n>                           # export current state to a NEW branch
```

`stash` is the safe move when the instance has team work you don't want to lose, but you need to pivot to a different branch (`import` would discard, `export --force` would overwrite). It exports current state to a fresh branch first.

## Polling and cancelling

```bash
metabase sync wait --profile <n>             # block on the in-flight task
metabase sync cancel-task --profile <n>      # cancel the in-flight task
```

Use `wait` after `import --no-wait` / `export --no-wait`. Use `cancel-task` if a sync hangs and you want to abandon it.

## Don't (sync-specific)

- Don't run `sync import --force` or `sync export --force` without explicit user confirmation. Both are lossy — `--force` import discards instance-side work, `--force` export overwrites the remote branch.
- Don't drive `sync` against a Metabase instance that doesn't have remote-sync configured — every verb returns an error pointing at the missing `remote-sync-*` settings. To check: `metabase setting get remote-sync-url --profile <n> --json`.
- Don't author content directly via `card create` / `transform create` and then assume `sync export` will commit it cleanly — the instance and repo can drift if you mix direct API writes with sync-tracked changes. If you do, follow direct writes immediately with `sync export -m "..."` to keep them in step.
- Don't omit `-m` on `export` if the user wants a meaningful commit message — the default server-generated message is generic.
- Don't `sync export` to `main`/`master` without explicit user confirmation — workspace work is conventionally on a feature branch. See "Branch guard" above.
- Don't pretend the host's `git status` is clean after `sync export` against a `--repo` bind mount — the export advances HEAD but leaves the working tree + index behind. See "Working-tree drift" above.
