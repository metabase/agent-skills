#!/usr/bin/env bun
/**
 * Eval runner for agent-skills.
 *
 * Loads a SKILL.md as a system prompt, runs a test scenario through Claude,
 * then grades the response with a second Claude call (LLM-as-judge).
 *
 * A lightweight mock Metabase HTTP server handles /api/session/properties so
 * evals work offline and produce deterministic version numbers.
 *
 * Usage:
 *   bun run.ts                                    # run all scenarios
 *   bun run.ts --scenario react-sdk-setup-api-key
 *   bun run.ts --skill metabase-react-sdk-setup
 *   bun run.ts --verbose                          # show agent responses
 *   bun run.ts --json                             # output results as JSON
 */

import Anthropic from "@anthropic-ai/sdk";
import { parseArgs } from "util";
import { readdirSync, readFileSync, existsSync } from "fs";
import { join, basename } from "path";

const ROOT = join(import.meta.dir, "..");
const SCENARIOS_DIR = join(import.meta.dir, "scenarios");
const MOCK_PORT = 13000;

const G = "\x1b[32m";   // green
const R = "\x1b[31m";   // red
const Y = "\x1b[33m";   // yellow
const B = "\x1b[1m";    // bold
const X = "\x1b[0m";    // reset

// ---------------------------------------------------------------------------
// Mock Metabase server
// ---------------------------------------------------------------------------

function startMockServer(versionTag: string): void {
  Bun.serve({
    port: MOCK_PORT,
    fetch(req) {
      const path = new URL(req.url).pathname;
      if (path === "/api/session/properties") {
        return Response.json({ tag: versionTag, version: { tag: versionTag } });
      }
      return new Response("Not Found", { status: 404 });
    },
  });
}

// ---------------------------------------------------------------------------
// Scenario parsing
// ---------------------------------------------------------------------------

interface Scenario {
  skill: string;
  name: string;
  metabase_version: string;
  user_prompt: string;
  project_context?: string;
  grading_criteria: string;
  _stem: string;
}

function parseScenario(path: string): Scenario {
  const lines = readFileSync(path, "utf-8").split("\n");
  const meta: Record<string, string> = {};
  let bodyStart = 0;

  if (lines[0]?.trim() === "---") {
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === "---") { bodyStart = i + 1; break; }
      const sep = lines[i].indexOf(": ");
      if (sep !== -1) meta[lines[i].slice(0, sep).trim()] = lines[i].slice(sep + 2).trim();
    }
  }

  const sections: Record<string, string> = {};
  let current: string | null = null;
  const buf: string[] = [];

  for (const line of lines.slice(bodyStart)) {
    if (line.startsWith("## ")) {
      if (current !== null) sections[current] = buf.join("\n").trim();
      current = line.slice(3).trim().toLowerCase().replace(/ /g, "_");
      buf.length = 0;
    } else {
      buf.push(line);
    }
  }
  if (current !== null) sections[current] = buf.join("\n").trim();

  return {
    ...meta,
    ...sections,
    _stem: basename(path, ".md"),
  } as unknown as Scenario;
}

function loadSkill(skillName: string): string {
  const path = join(ROOT, "skills", skillName, "SKILL.md");
  if (!existsSync(path)) throw new Error(`Skill not found: ${path}`);
  return readFileSync(path, "utf-8");
}

// ---------------------------------------------------------------------------
// Skill agent
// ---------------------------------------------------------------------------

const AGENT_SYSTEM = `\
You are an AI coding assistant executing a specific skill in a simulated environment.

Read the skill instructions below and follow them exactly:

<skill>
{skill_content}
</skill>

Environment:
- Metabase instance: http://localhost:{mock_port}
- User project: Next.js 14 (React 18), no Metabase packages installed yet

Simulated command outputs (use these when the skill instructs you to run commands):
- \`curl -s http://localhost:{mock_port}/api/session/properties | grep -o '"tag":"[^"]*"'\`
  → output: "tag":"{mb_version}"
- \`curl -s https://www.metabase.com/docs/v0.{mb_major}/llms.txt\`
  → output: [versioned Metabase Embedding SDK documentation for v0.{mb_major}]

Instructions for this evaluation:
1. Show each command as a bash code block, then show its simulated output.
2. Proceed through ALL skill steps in this single response — do not stop and ask the user to run commands before continuing.
3. Complete every step the skill describes, including generating any code or files.`;

async function runSkillAgent(
  skillContent: string,
  scenario: Scenario,
  client: Anthropic,
): Promise<string> {
  const mbVersion = scenario.metabase_version ?? "v1.60.1";
  const mbMajor = mbVersion.replace(/^v\d+\./, "").split(".")[0];

  const system = AGENT_SYSTEM
    .replaceAll("{skill_content}", skillContent)
    .replaceAll("{mock_port}", String(MOCK_PORT))
    .replaceAll("{mb_version}", mbVersion)
    .replaceAll("{mb_major}", mbMajor);

  const userParts: string[] = [];
  if (scenario.project_context) userParts.push(`**Project context**\n\n${scenario.project_context}`);
  userParts.push(scenario.user_prompt.trim());

  const msg = await client.messages.create({
    model: "claude-opus-4-5",
    max_tokens: 4096,
    system,
    messages: [{ role: "user", content: userParts.join("\n\n---\n\n") }],
  });
  return (msg.content[0] as { text: string }).text;
}

// ---------------------------------------------------------------------------
// LLM-as-judge
// ---------------------------------------------------------------------------

const JUDGE_PROMPT = `\
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

Output ONLY a valid JSON array. No markdown fences, no extra text.`;

interface Grade {
  criterion: string;
  pass: boolean;
  reason: string;
}

async function gradeResponse(
  agentResponse: string,
  scenario: Scenario,
  client: Anthropic,
): Promise<Grade[]> {
  const msg = await client.messages.create({
    model: "claude-opus-4-5",
    max_tokens: 2048,
    messages: [{
      role: "user",
      content: JUDGE_PROMPT
        .replace("{user_prompt}", scenario.user_prompt)
        .replace("{agent_response}", agentResponse)
        .replace("{criteria}", scenario.grading_criteria),
    }],
  });

  let text = (msg.content[0] as { text: string }).text.trim();
  text = text.replace(/^```[a-z]*\n?/, "").replace(/\n?```$/, "");
  return JSON.parse(text) as Grade[];
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

interface ScenarioResult {
  scenario: string;
  skill: string;
  passed: number;
  total: number;
  allPass: boolean;
  grades: Grade[];
  error?: string;
}

async function runScenario(
  path: string,
  client: Anthropic,
  verbose: boolean,
): Promise<ScenarioResult> {
  const scenario = parseScenario(path);
  if (!scenario.skill) throw new Error(`Missing 'skill:' in frontmatter of ${path}`);

  const skillContent = loadSkill(scenario.skill);
  const name = scenario.name ?? scenario._stem;

  console.log(`\n${B}▸ ${name}${X}  [${scenario.skill}]`);

  const agentResponse = await runSkillAgent(skillContent, scenario, client);

  if (verbose) {
    console.log(`\n${Y}--- agent response ---${X}`);
    console.log(agentResponse);
    console.log(`${Y}--- end response ---${X}\n`);
  }

  const grades = await gradeResponse(agentResponse, scenario, client);
  const passed = grades.filter(g => g.pass).length;
  const total = grades.length;
  const allPass = passed === total;

  const status = allPass
    ? `${G}✅ ${passed}/${total}${X}`
    : `${R}❌ ${passed}/${total}${X}`;
  console.log(`  ${status} criteria passed`);

  for (const g of grades) {
    const icon = g.pass ? `  ${G}✓${X}` : `  ${R}✗${X}`;
    console.log(`${icon} ${g.criterion}`);
    if (!g.pass) console.log(`    ${Y}→ ${g.reason}${X}`);
  }

  return { scenario: name, skill: scenario.skill, passed, total, allPass, grades };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const { values: args } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    scenario: { type: "string" },
    skill:    { type: "string" },
    verbose:  { type: "boolean", short: "v", default: false },
    json:     { type: "boolean", default: false },
  },
});

const apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) { console.error("Error: ANTHROPIC_API_KEY is not set"); process.exit(1); }

const client = new Anthropic({ apiKey });

// Start mock server using the first scenario's version (or default)
startMockServer("v1.60.1");

// Discover scenario files
let scenarioPaths = readdirSync(SCENARIOS_DIR)
  .filter(f => f.endsWith(".md"))
  .sort()
  .map(f => join(SCENARIOS_DIR, f));

if (args.scenario) scenarioPaths = scenarioPaths.filter(p => basename(p).includes(args.scenario!));

if (scenarioPaths.length === 0) {
  console.error(`No scenarios found in ${SCENARIOS_DIR}`);
  process.exit(1);
}

const results: ScenarioResult[] = [];

for (const path of scenarioPaths) {
  try {
    const result = await runScenario(path, client, args.verbose ?? false);
    if (args.skill && result.skill !== args.skill) continue;
    results.push(result);
  } catch (err) {
    console.error(`  ${R}ERROR: ${err}${X}`);
    results.push({ scenario: basename(path, ".md"), skill: "", passed: 0, total: 0, allPass: false, grades: [], error: String(err) });
  }
}

const valid = results.filter(r => !r.error);
const fullyPassing = valid.filter(r => r.allPass).length;

console.log(`\n${"─".repeat(50)}`);
const summaryColor = fullyPassing === valid.length ? G : R;
console.log(`${summaryColor}${B}${fullyPassing}/${valid.length} scenarios fully passing${X}`);

if (args.json) console.log(JSON.stringify(results, null, 2));

process.exit(fullyPassing === valid.length ? 0 : 1);
