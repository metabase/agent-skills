# Skill evals

LLM-graded evals for the agent-skills in this repo. Each eval loads a SKILL.md
as a system prompt, runs a test scenario through Claude, then grades the
response with a second Claude call (LLM-as-judge).

A lightweight mock Metabase HTTP server handles `/api/session/properties` on
`localhost:13000` so evals are deterministic and work without a real instance.

## Setup

```sh
cd evals
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

## Running evals

```sh
# Run all scenarios
python run.py

# Run a specific scenario
python run.py --scenario react-sdk-setup-api-key

# Run all scenarios for one skill
python run.py --skill metabase-react-sdk-setup

# Print the agent's full response for each scenario (useful for debugging)
python run.py --verbose

# Output results as JSON (useful for CI)
python run.py --json
```

## How it works

```
scenarios/*.md          test case: user prompt + grading criteria
        │
        ▼
run.py ──► [mock Metabase server on :13000]
        │
        ├─► Claude (skill agent)
        │     system prompt = SKILL.md content + environment context
        │     user message  = scenario prompt
        │
        └─► Claude (judge)
              evaluates agent response against each grading criterion
              returns pass/fail + reason per criterion
```

## Scenario format

Each `.md` file in `scenarios/` has YAML frontmatter followed by `## Sections`:

```markdown
---
skill: metabase-react-sdk-setup   # must match a directory under skills/
name: Friendly display name
metabase_version: v1.52.3         # reported by the mock server
---

## User prompt
What the user says to the agent.

## Project context
(optional) Existing files / setup the agent should be aware of.

## Grading criteria
- Bullet-point list of expected agent behaviors.
- Each bullet becomes one pass/fail criterion.
- Be specific and observable (did the agent show X command, generate Y component, avoid Z pattern).
```

## Adding a new scenario

1. Create `scenarios/<skill-name>-<short-description>.md` following the format above.
2. Run `python run.py --scenario <your-new-scenario>` to verify it passes.
