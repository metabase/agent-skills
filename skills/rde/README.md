# rde

A skill for an agent working as the data engineer and analyst of a company whose stack is unknown, with Metabase at the center: explore and profile raw data, build clean tables as Metabase transforms with tests pinning their rules, define the semantic layer (metadata, metrics, measures, segments, the Library), build dashboards and documents, answer questions with checked numbers, reconcile a number against a reference, and change what is delivered safely. `SKILL.md` orients on the instance and routes; each job runs one playbook.

The skill owns judgment and method, matched to the conventions the company already has. Metabase mechanics come from the CLI's bundled skills (`mb skills path <name>`), read one section at a time when a step names one.

## Requirements

The `mb` CLI, 0.3.0 or newer with the `transform-test` command (today only the `alpha-transform-tests` dist-tag ships it), logged in to at least one Metabase, or the rde installer, which installs `mb` and logs it in to a local Metabase:

```bash
npm i -g @metabase/cli@alpha-transform-tests
mb auth login --profile <name> --url <metabase-url>
```

## Install

```bash
npx skills add metabase/agent-skills --skill rde -a claude-code
```

## How it works

- **Which Metabase.** Every session settles one instance before any other call: the one `MB_PROFILE` names, else the one the working file recorded (re-checked with `mb auth list`), else the one the request names, else the installer's local instance, else the only one `mb` is logged in to, else one question, "Which Metabase should I work in?", asked once per directory. Every `mb` command then names that instance explicitly.
- **Credentials stay with the user.** The agent never reads `~/.rde`, never asks for or handles a password or an API key, and never runs `rde credentials` (the user runs it in their own terminal for the UI login). On its own it runs only `rde status --json` and `rde doctor --json`; starting the local instance (`rde start`), repairing its login (`rde init --only api-key`), and any other installer command wait for the user's yes. Other instances are logged in to by the user with `mb auth login`.
- **Orient first.** Before building or changing anything the agent reads where the instance stands: readiness per schema (raw, described, curated, defined with owners, governed), the practice style (Metabase transforms, dbt, models, native SQL), and what already exists. The situation (greenfield, resume, mature) picks the playbook, not the request alone.
- **State lives on the objects.** Grain, scope, required filters, caveats, and owners are written onto the tables, transforms, and definitions themselves, so the next session, Metabot, and people read the same thing. A local `./.scratch/rde-state.md` holds only work in flight (the instance, decisions, and a line per stop answered); when it disagrees with the instance, the instance wins, and the domain Document wins on decisions. `./.scratch` is added to `.git/info/exclude` so it is never committed.
- **Three planned stops.** Intake (who owns the numbers, which questions, is there a reference), the proposal point (the inventory and the decision memo, before anything is written), and go-live approval (tests, checks, and diffs, before a table becomes visible). Every stop is an `AskUserQuestion`; decisions are recorded as keyed lines, open with their default or decided with who.
- **Thin slice first.** One headline number end to end, handed back as Draft, before widening.

## Where the work lands

Production (one instance: built tables stay internal until approved, dashboards in Drafts until reviewed) or staging with remote sync (the deliverable is a job branch for review, never the main branch without confirmation).

## Files

- `SKILL.md`: route, invariants, `mb` conventions, domain-note triggers.
- `playbooks/`: `explore`, `build`, `semantic`, `deliver`, `answer`, `reconcile`, `change`, `extract`, `sync`; each with its commands, steps, and a done-when with the hand-back.
- `references/`: the method the playbooks cite, one owner per rule: `orient`, `collaboration`, `state`, `profiling`, `modeling`, `time-and-entities`, `quality-checks`, `transform-tests`, `semantic-layer`, `dashboards`, `reconciliation`, `extraction`.
- `references/domains/`: subscription revenue, payments, commerce orders, general ledger, sales pipeline, product usage events, event and registration data; each with its metrics, owner questions (default, probe, effect if wrong), traps, invariants, test cases, and answering rules.
- `references/methods/retention-and-cohorts.md`: retention, NRR and GRR, cohort tables, activation.
