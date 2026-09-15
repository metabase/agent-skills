# rde (skill)

A router skill for an agent working as a data engineer on the Metabase stack: explore and profile raw data, build clean tables as Metabase transforms, define the semantic layer, build dashboards, answer questions, and reconcile results against a reference. `SKILL.md` loads first and names the one playbook and the few references a job needs.

The skill owns judgment and method, matched to the conventions the company already has; Metabase mechanics come from the CLI's bundled skills, loaded on demand with `mb skills get <name>`.

## Requirements

The `mb` CLI, with an authenticated profile:

```bash
npm i -g @metabase/cli
```

## Install

```bash
npx skills add metabase/agent-skills --skill rde -a claude-code
```

## Playbooks

- `playbooks/explore-raw-data.md`: land data if needed, discover what exists, profile the sources, propose a model inventory.
- `playbooks/build-clean-tables.md`: build the models as transforms, layer by layer, with a data-quality gate after each.
- `playbooks/build-semantic-layer.md`: metadata, models, measures, segments, metrics; described, verified, published.
- `playbooks/build-dashboards.md`: plan the content from the questions; layout and wiring via the bundled skills.
- `playbooks/answer-a-question.md`: from a scoped question to a cross-checked written answer.
- `playbooks/validate-and-reconcile.md`: reconcile a built number against a reference, decompose the gap, leave controls.
- `playbooks/extract-business-logic.md`: turn existing code or documents into a tagged reference and a gap report.

## Files

- `SKILL.md`: the router, read first.
- `playbooks/`: one procedure per job, each ending in a done-when predicate and a reply.
- `references/`: the method the playbooks cite, one owner per rule, plus domain notes.
