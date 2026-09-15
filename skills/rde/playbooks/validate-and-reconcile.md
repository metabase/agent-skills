# Validate and reconcile

Applies when a built number must be proven against something outside itself, or disagrees with an existing one; produces a declared validation mode, a row-level comparison at the narrowest shared grain, a gap decomposed with a cause per bucket, a fix or a stated ceiling per cause, and standing controls. Data-quality checks prove self-consistency only.

Read first: [`reconciliation.md`](../references/reconciliation.md), [`ledgers-and-artifacts.md`](../references/ledgers-and-artifacts.md), [`collaboration-contract.md`](../references/collaboration-contract.md), the Tools and limits section of [`profiling-catalog.md`](../references/profiling-catalog.md) (full-extract path, dialect, row ceiling), `mb skills get notification` (alerts on saved questions), and `mb skills get transform` (scheduled transform-jobs).

## 1. Land the reference, declare the mode

Search before asking: `mb search "<term>" --models table,card --json`, reference-shaped warehouse tables, existing comparison transforms or cards. Ask for it at the finest grain, keyed by something both sides carry, before building. Land it with `mb upload csv --file <path>` only when `mb setting get uploads-settings --json` reports the build's database as `db_id`; otherwise the user lands the reference with their loader. Never fabricate a figure. Declare the validation mode from the table in `reconciliation.md`; with no reference, a pass rate proves nothing.

Check: mode, reference row count, grain, pull date in the ledger.

## 2. Filter the reference to the build's scope

Apply the scope filters first, each with its reason: the categories the build recognizes, no forecast or forward-filled rows, complete periods, the exclusions both sides claim. A reference covering part of the population is a coverage difference to report, not a defect.

Check: the comparison universe is one sentence, and every figure is quoted against it.

## 3. Reconcile at the narrowest shared grain

Build the comparison as its own transform (body from the bundled skill), or as a model in the company's tool, with the full-outer-join shape in `reconciliation.md`, on a declared key, at the grain the model produces; roll up to the reporting grain only after the row-level comparison passes.

Check: key declared, full outer join, model's own grain.

## 4. Decompose the gap

Bucket every compared row per `reconciliation.md`: per bucket, row count, signed and absolute contribution, share of total absolute gap. Net and gross together; agreement at several tolerance bands; top rows by absolute gap read one by one. Attribute each bucket to a cause, marked fixable or not; the rest stays explicitly unattributed. Compare dimensions too, not only the measure. Deliver the rows through the full-extract path in `profiling-catalog.md`, stating what the file omits.

Check: bucket counts sum to the compared row count; every headline count is computed from the comparison, never remembered.

## 5. Fix one rule at a time

Each fix changes one rule and is re-measured against the same reference under the same universe, reporting before and after per misclassification direction. Closing a gap with logic not in the plan is a checkpoint (block in [`collaboration-contract.md`](../references/collaboration-contract.md)), never a quiet addition; logic deliberately deferred goes on the deferred list in `reconciliation.md`.

Check: every iteration is in the ledger with its rule and its effect in each direction.

## 6. Declare the ceiling

Apply the ceiling rule in `reconciliation.md`: list each item the sources cannot carry with its reason and effect, apart from the deferred list; state the residual and stop.

## 7. Standing controls

Leave controls that run without you, from the standing-controls table in `reconciliation.md`, each an alert on a saved question (`mb skills get notification`), a scheduled transform-job (`mb skills get transform`), or a model in the company's tool. A movement classifier ships with the state and motion tables (Reconcile by construction, `reconciliation.md`).

Check: each control has a threshold, an owner, a place it runs.

## Done when

Every check in steps 1 to 5 and 7 passes, every bucket has a cause or an explicit non-attribution, and the residual is named with its causes.

## Reply

The verdict in one sentence: how close, at which grain, over which universe. Net and gross together. The gap buckets as a short table with causes; what you fixed and what moved; the ceiling in plain language; the controls running; the decisions waiting on the user.
