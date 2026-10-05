# Remote sync

Read before any sync step when STATE.md `remote_sync` is not `none`, and always for a data app, which requires remote sync; with `none` and no app, nothing here applies (`SKILL.md`, "Where the work lands"). A data app reads only synced Library content: `rde-data-apps`, sections 4 to 6. Mechanics: `mb skills path git-sync`.

## What belongs in git

When remote sync is configured, the semantic layer is versioned in the repository: curated tables published to the Library with their field metadata, measures, and segments (these serialize only on a Library-published table in a synced Library collection; a measure on an unpublished table never reaches the repository, and an empty `mb git-sync dirty` after writing one means the scope is wrong, not that nothing changed); metrics in the Library's Metrics collection; models and transforms in synced collections. Dashboards live in ordinary collections, outside the Library, and are synced only when the company already syncs those collections.

When a set of definitions passes its gate (described, trust-labelled, verified), ask whether to sync it now rather than waiting for an app to need it. Clean up drafts before the first export: once exported, a mistake stays in the git history.

## Ask before every sync step

Every sync step publishes to a shared repository, so the user approves it first: flagging a collection for sync, switching `remote-sync-type`, `export`, `create-branch`, `stash`, `import`, any `--force`, and every `git push` to the synced remote. One checkpoint per sync point ([collaboration-contract.md](collaboration-contract.md)), not per command, saying plainly what will move and where: the objects from `mb git-sync dirty --json` by kind and name, the collections being flagged, the branch, the commit message, and what will change in Metabase for the people using it. Recommendation first; "not now" is always an option. Record the answer in STATE.md.

## Before each step

Remote sync merges per entity but resolves no conflicts. Run `mb git-sync status --json` (`is_dirty`, `branch`) and `mb git-sync has-remote-changes --force-refresh --json` before each step, every import and export included; without `--force-refresh` the answer can be a minute old.

- **Only the remote moved** (`is_dirty: false`): `mb git-sync import`.
- **Only the instance is dirty:** `mb git-sync export -m "<what and why>"`.
- **Both moved:** read `mb git-sync export-preflight --json` before exporting.
  - `clean: true`: `mb git-sync export --merge -m "<what and why>"` folds the remote's changes in and pushes both in one commit. `mb git-sync import --merge` instead pulls first and keeps the instance's work.
  - `clean: false` with entities in `conflicts`: the user chooses between a reviewed PR from a new branch (`create-branch <name>`, `export`, a PR into the tracked branch, then `import --branch <tracked>` once it merges), `import --force` (the remote's side), and `export --force` (the instance's side; it discards what `force_push_casualties` lists).
  - `reason: "history-rewritten"`: the remote was force-pushed, so nothing can merge. Show the user `force_push_casualties`; only `export --force` can push, or `import --force` takes the remote.
  - Not `stash`: its new branch starts at the moved remote tip, so it ends in `conflict` too.

`export-preflight` and `--merge` need Metabase 63 or later; `mb` refuses them on an older server. There, a plain export against a moved remote is refused with 400 rather than ending in a `conflict` task: treat it as `clean: false` and ask the user between the same three moves, without a preview.

Renaming a collection moves every file inside it, so editing any of those entities on the other side is a conflict. Never `--force` without the user's yes.

### After a `conflict` task

Do not retry, and do not decide from `has-remote-changes`, `export-preflight` or `force_push_casualties`. Some servers then count the remote as synced: all three report nothing pending, and a retry (`--merge` included) succeeds without bringing the remote's changes into the instance, which stays silently out of date until a later edit or forced export overwrites them. Offer the user three choices, saying what each discards:

- **The remote's side:** `mb git-sync import --force`. Discards the instance's un-exported work.
- **The instance's side:** `mb git-sync export --force`. Overwrites the remote; its casualties can't be previewed here, so show the user the remote's commits since the last export in git first.
- **Both, through a reviewed PR:**
  1. Record the tracked branch from `mb git-sync status --json` (`branch`) in STATE.md: this is `<original>`.
  2. `mb git-sync create-branch <name>`
  3. `mb git-sync export -m "<what and why>"`
  4. `mb git-sync import --force`, which reloads the instance from `<name>`.
  5. Open a PR from `<name>` into `<original>` and review its diff with the user before it merges. On a server that counted the conflict as synced, `<name>` starts at the remote's tip, so the PR can undo the remote's edits to the conflicting entities without a git conflict: restore any such edit in the PR.
  6. Wait for the user to confirm the PR merged, then run `mb git-sync import --branch <original>` to track it again and load the merged result.

## Staging

In staging (STATE.md `environment`), build freely. Then export the work to a job branch: `mb git-sync create-branch <job-branch>`, then `mb git-sync export -m "<what and why>"`. Don't use `export --branch <job-branch>`: on Metabase 63 and later it accepts only the tracked branch. The instance now tracks `<job-branch>`; record that in STATE.md. Never export to the main branch without confirmation. Hand back the branch for review; importing into production is the reviewer's step.
