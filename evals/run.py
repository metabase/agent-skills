#!/usr/bin/env python3
"""
Eval runner for agent-skills.

Loads a SKILL.md as a system prompt, runs a test scenario through Claude,
then grades the response with a second Claude call (LLM-as-judge).

A lightweight mock Metabase HTTP server handles /api/session/properties so
evals work offline and produce deterministic version numbers.

Usage:
  python evals/run.py                                   # run all scenarios
  python evals/run.py --scenario react-sdk-setup-api-key
  python evals/run.py --skill metabase-react-sdk-setup
  python evals/run.py --verbose                         # show agent responses
"""

import argparse
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent
SCENARIOS_DIR = Path(__file__).parent / "scenarios"
MOCK_PORT = 13000

ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


# ---------------------------------------------------------------------------
# Mock Metabase server
# ---------------------------------------------------------------------------

class MockMetabaseHandler(BaseHTTPRequestHandler):
    version_tag = "v1.52.3"

    def do_GET(self):
        if self.path == "/api/session/properties":
            body = json.dumps({
                "tag": self.version_tag,
                "version": {"tag": self.version_tag},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # suppress request logs


def start_mock_server(version_tag: str = "v1.52.3") -> HTTPServer:
    MockMetabaseHandler.version_tag = version_tag
    server = HTTPServer(("localhost", MOCK_PORT), MockMetabaseHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ---------------------------------------------------------------------------
# Scenario parsing
# ---------------------------------------------------------------------------

def parse_scenario(path: Path) -> dict:
    """Parse a scenario .md file with YAML-ish frontmatter into a dict."""
    text = path.read_text()
    lines = text.splitlines()

    meta = {}
    body_start = 0

    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                body_start = i + 1
                break
            if ": " in line:
                key, _, value = line.partition(": ")
                meta[key.strip()] = value.strip()

    body = "\n".join(lines[body_start:])

    # Split body into ## sections
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().lower().replace(" ", "_")
            buf = []
        else:
            buf.append(line)

    if current is not None:
        sections[current] = "\n".join(buf).strip()

    return {**meta, **sections, "_path": str(path), "_stem": path.stem}


def load_skill(skill_name: str) -> str:
    path = ROOT / "skills" / skill_name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text()


# ---------------------------------------------------------------------------
# Skill agent
# ---------------------------------------------------------------------------

AGENT_SYSTEM = """\
You are an AI coding assistant executing a specific skill.

Read the skill instructions below and follow them exactly:

<skill>
{skill_content}
</skill>

Environment context:
- The user's Metabase instance is running at http://localhost:{mock_port}
- Metabase version in that instance: {mb_version}
- The user is working in a Next.js 14 project (React 18)

When you need to run shell commands, show them as bash code blocks.
When you need to create files, show their full content.
Work through the skill steps carefully and thoroughly.
"""


def run_skill_agent(skill_content: str, scenario: dict, client: anthropic.Anthropic) -> str:
    mb_version = scenario.get("metabase_version", "v1.52.3")

    system = AGENT_SYSTEM.format(
        skill_content=skill_content,
        mock_port=MOCK_PORT,
        mb_version=mb_version,
    )

    user_parts = []
    if scenario.get("project_context"):
        user_parts.append(f"**Project context**\n\n{scenario['project_context']}")
    user_parts.append(scenario.get("user_prompt", "").strip())
    user_message = "\n\n---\n\n".join(user_parts)

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# LLM-as-judge
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """\
You are evaluating whether an AI agent correctly executed a skill.

The agent received this user request:
<request>
{user_prompt}
</request>

The agent produced this response:
<response>
{agent_response}
</response>

Evaluate the response against each grading criterion listed below.
For each criterion output a JSON object with exactly these keys:
  "criterion"  – the criterion text (copy it verbatim)
  "pass"       – true or false
  "reason"     – one sentence explaining your judgment

Criteria:
{criteria}

Output ONLY a valid JSON array. No markdown fences, no extra text.
"""


def grade_response(agent_response: str, scenario: dict, client: anthropic.Anthropic) -> list[dict]:
    criteria_raw = scenario.get("grading_criteria", "").strip()

    result = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(
                user_prompt=scenario.get("user_prompt", ""),
                agent_response=agent_response,
                criteria=criteria_raw,
            ),
        }],
    )

    text = result.content[0].text.strip()
    # Strip markdown fences if the model adds them anyway
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenario(path: Path, client: anthropic.Anthropic, verbose: bool = False) -> dict:
    scenario = parse_scenario(path)
    skill_name = scenario.get("skill")
    if not skill_name:
        raise ValueError(f"Missing 'skill:' in frontmatter of {path}")

    skill_content = load_skill(skill_name)
    name = scenario.get("name", path.stem)

    print(f"\n{ANSI_BOLD}▸ {name}{ANSI_RESET}  [{skill_name}]")

    agent_response = run_skill_agent(skill_content, scenario, client)

    if verbose:
        print(f"\n{ANSI_YELLOW}--- agent response ---{ANSI_RESET}")
        print(agent_response)
        print(f"{ANSI_YELLOW}--- end response ---{ANSI_RESET}\n")

    grades = grade_response(agent_response, scenario, client)
    passed = sum(1 for g in grades if g.get("pass"))
    total = len(grades)

    all_pass = passed == total
    status = f"{ANSI_GREEN}✅ {passed}/{total}{ANSI_RESET}" if all_pass else f"{ANSI_RED}❌ {passed}/{total}{ANSI_RESET}"
    print(f"  {status} criteria passed")

    for g in grades:
        icon = f"  {ANSI_GREEN}✓{ANSI_RESET}" if g.get("pass") else f"  {ANSI_RED}✗{ANSI_RESET}"
        print(f"{icon} {g['criterion']}")
        if not g.get("pass"):
            print(f"    {ANSI_YELLOW}→ {g.get('reason', '')}{ANSI_RESET}")

    return {
        "scenario": name,
        "skill": skill_name,
        "passed": passed,
        "total": total,
        "all_pass": all_pass,
        "grades": grades,
    }


def main():
    parser = argparse.ArgumentParser(description="Run agent-skills evals")
    parser.add_argument("--scenario", help="Run a specific scenario by filename stem")
    parser.add_argument("--skill", help="Run all scenarios for a skill")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print agent responses")
    parser.add_argument("--json", action="store_true", help="Output results as JSON (to stdout)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Start mock Metabase server (used by skill version-detection steps)
    start_mock_server()

    # Discover scenarios
    all_paths = sorted(SCENARIOS_DIR.glob("*.md"))
    if args.scenario:
        paths = [p for p in all_paths if args.scenario in p.stem]
    elif args.skill:
        # Filter after parsing to match the 'skill:' frontmatter field
        paths = all_paths
    else:
        paths = all_paths

    if not paths:
        print(f"No scenarios found in {SCENARIOS_DIR}", file=sys.stderr)
        sys.exit(1)

    results = []
    for path in paths:
        try:
            result = run_scenario(path, client, verbose=args.verbose)
            if args.skill and result["skill"] != args.skill:
                continue
            results.append(result)
        except Exception as exc:
            print(f"  {ANSI_RED}ERROR: {exc}{ANSI_RESET}")
            results.append({"scenario": path.stem, "error": str(exc)})

    # Summary
    valid = [r for r in results if "error" not in r]
    fully_passing = sum(1 for r in valid if r.get("all_pass"))

    print(f"\n{'─' * 50}")
    if fully_passing == len(valid):
        print(f"{ANSI_GREEN}{ANSI_BOLD}{fully_passing}/{len(valid)} scenarios fully passing{ANSI_RESET}")
    else:
        print(f"{ANSI_RED}{ANSI_BOLD}{fully_passing}/{len(valid)} scenarios fully passing{ANSI_RESET}")

    if args.json:
        for r in results:
            r.pop("response", None)
        print(json.dumps(results, indent=2))

    sys.exit(0 if fully_passing == len(valid) else 1)


if __name__ == "__main__":
    main()
