#!/usr/bin/env node
// Copies skills/data-apps/master to skills/data-apps/<version> and sets each
// copied skill's `metadata.version` to <version>. Run when Metabase cuts its release-x.<version>.x branch
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA_APPS_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../skills/data-apps",
);
const FRONTMATTER = /^---\n[\s\S]*?\n---\n/;
const MASTER_VERSION = /^([ \t]+version: )master$/gm;

function fail(message) {
  console.error(message);
  process.exit(1);
}

function stampVersion(skillMdPath, version) {
  const content = fs.readFileSync(skillMdPath, "utf8");
  const frontmatter = content.match(FRONTMATTER)?.[0] ?? "";

  // Only the frontmatter is rewritten, and it must name `master` exactly once,
  // so a skill missing the field fails the cut instead of shipping unversioned.
  if ((frontmatter.match(MASTER_VERSION) ?? []).length !== 1) {
    throw new Error(
      `${path.relative(DATA_APPS_DIR, skillMdPath)}: expected one \`version: master\` in its frontmatter metadata`,
    );
  }

  const stamped = frontmatter.replace(MASTER_VERSION, `$1"${version}"`);
  fs.writeFileSync(skillMdPath, stamped + content.slice(frontmatter.length));
}

const version = process.argv[2] ?? "";
if (!/^\d+$/.test(version)) {
  fail("Usage: node scripts/cut-data-app-skills.mjs <major Metabase version, e.g. 65>");
}

const targetDir = path.join(DATA_APPS_DIR, version);
if (fs.existsSync(targetDir)) {
  fail(`skills/data-apps/${version} already exists`);
}

fs.cpSync(path.join(DATA_APPS_DIR, "master"), targetDir, { recursive: true });

try {
  for (const entry of fs.readdirSync(targetDir, { withFileTypes: true })) {
    const skillMdPath = path.join(targetDir, entry.name, "SKILL.md");
    if (entry.isDirectory() && fs.existsSync(skillMdPath)) {
      stampVersion(skillMdPath, version);
    }
  }
} catch (error) {
  fs.rmSync(targetDir, { recursive: true });
  fail(error.message);
}

console.log(`Copied skills/data-apps/master to skills/data-apps/${version}`);
