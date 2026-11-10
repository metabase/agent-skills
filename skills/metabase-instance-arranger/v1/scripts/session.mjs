// Shared Playwright session for metabase-instance-arranger.
//
// The person signs in once, by hand, in a visible browser window
// (password or SSO); the session cookie is saved to ./auth-<host>.json next
// to this file (one per instance) and reused headless until it expires. No credentials pass
// through the agent or any file other than that cookie.
//
//   MB_URL=https://… node session.mjs --login     # open a window, wait for sign-in
//
// Step scripts and screenshot.mjs import withPage(); it throws
// NeedsLoginError when there is no valid saved session.
import { chromium } from "playwright";
import { existsSync, unlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const LOGIN_TIMEOUT_MS = 5 * 60_000;

export class NeedsLoginError extends Error {
  constructor() {
    super(
      "No valid Metabase session. Run `node session.mjs --login` and sign in " +
        "in the browser window that opens.",
    );
    this.name = "NeedsLoginError";
  }
}

function baseURL() {
  const v = process.env.MB_URL;
  if (!v) throw new Error("MB_URL is not set");
  return v.replace(/\/+$/, "");
}

// One saved session per instance, so switching instances keeps both sign-ins.
function storagePath() {
  const host = new URL(baseURL()).host.replace(/[^a-zA-Z0-9.-]/g, "_");
  return join(here, `auth-${host}.json`);
}

async function signedIn(context, url) {
  const res = await context.request.get(`${url}/api/user/current`);
  return res.ok();
}

/** Open a visible window and wait until the person has signed in. */
export async function login() {
  const url = baseURL();
  const browser = await chromium.launch({ headless: false });
  try {
    const context = await browser.newContext({ viewport: null });
    const page = await context.newPage();
    await page.goto(url);
    console.log(`Sign in to ${url} in the browser window (waiting up to 5 minutes)…`);
    const deadline = Date.now() + LOGIN_TIMEOUT_MS;
    while (Date.now() < deadline) {
      if (await signedIn(context, url)) {
        await context.storageState({ path: storagePath() });
        console.log(`Signed in. Session saved to ${storagePath()}`);
        return;
      }
      await page.waitForTimeout(2000);
    }
    throw new Error("Timed out waiting for sign-in");
  } finally {
    await browser.close();
  }
}

/**
 * Open an authenticated headless page and run fn(page, context).
 * opts: { viewport: {width, height}, colorScheme: "light" | "dark" }
 */
export async function withPage(fn, opts = {}) {
  const url = baseURL();
  const STORAGE = storagePath();
  if (!existsSync(STORAGE)) throw new NeedsLoginError();
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({
      baseURL: url,
      viewport: opts.viewport ?? { width: 1440, height: 900 },
      colorScheme: opts.colorScheme ?? "light",
      deviceScaleFactor: 2,
      storageState: STORAGE,
    });
    if (!(await signedIn(context, url))) {
      unlinkSync(STORAGE);
      throw new NeedsLoginError();
    }
    const page = await context.newPage();
    return await fn(page, context);
  } finally {
    await browser.close();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (process.argv.includes("--login")) {
    await login();
  } else {
    console.error("usage: MB_URL=… node session.mjs --login");
    process.exit(2);
  }
}
