# Remote sync

Read before any sync step when STATE.md `remote_sync` is not `none`, and always for a data app, which requires remote sync; with `none` and no app, nothing here applies (`SKILL.md`, "Where the work lands"). A data app reads only synced Library content: `rde-data-apps`, sections 4 to 6. Mechanics: `mb skills path git-sync`.

## What belongs in git

When remote sync is configured, the semantic layer is versioned in the repository: curated tables published to the Library with their field metadata, measures, and segments (these serialize only on a Library-published table in a synced Library collection; a measure on an unpublished table never reaches the repository, and an empty `mb git-sync dirty` after writing one means the scope is wrong, not that nothing changed); metrics in the Library's Metrics collection; models and transforms in synced collections. Dashboards live in ordinary collections, outside the Library, and are synced only when the company already syncs those collections.

When a set of definitions passes its gate (described, trust-labelled, verified), ask whether to sync it now rather than waiting for an app to need it. Clean up drafts before the first export: once exported, a mistake stays in the git history.

## Ask before every sync step

Every sync step publishes to a shared repository, so the user approves it first: flagging a collection for sync, switching `remote-sync-type`, `export`, `create-branch`, `stash`, `import`, any `--force`, and every `git push` to the synced remote. One checkpoint per sync point ([collaboration-contract.md](collaboration-contract.md)), not per command, saying plainly what will move and where: the objects from `mb git-sync dirty --json` by kind and name, the collections being flagged, the branch, the commit message, and what will change in Metabase for the people using it. Recommendation first; "not now" is always an option. Record the answer in STATE.md.

## Before each step

Remote sync merges per entity but resolves no conflicts. Run `mb git-sync status --json` and `mb git-sync has-remote-changes --force-refresh --json` before each step, every import and export included; without `--force-refresh` the answer can be a minute old.

- **Only the remote moved:** import. A plain import on a dirty instance is rejected; `import --merge` keeps the instance's work and folds the remote's in.
- **Only the instance is dirty:** export.
- **Both moved:** read `mb git-sync export-preflight --json` before exporting. With `clean: true`, `mb git-sync export --merge -m "<what and why>"` folds the remote's changes in and pushes both in one commit. With `clean: false`, `conflicts` names the entities changed on both sides, and the user chooses: `create-branch <name>` then `export` puts the instance's side on a new branch; `import --force` takes the remote's side; `export --force` takes the instance's side and discards what `force_push_casualties` lists.

`export-preflight` and `--merge` need Metabase 63 or later; `mb` refuses them on an older server. There, when both moved, the user chooses between the same three moves without a preview.

Renaming a collection moves every file inside it, so editing any of those entities on the other side is a conflict. Never `--force` without the user's yes.

After a task that ends in `conflict`, do not retry, and do not trust `has-remote-changes` or `export-preflight`: some servers then count the remote as synced, so both report nothing pending, a retry (`--merge` included) silently drops the remote's changes, and `force_push_casualties` comes back empty. Take the user's call between `create-branch <name>`, `export`, then `import --force` (keeps both: the instance's side lands on a new branch, the reload makes the instance match it, and a PR merges that branch into the tracked one), `import --force` alone (the remote's side), and `export --force` (the instance's side), saying plainly what each discards.

## Staging

In staging (STATE.md `environment`): build freely, then export the work to a job branch with `mb git-sync create-branch <job-branch>` then `mb git-sync export -m "<what and why>"` (on Metabase 63 and later, `export --branch` accepts only the tracked branch), never to the main branch without confirmation, and hand back the branch for review; importing into production is the reviewer's step.
