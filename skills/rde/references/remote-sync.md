# Remote sync

Read before any sync step when STATE.md `remote_sync` is not `none`, and always for a data app, which requires remote sync; with `none` and no app, nothing here applies (`SKILL.md`, "Where the work lands"). A data app reads only synced Library content: `rde-data-apps`, sections 4 to 6. Mechanics: `mb skills path git-sync`.

## What belongs in git

When remote sync is configured, the semantic layer is versioned in the repository: curated tables published to the Library with their field metadata, measures, and segments (these serialize only on a Library-published table in a synced Library collection; a measure on an unpublished table never reaches the repository, and an empty `mb git-sync dirty` after writing one means the scope is wrong, not that nothing changed); metrics in the Library's Metrics collection; models and transforms in synced collections. Dashboards live in ordinary collections, outside the Library, and are synced only when the company already syncs those collections.

When a set of definitions passes its gate (described, trust-labelled, verified), ask whether to sync it now rather than waiting for an app to need it. Clean up drafts before the first export: once exported, a mistake stays in the git history.

## Ask before every sync step

Every sync step publishes to a shared repository, so the user approves it first: flagging a collection for sync, switching `remote-sync-type`, `export`, `create-branch`, `stash`, `import`, any `--force`, and every `git push` to the synced remote. One checkpoint per sync point ([collaboration-contract.md](collaboration-contract.md)), not per command, saying plainly what will move and where: the objects from `mb git-sync dirty --json` by kind and name, the collections being flagged, the branch, the commit message, and what will change in Metabase for the people using it. Recommendation first; "not now" is always an option. Record the answer in STATE.md.

## Before each step

Remote sync merges per entity but resolves no conflicts. Run `mb git-sync status --json` (`is_dirty`, `branch`) and `mb git-sync has-remote-changes --force-refresh --json` before each step, every import and export included; without `--force-refresh` the answer can be a minute old.

- **Neither moved:** nothing to sync.
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

A conflict changes nothing: Metabase keeps its last sync point, and the remote keeps the teammate's work. Read why it stopped, then:

- **Nothing named in `conflicts`** (the task's `outcome.kind` is `remote-changed`: the remote moved on): run `mb git-sync export-preflight --json`; with `clean: true`, `mb git-sync export --merge -m "<what and why>"`.
- **Entities named in `conflicts`, or `clean: false`:** both sides changed them. Show the user which, and let them pick: the remote's side (`import --force`), the instance's side (`export --force`, which overwrites what `force_push_casualties` lists), or both through a reviewed branch (`create-branch <name>`, `export`, a PR, then `import --branch <tracked>` once it merges).
- **`history-rewritten`:** there is nothing to merge against. Only a `--force` either way, and only with the user's yes.

Running the preflight again, or the merge, is always safe. Only the `--force` moves discard work, and only the user chooses them.

## Staging

In staging (STATE.md `environment`), build freely. Then export the work to a job branch: `mb git-sync create-branch <job-branch>`, then `mb git-sync export -m "<what and why>"`. Don't use `export --branch <job-branch>`: on Metabase 63 and later it accepts only the tracked branch. The instance now tracks `<job-branch>`; record that in STATE.md. At the start of the next job, once the review has merged, run `mb git-sync import --branch <main>` so the new job branches from the reviewed work, not from the previous job branch. Never export to the main branch without confirmation. Hand back the branch for review; importing into production is the reviewer's step.
