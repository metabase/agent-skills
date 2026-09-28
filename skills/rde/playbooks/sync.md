# Sync the work to a branch

Applies on a staging instance whose changes reach production as a reviewed change through remote sync. Produces the session's work on a job branch with a message saying what and why, handed to the reviewer. Importing into production is the reviewer's step, never yours.

Read first: the `git-sync` skill.

Order: 1 read state, 2 clean up, 3 scope, 4 branch, 5 export, hand-back.

## 1. Read the state

`mb git-sync status`: no remote configured is a stop for the admin, never a reason to write content as files. The state file must record go-live approval (build §7) for the work being exported; when it does not, that approval is asked here first. Then `mb git-sync is-dirty`, `dirty` (what the instance holds that the remote lacks) and `has-remote-changes` (the reverse): importing on a dirty instance is rejected; exporting while behind pushes a stale state.

## 2. Clean up before the first export

Delete what you created and mean to delete (smoke tests, dev copies, body-shape test cards, abandoned drafts) before the first export; afterwards the cleanup is a second commit and the failure stays in history. A transform is updated, never deleted and recreated.

## 3. Scope

Only flagged collections serialise: add each collection the work landed in (`mb git-sync add-collection <id>`; the flag cascades). The server refuses this while `remote-sync-type` is read-only (the install default); switching it (`mb setting set remote-sync-type '"read-write"'`) is a stop for the admin. Table and field metadata serialise only for Library-published tables whose Library Data collection is flagged; an empty dirty list after a metadata pass means that collection is out of scope.

## 4. Branch

Never export to `main` or `master`. From the main branch, `mb git-sync create-branch rde/<what>`: it exports the instance's current state to the new branch and switches the instance to track it, so later exports land there. When the instance holds team work that must not be lost, stash it to a fresh branch first. Exporting to the main branch only when the user asks by name, confirmed through `AskUserQuestion`.

## 5. Export

When the remote moved on, offer `mb git-sync import --branch <tracked>` first so the export carries the team's work. Then `mb git-sync export --branch rde/<what> --message "<what changed and why>"` (it waits for the task); report a failure with its message; read `is-dirty` back clean. `--force` on export overwrites the remote branch and on import discards instance work: both need the user's explicit word and never bypass a dirty state you did not read. Transform tests export with their transforms.

## Don't

- Hand-write repository files for instance content: formats the serializer does not own never apply on import, and writing behind Metabase races its sync.
- Read an empty dirty list as "untracked" before checking the scope.
- Mix direct writes and sync-tracked changes without exporting right after.

## Done when

The branch holds every change, the instance reads clean, and the reviewer has the branch, the message, the objects by kind, and the tests to run. Hand-back says importing into production is the reviewer's step (an import of the branch on production after review); the branch is recorded in the state file.
