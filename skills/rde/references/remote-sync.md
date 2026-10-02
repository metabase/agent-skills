# Remote sync

Read before any sync step when STATE.md `remote_sync` is not `none`, and always for a data app, which requires remote sync; with `none` and no app, nothing here applies (`SKILL.md`, "Where the work lands"). A data app reads only synced Library content: `rde-data-apps`, sections 4 to 6. Mechanics: `mb skills path git-sync`.

## What belongs in git

When remote sync is configured, the semantic layer is versioned in the repository: curated tables published to the Library with their field metadata, measures, and segments (these serialize only on a Library-published table in a synced Library collection; a measure on an unpublished table never reaches the repository, and an empty `mb git-sync dirty` after writing one means the scope is wrong, not that nothing changed); metrics in the Library's Metrics collection; models and transforms in synced collections. Dashboards live in ordinary collections, outside the Library, and are synced only when the company already syncs those collections.

When a set of definitions passes its gate (described, trust-labelled, verified), ask whether to sync it now rather than waiting for an app to need it. Clean up drafts before the first export: once exported, a mistake stays in the git history.

## Ask before every sync step

Every sync step publishes to a shared repository, so the user approves it first: flagging a collection for sync, switching `remote-sync-type`, `export`, `create-branch`, `stash`, `import`, any `--force`, and every `git push` to the synced remote. One checkpoint per sync point ([collaboration-contract.md](collaboration-contract.md)), not per command, saying plainly what will move and where: the objects from `mb git-sync dirty --json` by kind and name, the collections being flagged, the branch, the commit message, and what will change in Metabase for the people using it. Recommendation first; "not now" is always an option. Record the answer in STATE.md.

## Before each step

Remote sync merges nothing and resolves no conflicts. An import on a dirty instance is rejected, or with `--force` discards the instance's work; an export from an instance behind the remote pushes a stale state. Run `mb git-sync status --json` and `mb git-sync has-remote-changes --json` before each step, every import and export included. Import first when the remote moved; export first when the instance is dirty. Never `--force` either way without the user's yes.

## Staging

In staging (STATE.md `environment`): build freely, then export the work to a job branch with `mb git-sync export --branch <job-branch> -m "<what and why>"`, never to the main branch without confirmation, and hand back the branch for review; importing into production is the reviewer's step.
