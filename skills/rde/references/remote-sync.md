# Remote sync

Read before the first collection, card, dashboard, or transform of a job and before any sync step when STATE.md `remote_sync` is not `none`, and always for a data app, which requires remote sync; with `none` and no app, nothing here applies (`SKILL.md`, "Where the work lands"). A data app reads only synced Library content: `rde-data-apps`, sections 4 to 6. Mechanics: `mb skills path git-sync`.

## What belongs in git

Remote sync carries what sits in a synced collection, each collection with its whole subtree, plus transforms when the `remote-sync-transforms` setting is on. The semantic layer lives in the Library: curated tables published to its Data collection with their field metadata, measures, and segments (these serialize only on a Library-published table in a synced Library; a measure on an unpublished table never reaches the repository, and an empty `mb git-sync dirty` after writing one means the scope is wrong, not that nothing changed); metrics in its Metrics collection. Dashboards, questions, documents, models, and `Definitions` live under STATE.md `synced_root`. Transforms, their tags, and their jobs sync together through the setting, all or none, never by collection.

When a set of definitions passes its gate (described, trust-labelled, verified), ask whether to sync it now rather than waiting for an app to need it. Clean up drafts before the first export: once exported, a mistake stays in the git history.

## Filing

- A domain collection is created under `synced_root`: `mb collection create --body '{"name":"Revenue","parent_id":<synced_root>}'`. The same for `Definitions` under it. A card or document saved straight into one by `collection_id` is filed; nothing more is needed.
- `Drafts` sits outside the synced tree, so work in progress never reaches an export. Moving finished work in goes leaf first: Metabase refuses to save a synced card, dashboard, or document that uses a card or metric outside the synced tree (`Uses content that is not remote synced.`). Move each card a dashboard or document shows, then the dashboard, then the document. The same message on a create means a card or metric the new object uses lives outside the synced tree, usually still in `Drafts`; move that first.
- The Library is never created by hand on an instance whose repository may hold one and has not been imported: `mb library publish` and `mb library create` both create it when absent, and a second Library conflicts on the next import. `rde init` creates it after the import; when `mb library get --json` shows none on an rde instance, ask before creating one.

## No synced root

Remote sync is configured but no top-level collection is synced (an instance set up before rde marked one, or a repository nobody has exported to yet): one checkpoint before the first collection is created, recommending one top-level collection for the work (`Analytics` unless the company names one), created, flagged with `mb git-sync add-collection <id>`, and recorded as `synced_root`; with the Library absent from `synced_collections`, flag it in the same answer. "Not now" files at the root as before, is recorded in STATE.md, and is named in every hand-back as content that will not reach git.

## Transforms

Before the first `mb transform create` of a job: `mb setting get remote-sync-transforms --json` reads `true` on an rde instance. An import from a repository without transforms switches it off. When it reads `false`, ask to switch it on (`mb setting set remote-sync-transforms true`), a sync step: without it the transform never reaches git, and the next import deletes it or stops on a deletion conflict.

## Ask before every sync step

Every sync step publishes to a shared repository, so the user approves it first: flagging a collection for sync, switching `remote-sync-type` or `remote-sync-transforms`, `export`, `create-branch`, `stash`, `import`, any `--force`, and every `git push` to the synced remote. One checkpoint per sync point ([collaboration-contract.md](collaboration-contract.md)), not per command, saying plainly what will move and where: the objects from `mb git-sync dirty --json` by kind and name, the collections being flagged, the branch, the commit message, and what will change in Metabase for the people using it. Recommendation first; "not now" is always an option. Record the answer in STATE.md. The scope `rde init` set (the Library, the `Analytics` collection it created or the synced collections the repository brought in, transforms) is already approved, and filing under a synced collection is not a sync step: neither is asked. Exporting that scope is a sync step: `rde init` offers it, and when the user declined or the branch had moved, the init summary says `Export pending` and the instance stays dirty until it is exported.

## Before each step

Remote sync merges nothing and resolves no conflicts. An import on a dirty instance is rejected, or with `--force` discards the instance's work; an export from an instance behind the remote pushes a stale state. Run `mb git-sync status --json` and `mb git-sync has-remote-changes --json` before each step, every import and export included. Import first when the remote moved; export first when the instance is dirty. When both hold, a plain import is refused and a plain export ends in `conflict`, which counts the remote commit as synced, so a retry no longer sees the remote's changes: run `mb git-sync export-preflight` and never retry a conflicted export. When the dirty objects are only the init scope (the Library and its Data, Metrics, and Dashboards collections, the synced root, the Transforms row), export with `--merge` (Metabase 63+), which folds the remote's changes in. With other work dirty too, `--merge` still applies, but objects changed on both sides end in `conflict`: show the preflight result and recommend `mb git-sync create-branch` and an export to that branch for review. An import that stops on a transform deletion conflict means a local transform was never exported: export first. Before an export, check every metric in `mb git-sync dirty` that uses a measure or segment: its table must read `"is_published": true` (`SKILL.md`, "Filing with a `synced_root`"); otherwise publish the table or rewrite the metric inline first, since the export carries the metric without what it uses. Never `--force` either way without the user's yes.

## Staging

In staging (STATE.md `environment`): build freely, then export the work to a job branch with `mb git-sync export --branch <job-branch> -m "<what and why>"`, never to the main branch without confirmation, and hand back the branch for review; importing into production is the reviewer's step.
