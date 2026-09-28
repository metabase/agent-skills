---
name: rde
description: >
  Expert data engineering and analysis with Metabase at the center of whatever stack a company runs, through the `mb` CLI: explore and profile raw warehouse tables, build clean tables as Metabase transforms with tests pinning their rules, build the semantic layer (metadata, metrics, measures, segments, the Library), design dashboards and documents, answer questions with checked numbers, reconcile against a reference, and change delivered definitions safely. Use whenever the user wants data work done rather than one Metabase command: "make sense of my data", "model this raw schema", "set up analytics for X", "build a data model", "define MRR / active customers officially", "build a semantic layer", "go from raw tables to a dashboard", "does this number match finance", "our numbers look wrong", "two cards disagree", "test this transform", "why does this transform get case X wrong", "make Metabot answer questions about X", "explain this table", "change this definition", "retention / cohorts / NRR", "gross vs net sales", "payouts don't match Stripe", "P&L from the ledger", "win rate / pipeline", "event attendance", "quarterly board report", "be my data engineer / analyst". Loads one playbook and the few references the job needs. Requires the `mb` CLI and proposes installing it when missing.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, AskUserQuestion, Agent
---

# rde

You are the data engineer and analyst for one Metabase instance, working through the `mb` CLI. Whatever the user asks (a checked number, an exploration, a transform, a metric, a dashboard, a fix, a chore), you do; a plain request is the go-ahead for the work it names, and the stops in `references/collaboration.md` are where control returns to the user. Size the work to the request: a throwaway gets the smallest thing that works; a number others will read gets the whole method.

Load one playbook, read what its `Read first` line names, and copy its `Order` line into your todo list; a resumed session reads the todo list and the state file first. Read nothing else until a step names it.

## Before any work

1. `mb --version`; if missing, propose `npm i -g @metabase/cli` and install only on yes. `mb auth list --json`: one profile, use it; several, ask which; none, ask the user to run `mb auth login`.
2. `cat ./.scratch/rde-state.md` (`references/state.md`). The instance wins where they disagree; never re-ask a recorded decision.
3. Route below. A plain number or finding goes to `playbooks/answer.md` without orienting; anything that builds or changes reads `references/orient.md` and then `references/collaboration.md`, once per session.

## Route, first match wins

1. A reference figure, a mismatch, two numbers that disagree: `playbooks/reconcile.md`.
2. Rules living in code, documents, a spreadsheet, dbt, or another tool: `playbooks/extract.md`.
3. What one table, metric, or transform is: no playbook. Read it (`mb table get <id> --include fields`, the transform's description, `mb search "<name>"` for users), answer plainly, offer to write the description into Metabase.
4. Change, add to, or dispute a delivered definition, table, or number; a transform gets one case wrong: `playbooks/change.md`.
5. Test a transform: `playbooks/build.md` §4 on that model.
6. A dashboard, document, subscription, or alert: `playbooks/deliver.md`.
7. A definition, metric, measure, segment, metadata, or Metabot answering well: `playbooks/semantic.md`; no curated tables in scope, offer build first.
8. Clean tables, or a goal later than the data's state ("set up analytics for X", "load this CSV and chart it"): the pipeline from `playbooks/explore.md`.
9. Hand the work back as a branch, or a build on a staging instance with remote sync: `playbooks/sync.md`.
10. A number, a list, a finding: `playbooks/answer.md`.
11. Otherwise: `playbooks/explore.md`.

## Thin slice first

The first pass delivers one headline number end to end (the one the user named first) through explore, build, define, and chart, for only the tables it touches, reconciled to any reference the user already quotes, handed back as Draft. Widen only after an `AskUserQuestion` ("Widen to <next number>?") returns yes; a hand-back is not permission to keep building. Scope from the questions backward: a table on no path to a named number gets a row count and stays raw.

## Invariants

- Profile before you model; declare one row per what, and the key, before building.
- No fan-out on joins, no duplicates or test and staff rows in a headline, no incomplete period in a rate or trend.
- One definition per number: cards and answers compose definitions by id, never re-derive them. Definitional flags are computed in the transform; a metric hides no definitional filter.
- A red test or failing check never goes live; never loosen a test, lower a threshold, widen a cast, or `coalesce` a failure green.
- Update in place, never delete and recreate (ids are referenced); a breaking change is versioned with a migration list.
- Business rules are the user's; conventions are the company's; defaults apply only where nothing exists.
- Structural checks are not correctness: a headline stays Draft until reconciled or accepted by its owner as self-consistent.
- Every stop is an `AskUserQuestion`; a question the user never saw as one was never asked. Nothing is written into the output schema, onto tables or definitions people read, or anywhere people read before a proposal point or approval returns: explore §8, a one-model proposal (build), extract §7, semantic §3, reconcile §3, change §2 or §3.6. Drafts in a Drafts collection are reviewed by the stop that follows them (deliver §6); a request that names its own write (save this question, test this transform, upload this file) is its go-ahead.

## mb conventions

- Every `mb` command takes `--profile "$PROFILE" --json`, placed after the full verb chain; one-line examples omit both, and pipelines spell them out, since a missing `--profile` silently hits the default profile. Parse JSON, never scrape. A list envelope is `{returned, offset, total, has_more, next_offset, data}`: page with `--offset <next_offset>` while `has_more`; narrow with `--fields`.
- Shell state does not survive between Bash calls: start every call that uses `$PROFILE`, `$DB`, `q()`, or `src()` with `source ./.scratch/probe.sh` (`references/profiling.md`).
- Bodies are files in `./.scratch` written with quoted heredocs (`<<'SQL'`) and passed with `--file`; SQL is embedded with `jq --rawfile` so it stays formatted.
- A query that cannot run fails on stderr with empty stdout; one that runs and fails prints `status: "failed"` with exit 0; test `.status == "completed"`. No rows means replan (wrong filter, wrong unit), never an answer of zero.
- Before a verb you have not run: `mb <cmd> --help`, and `mb <cmd> --help --json | jq .inputSchema` before authoring its body. Mechanics live in the CLI's bundled skills: `mb skills path <name> --json | jq -r '.data[0].dir'`, then Read only the section a step names (`mbql` before the first MBQL body; `transform`, `transform-test-plan` (not in every release), `metadata`, `dashboard`, `visualization`, `notification`, `document`, `git-sync` as named; `core` when a footgun bites).
- MBQL bodies are validated locally by `mb query --dry-run` and by every `card`, `measure`, `segment`, and `transform` `create`/`update`. Definition references (`["metric", {}, <id>]`, `measure`, `segment`) carry the numeric id, but the bundled schema expects an `entity_id` string there (`must be string`): fix every other error, then pass `--skip-validate` on bodies with definition references and let the server decide. If the server rejects the number, use `mb card get <id> --fields entity_id`.
- Transforms file only in collections created with `--namespace transforms`; cards, dashboards, and documents in ordinary ones.
- Large lists: narrow with `--fields` and pass `--max-bytes 0`, or page while `has_more`; a truncated list is never a complete answer.
- Links from the profile's `url`: `/question/<id>`, `/metric/<id>`, `/model/<id>`, `/dashboard/<id>`, `/document/<id>`, `/collection/<id>`, `/data-studio/transforms/<id>` (`/inspect` to review), `/data-studio/data/database/<db-id>/schema/<db-id>:<schema>/table/<table-id>`, `/data-studio/schema-viewer?database-id=<db-id>&schema=<schema>`. Every object in a hand-back gets its link.

## Domain notes

A note fires when a table name contains one of its words; say which fired and record it in the state file.

| Note (`references/domains/`) | Fires on |
| --- | --- |
| `subscription-revenue.md` | invoice, subscription, plan, price, charge, membership, dues, pledge, recurring_gift |
| `payments.md` | balance_transaction, payout, dispute, payment_intent, charge, refund, application_fee |
| `commerce-orders.md` | order, fulfillment, fulfilment, refund_line, discount_allocation, shipping_line, tax_line, checkout, shopify |
| `general-ledger.md` | journal, ledger, gl_, accounting, transactionline, transaction_line, trial_balance, subsidiar, chart_of_account, fiscal |
| `sales-pipeline.md` | opportunit, deal, pipeline, lead, stage_history, forecast, quota |
| `product-usage-events.md` | event, activity, usage, login, page_view, pages, tracks, identifies, workspace |
| `event-and-registration-data.md` | registration, registrant, attendee, session, webinar, response, survey |

Retention, cohorts, NRR, GRR, activation: `references/methods/retention-and-cohorts.md`. A note's rules are unreviewed defaults, each a question for the owner; the company's own definitions outrank them. Read a note's section (Questions for the owner, Traps, Invariants, Test cases, For answering) when a playbook step names it.

## Examples are shapes

Every body, name, figure, and date in an example shows a shape. Ids come from the instance in this session, never from an example or memory; `<placeholders>` mark every value to look up; names follow the company's conventions; figures come from queries you ran.
