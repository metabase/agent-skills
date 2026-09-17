# rde

A skill for an agent working as a data engineer at a company whose stack is unknown, with Metabase at the center: explore and profile raw data, build clean tables as Metabase transforms with transform tests pinning their rules, define the semantic layer (models, measures, segments, metrics, metadata), build dashboards, answer questions, and reconcile a number against a reference. `SKILL.md` routes; each job runs one playbook, resumable from `./.scratch/STATE.md`.

The skill owns judgment and method, matched to the conventions the company already has. Metabase mechanics come from the CLI's bundled skills, read one section at a time when a step names one.

## Requirements

The `mb` CLI with an authenticated profile:

```bash
npm i -g @metabase/cli
```

## Install

```bash
npx skills add metabase/agent-skills --skill rde -a claude-code
```

## Where the work lands

Two environment modes, detected with `mb git-sync status`: a single production instance, where the build lands directly, hidden until it passes its checks and drafted until reviewed; or a staging instance with remote sync, where the deliverable is an exported branch for review, never the main branch without confirmation.

## Playbooks

- `playbooks/explore-raw-data.md`: land data if needed, discover once, profile what a question touches, propose an inventory, send the decision memo, start the first slice.
- `playbooks/build-clean-tables.md`: build the models as transforms, pin each model's rules with transform tests before it materialises, gate it on the landed data, hide the plumbing, schedule the chain, leave a standing check.
- `playbooks/build-semantic-layer.md`: one starting object per table, measures, metrics, segments, descriptions, verification, the canonical set published.
- `playbooks/build-dashboards.md`: a content plan, a draft reviewed on screen, cards composed from definitions, a plausibility pass, delivery per audience.
- `playbooks/answer-a-question.md`: a scoped, checked answer computed through the definition when one exists.
- `playbooks/validate-and-reconcile.md`: a number proven against a reference, the gap decomposed, controls left running.
- `playbooks/extract-business-logic.md`: existing code or documents turned into a tagged reference and a gap report.

## Files

- `SKILL.md`: the router, read first.
- `playbooks/`: one procedure per job, each with a checklist, exact command bodies, a done-when predicate, and a reply.
- `references/`: the method the playbooks cite, one owner per rule, plus domain notes.
