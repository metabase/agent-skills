# Extract business logic from existing artifacts

Applies when the rules exist in code, documents, a transformation project, or a spreadsheet; produces a builder's reference independent of the originals, every claim tagged by confidence, a gap report per requested number, and ratified assumptions. No SQL is written.

Read first: the specification-extraction, gap-report, and specification-versus-build-instructions sections of [`ledgers-and-artifacts.md`](../references/ledgers-and-artifacts.md), [`profiling-catalog.md`](../references/profiling-catalog.md), and [`collaboration-contract.md`](../references/collaboration-contract.md).

## 1. Inventory the artifacts

Scope is what you can read locally or fetch; an unreachable document space is one the user exports on request. List every repository, document space, and export; record an unreachable one per the unreachable-sources rule in `ledgers-and-artifacts.md`.

Check: each artifact is marked reachable or not; the crawl scope is written down.

## 2. Read exhaustively

Apply the code reading list and the document dating and tagging rules from `ledgers-and-artifacts.md` to every artifact in scope.

Check: every child page and linked file in scope was read, not only the pages handed to you.

## 3. Tag every claim

Apply the claim tags, the citation rule, the contradiction rule, and the two mandatory sections (hardcoded-value inventory, join map) from `ledgers-and-artifacts.md`; the document's opening lines state the tagging scheme.

Check: no untagged claim; no `PROVEN` claim without a citation.

## 4. Check against live data

Confirm every cited table and column exists (`mb table list --db-id <db-id> --fields id,name,schema --max-bytes 0 --json`, then `mb table get <id> --include fields --json`) and profile the values behind each rule with `profiling-catalog.md`. Verdict-changing findings: a filter on a value that no longer occurs; a mapping covering only inactive keys; a documented uniqueness rule the data violates. On a fact about the data, the data wins; the divergence is a finding.

Check: every cited identifier was verified against the live catalog.

## 5. Build the gap report

One record per requested number and dimension in the gap-report format from `ledgers-and-artifacts.md`, opening with the verdict matrix.

Check: the summary counts match a recount of the matrix; no cited column skipped step 4.

## 6. Stop and ratify

Present the gap report and wait. Group open questions by owner, one sentence each; a decision uses the checkpoint block in [`collaboration-contract.md`](../references/collaboration-contract.md). Record every resolution in the assumption ledger; an unratified assumption enters the build as a pre-registered checkpoint, never as a fact.

Check: no unresolved question is about to become a modeling choice made alone.

## 7. Hand off

Split the deliverable per Specification versus build instructions in `ledgers-and-artifacts.md`: the ratified reference is the specification, the gap report and environment values are the build instructions; together they are the approved plan [`build-clean-tables.md`](build-clean-tables.md) expects. Validation against the original artifact's own output measures parity only (validation-mode table in `reconciliation.md`); say so.

## Done when

Every check in steps 1 to 6 passes and the user has approved.

## Reply

What can and cannot be built, as three counts and one sentence on why. The contradictions found, both positions with dates. Where the data disagreed with the documents. The open questions grouped by who can answer them. Nothing is built; approval starts the build.
