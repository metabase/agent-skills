# Extract business logic

Applies when rules live outside the instance's definitions (SQL files, a dbt project, application code, a wiki or spec, a spreadsheet, another BI tool) or the company wants its existing definitions mirrored. Produces a mirror (light path) or a tagged reference plus a gap report per requested number (migration path); no SQL on the migration path until the report is reviewed.

Read first: `references/extraction.md`, `references/profiling.md`.

Order: 1 path, 2 inventory, 3 read, 4 tag, 5 check live, 6 gap report, 7 ratify (stop), hand-back.

## 1. Pick the path

Per `references/extraction.md`, Two paths; the light path continues in `playbooks/semantic.md` (its proposal point applies).

## 2–4. Inventory, read, tag

What you can read locally or fetch; unreachable spaces are exported by the user on request or recorded unreachable; the scope, written down, is a decided line. Then the reading list, dating rules, tags, citations, contradictions, value inventory, and join map in `references/extraction.md`. No untagged claim; no `PROVEN` claim without a citation.

## 5. Check against live data

Every cited table and column exists (`mb table list --db-id <db-id> --fields id,name,schema`, `mb table get <id> --include fields`); the values behind each rule are profiled (`source ./.scratch/probe.sh && q "SELECT t.<col>, count(*) FROM <schema>.<table> t GROUP BY 1 ORDER BY 2 DESC LIMIT 50"`). Verdict-changing findings: a filter on a value that no longer occurs, a mapping covering only inactive keys, a documented uniqueness the data violates. On a fact about the data, the data wins; the divergence is a finding.

## 6. The gap report

Per `references/extraction.md`; instance ids stay in the state file. Kept as a local Markdown file until §7 returns; filed afterwards where the user keeps specifications, or as a document in the domain's collection.

## 7. Ratify

Present the report, then the open questions as one decision memo printed as a numbered list grouped by who answers, and one `AskUserQuestion` about it. This is the build's proposal point: write the decision lines to the state file before asking; after the answer, create the domain Document's decisions section as in explore §8. After the answer, reversible items left unchanged proceed on their defaults as open decisions; irreversible ones wait for their own yes; an unratified assumption enters the build as an open decision, never a fact. The ratified reference and report are the plan `playbooks/build.md` expects; worked examples found in artifacts become test cases.

## Done when

Every artifact read or marked unreachable; every claim tagged; every cited identifier checked live; the report's counts match a recount of the matrix; open questions recorded with owners. Hand-back: verdict counts and why, contradictions with both positions and dates, where the data disagreed with the documents.
