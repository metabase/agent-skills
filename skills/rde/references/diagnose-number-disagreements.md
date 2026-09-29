# Diagnose a number disagreement

The read-only front end to [reconciliation.md](reconciliation.md) and `playbooks/validate-and-reconcile.md`: when the ask is only to explain or verify a disagreement — "why is X", "which is right", "is this number correct", one card against another or against an outside figure — resolve the object to its true grain and filters, isolate which layer is at fault, and attribute the gap, before standing up any comparison transform. Escalate to the playbook (comparison transform, standing controls) only when the number must be reconciled on a cadence or a fix must ship.

Read first: this file, [reconciliation.md](reconciliation.md) (validation mode, the bucket `CASE`), [state.md](state.md).

## The loop — each step is a query, not a claim

1. **Resolve the definition.** Never trust the title or the number. `mb card get <id> --fields name,dataset_query --json` (or `mb transform get <id> --full --json`). Read the actual MBQL/SQL: filters, aggregation, source.
2. **Walk the dependency chain to the base tables.** source-card → source-card → model → the rawest ingested tables upstream of every transform (`mb card get`, `mb table get <id> --include fields --json` at each hop). Record the exact filter and the join grain introduced at every hop.
3. **Reproduce two numbers.** (a) The card's figure as it stands — if you cannot reproduce it you do not yet understand it. (b) The number the card is *meant* to show, rebuilt straight from the base ingested tables, bypassing every transform and card.
4. **Isolate the layer before troubleshooting it.** Compare (a), (b), and the reference; where they first agree names the fault:
   - the base-table build agrees with the reference, the card does not → the fault is in the **modelling** (a transform or the card): a filter, a join grain, an aggregation. Troubleshoot there.
   - the base-table build disagrees with the reference too → the fault is in **ingestion**: the ingested table itself is wrong or stale, and no card fix will correct it. A "current-state" ingested table can be a derived snapshot that dropped history; look for a more primitive ingested source (an event log, a change/history feed, an append stream) and rebuild from whichever agrees. Do not debug the card for a defect the raw tables already carry.
5. **Decompose the faulty layer** along the suspect dimension — conditional aggregation (`count(*) FILTER (WHERE …)`), `count(*)` vs `count(distinct <key>)`, a per-key child-count distribution. Every bucket computed.
6. **Attribute and reconcile.** Bucket counts sum back to the headline, exactly. Name each bucket's class (below) and cause; declare the mode and reconcile per [reconciliation.md](reconciliation.md); state the residual in plain language.

## Three classes to check first

Most single-card disagreements are one of these; they sit in front of reconciliation.md's comparison buckets (scope maps to its `scope`, fan-out to its `dedup`, staleness to its `timing`/history note).

- **Scope / filter** — the two sides count different populations. Tell: a filter on one side, absent on the other (a category, a date window, a status, a sub-type the reference excludes). Probe: re-run each side under the other's filter.
- **Grain / fan-out** — a join multiplies rows, so the aggregate counts children, not parents. Tell: `count(*)` over a join to a one-row-per-child table (tags, labels, assignees, line items). Probe: `count(*)` vs `count(distinct <parent key>)`, plus a children-per-parent distribution. The child table is correct; counting its rows as parents is the bug, and the fix is in the query (`count(distinct)` or drop the join), never the child table.
- **Source staleness** — the row is present but no longer true. Tell: a "current" snapshot table disagrees with an event/history table or with the entity's own derived column. Probe: reduce the history **last-event-wins** per key and compare; a snapshot can retain deletes it never received. Quantify the stale set before asserting scale ([entities-and-time.md](entities-and-time.md) for the history source).

## Invariants

- Corroborate from the base before troubleshooting the top: a gap you can reproduce straight from the ingested tables is not the card's fault, and the isolation step (loop 3–4) runs before any card or transform is blamed.
- Reproduce before you explain; buckets sum to the total, exactly.
- **Validate any candidate fix against ground truth before recommending it.** A "cleaner" column or table you would switch the definition to is a `[CHECKPOINT]` until a query proves it matches the reference at the shared grain — never on its shape or name.
- Fixing source data makes rows accurate; it does not change grain. A fan-out survives a perfect source table — that fix is in the query.
- Compute, never remember: every count in the reply came from a query this session.

## Reply

Verdict in one sentence (how far apart, which grain, which universe, which layer), the bucket table (rows, cause, class), the residual named, and the fix at the right layer — ingestion vs transform vs query. If a fix ships or a recurring control is wanted, continue in `playbooks/validate-and-reconcile.md`.
