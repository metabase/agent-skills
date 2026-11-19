#!/usr/bin/env node
// mb_rest.mjs: call one Metabase REST endpoint with the credentials of an existing `mb` CLI profile.
//
// For endpoints the CLI has no verb for (e.g. /api/ee/replacement/*, /api/action/:id, /api/cache, /api/mt/gtap,
// DELETE /api/card/:id). Resolves the profile like `mb` does: <configDir>/profiles.json for the URL
// (configDir = $XDG_CONFIG_HOME/metabase-cli, default ~/.config/metabase-cli; %APPDATA%/metabase-cli on Windows),
// and the secret from the inline copy there if present, else the OS keychain entry service "metabase-cli",
// account "profile:<name>:apiKey" (OAuth: "profile:<name>:oauthAccess"), read through the installed CLI's own
// @napi-rs/keyring module. The secret only ever goes into a request header; it is never printed or logged.
//
// Environment overrides (MB_URL / MB_API_KEY / METABASE_URL / METABASE_API_KEY) silently redirect `mb` itself.
// This helper refuses to run while any of them is set, unless --use-env is passed (then it uses env URL + key only).
//
// Usage:
//   node mb_rest.mjs --profile prod GET "/api/ee/replacement/runs?is-active=true"
//   node mb_rest.mjs --profile prod POST /api/ee/replacement/check-replace-source --body-file check.json   # read-only POST
//   node mb_rest.mjs --profile prod POST /api/ee/replacement/replace-source --body-file swap.json \
//        --allow-write "POST /api/ee/replacement/replace-source"
//   node mb_rest.mjs --profile prod GET /api/ee/replacement/runs --dry-run      # resolves, sends nothing
// Writes need --allow-write "<METHOD> <path>" naming the exact request (pass it only after the user approved that call).
// Every call is appended to --log (default ./.scratch/model-migration/rest-log.jsonl): method, path, status, and for
// writes the request body plus the first 2,000 characters of the response. GET responses are not logged unless
// --log-bodies is passed, since they can carry personal data (emails, user attributes).

import { appendFileSync, mkdirSync, readFileSync, realpathSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

// POST endpoints that only compute and never change server state.
const READ_ONLY_POSTS = new Set(["/api/ee/replacement/check-replace-source"]);
const ENV_VARS = ["MB_URL", "MB_API_KEY", "METABASE_URL", "METABASE_API_KEY"];

function parseArgs(argv) {
  const out = { profile: null, allowWrite: null, dryRun: false, useEnv: false, logBodies: false,
                log: "./.scratch/model-migration/rest-log.jsonl" };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--profile" || a === "-p") out.profile = argv[++i];
    else if (a === "--body-file") out.bodyFile = argv[++i];
    else if (a === "--body") out.body = argv[++i];
    else if (a === "--log") out.log = argv[++i];
    else if (a === "--allow-write") out.allowWrite = argv[++i];
    else if (a === "--dry-run") out.dryRun = true;
    else if (a === "--use-env") out.useEnv = true;
    else if (a === "--log-bodies") out.logBodies = true;
    else rest.push(a);
  }
  [out.method, out.path] = rest;
  if (!out.method || !out.path || !out.path.startsWith("/api/")) {
    throw new Error('usage: mb_rest.mjs --profile P METHOD /api/... [--body JSON | --body-file F] [--allow-write "METHOD /api/..."] [--dry-run] [--use-env] [--log F] [--log-bodies]');
  }
  out.method = out.method.toUpperCase();
  return out;
}

function configDir() {
  if (process.platform === "win32") return join(process.env.APPDATA ?? join(homedir(), "AppData", "Roaming"), "metabase-cli");
  return join(process.env.XDG_CONFIG_HOME ?? join(homedir(), ".config"), "metabase-cli");
}

let keyringModule;
function keyring() {
  if (keyringModule) return keyringModule;
  const bin = realpathSync(execFileSync("sh", ["-c", "command -v mb"]).toString().trim()); // …/@metabase/cli/dist/cli.mjs
  keyringModule = createRequire(join(dirname(dirname(bin)), "package.json"))("@napi-rs/keyring");
  return keyringModule;
}

function readKeychain(account) {
  if (process.env.MB_CLI_DISABLE_KEYRING === "1") return null;
  try {
    return new (keyring().Entry)("metabase-cli", account).getPassword() ?? null;
  } catch {
    return null;
  }
}

function resolve(args, { readSecret }) {
  const setVars = ENV_VARS.filter((v) => process.env[v]);
  if (args.useEnv) {
    const url = process.env.MB_URL ?? process.env.METABASE_URL;
    const key = process.env.MB_API_KEY ?? process.env.METABASE_API_KEY;
    if (!url || !key) throw new Error("--use-env needs both MB_URL and MB_API_KEY (or the METABASE_ variants)");
    return { url, kind: "apiKey", source: "env", header: () => ({ "x-api-key": key }) };
  }
  if (setVars.length) {
    throw new Error(`${setVars.join(", ")} set in the environment: they override --profile for mb and this helper. ` +
                    "Unset them, or pass --use-env to use them deliberately");
  }
  if (!args.profile) throw new Error("pass --profile <name> (see `mb auth list`)");
  const file = JSON.parse(readFileSync(join(configDir(), "profiles.json"), "utf8"));
  const rec = (file.profiles ?? []).find((p) => p.name === args.profile);
  if (!rec) throw new Error(`no mb profile named "${args.profile}" (see \`mb auth list\`)`);
  if (rec.oauth) {
    if (Date.parse(rec.oauth.expiresAt) <= Date.now()) {
      throw new Error(`OAuth token of "${args.profile}" expired: run any networked mb command (e.g. \`mb collection get root --profile ${args.profile} --json\`) to refresh it, then retry`);
    }
    return {
      url: rec.url, kind: "oauth", source: rec.oauth.accessToken ? "inline" : "keychain",
      header: () => {
        const token = readSecret ? (rec.oauth.accessToken ?? readKeychain(`profile:${args.profile}:oauthAccess`)) : null;
        if (!token) throw new Error(`no OAuth access token found for "${args.profile}"`);
        return { authorization: `Bearer ${token}` };
      },
    };
  }
  return {
    url: rec.url, kind: "apiKey", source: rec.apiKey ? "inline" : "keychain",
    header: () => {
      const key = rec.apiKey ?? readKeychain(`profile:${args.profile}:apiKey`);
      if (!key) throw new Error(`no API key found for "${args.profile}"; ask the user to run \`mb auth login --profile ${args.profile}\``);
      return { "x-api-key": key };
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const pathOnly = args.path.split("?")[0];
  const isWrite = args.method !== "GET" && !(args.method === "POST" && READ_ONLY_POSTS.has(pathOnly));
  if (isWrite && args.allowWrite !== `${args.method} ${args.path}`) {
    throw new Error(`${args.method} ${args.path} changes server state. Once the user approved this exact call, ` +
                    `re-run with --allow-write "${args.method} ${args.path}"`);
  }
  const body = args.bodyFile ? readFileSync(args.bodyFile, "utf8") : args.body;
  if (body !== undefined) JSON.parse(body); // fail fast on malformed JSON
  const cred = resolve(args, { readSecret: !args.dryRun });
  const url = new URL(cred.url.replace(/\/+$/, "") + args.path); // keep any subpath of the instance URL
  if (args.dryRun) {
    process.stdout.write(JSON.stringify({ dryRun: true, method: args.method, url: url.toString(), auth: cred.kind,
                                          credentialSource: cred.source, write: isWrite, body: body ? JSON.parse(body) : null }) + "\n");
    return;
  }
  if (isWrite) process.stderr.write(`mb_rest: ${args.method} ${url} (profile ${args.profile ?? "env"}, credentials from ${cred.source})\n`);
  const res = await fetch(url, {
    method: args.method,
    headers: { accept: "application/json", "content-type": "application/json", "user-agent": "mb-rest-helper", ...cred.header() },
    body,
  });
  const text = await res.text();
  try {
    mkdirSync(dirname(args.log), { recursive: true });
    const entry = { at: new Date().toISOString(), profile: args.profile, url: cred.url, method: args.method, path: args.path, status: res.status };
    if (isWrite || args.logBodies) {
      entry.body = body ? JSON.parse(body) : null;
      entry.response = args.logBodies ? text.slice(0, 20000) : text.slice(0, 2000);
    }
    appendFileSync(args.log, JSON.stringify(entry) + "\n");
  } catch { /* logging is best-effort */ }
  let parsed;
  try { parsed = JSON.parse(text); } catch { parsed = text; }
  process.stdout.write(JSON.stringify({ status: res.status, ok: res.ok, body: parsed }) + "\n");
  if (!res.ok) process.exitCode = 1;
}

main().catch((e) => {
  process.stderr.write(`mb_rest: ${e.message}\n`);
  process.exitCode = 2;
});
