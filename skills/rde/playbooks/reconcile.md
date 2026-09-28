# Reconcile a number

Applies to "does this match finance", two cards that disagree, a number that looks wrong, and the first headline of any build before it leaves Draft. Produces a comparison at the finest shared grain, every gap bucketed with a cause, fixes re-measured, the ceiling named, standing controls, the result recorded.

Read first: `references/reconciliation.md`; the domain note's Invariants.

Order: 1 mode, 2 scope, 3 acceptance pair and plan (stop), 4 roll-forward identity, 5 compare, 6 bucket, 7 fix one rule at a time, 8 ceiling, 9 controls, 10 record, hand-back.

## 1. Mode

Per `references/reconciliation.md` (Validation modes; Baselines and disqualifiers). Search first: `mb search "<number>" --models metric,card,table`, and authoritative tables (`mb table list --db-id <db-id> --fields id,schema,name,data_authority --max-bytes 0`, filter `data_authority == "authoritative"`); then ask once for a reference at its finest grain. Never fabricate a figure. Record mode, reference, grain, pull date in the state file.

## 2. Scope

Per `references/reconciliation.md`, Scope the reference.

## 3. The acceptance pair, and the plan

The comparison's proposal point. Propose the pair (defaults: 95 percent of reference rows within 1 percent; net gap within 1 percent of the reference total); print the mode, reference and scope, grain and key, the pair, and what will be written (the reference table, the `cmp_<number>` transform, the saved question over it, and the standing controls with their alert and recipients); one `AskUserQuestion`. Nothing is uploaded or created before the answer. Then land the reference (`mb upload csv --file <path> --collection <id>` when `uploads-settings` points at the build's database, otherwise the user's loader) and mark it `mb table update <id> --body '{"data_authority":"authoritative","description":"<what, grain, pull date>"}'`.

## 4–9. Identity, compare, bucket, fix, ceiling, controls

Per `references/reconciliation.md`, in that order: the roll-forward identity first (a break is a build bug fixed through `playbooks/change.md`); `cmp_<number>` built like any transform (`playbooks/build.md` §3, `data_layer: internal`), plus a saved native question over it in the data-quality collection for the row-level export; every gap bucketed (the summary query through `q()` after `source ./.scratch/probe.sh`); one rule per fix through `playbooks/change.md`, its exposing row a test case first, logic the definition does not hold a stop for the owner, a moved headline restated (`playbooks/change.md` §5); the ceiling in two parts; standing controls with thresholds and owners.

## 10. Record the result

A decided line `reconciliation-<number>` (by the owner): reference, period, mode, hit rate, net gap, unexplained share; a disqualified or absent reference recorded with mode `none`. On a pass the label becomes `Reconciled to <reference>, <period>, within <tolerance>`, `Draft.` leaves the description if no open decision shapes it, the domain Document records it, and the hand-back asks the user to verify the metric in the UI.

## Done when

The mode is named; every gap row sits in one bucket; each fix was re-measured; the ceiling is split; the identity holds; controls run unattended; the result is recorded. Hand-back: the verdict in one sentence (how close, at which grain, in which universe), the pair against its thresholds, buckets largest first, what each fix moved, the ceiling in plain words.
