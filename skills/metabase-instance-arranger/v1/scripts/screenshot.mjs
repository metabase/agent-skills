// Screenshot a Metabase page once it has finished loading.
// Usage: node screenshot.mjs --path /dashboard/12 --out shot-01.png
//          [--viewport 1440x900] [--full-page] [--fit] [--theme light|dark]
//          [--selector <css>] [--wait <css>]
import { withPage } from "./session.mjs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

// Metabase's loading test id: the default on the shared `Loader`
// (metabase/ui/components/feedback/Loader), and used by DashCardLoadingView,
// DelayedLoading, LoadingAndErrorWrapper and the nav loading view. Metabase's
// own e2e helper `waitForLoaderToBeRemoved` waits on the same id.
const SPINNERS = '[data-testid="loading-indicator"]';

async function settle(page, wait) {
  await page.waitForLoadState("networkidle");
  if (wait) await page.locator(wait).first().waitFor({ state: "visible" });
  await page
    .waitForFunction((sel) => document.querySelectorAll(sel).length === 0, SPINNERS, {
      timeout: 30_000,
    })
    .catch(() => console.warn("warning: loading indicators still present"));
}

// Metabase scrolls dashboards and other long pages inside an inner element,
// so a full-page screenshot only captures the viewport. Grow the viewport
// until no element has hidden overflow left, then the whole page is visible.
async function fitToContent(page) {
  for (let i = 0; i < 3; i++) {
    const hidden = await page.evaluate(() => {
      let extra = 0;
      for (const el of document.querySelectorAll("*")) {
        const oy = getComputedStyle(el).overflowY;
        if ((oy === "auto" || oy === "scroll") && el.clientHeight > 0) {
          extra = Math.max(extra, el.scrollHeight - el.clientHeight);
        }
      }
      return extra;
    });
    if (hidden <= 1) break;
    const { width, height } = page.viewportSize();
    await page.setViewportSize({ width, height: height + hidden });
    await page.waitForTimeout(500); // let the grid relayout
  }
  // Trim the blank band below the content: scrollers keep bottom padding and
  // min-heights, so shrink to the lowest visible leaf element plus a margin.
  const bottom = await page.evaluate(() => {
    let max = 0;
    for (const el of document.querySelectorAll("body *")) {
      if (el.childElementCount > 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) max = Math.max(max, r.bottom);
    }
    return Math.ceil(max);
  });
  const { width, height } = page.viewportSize();
  if (bottom > 0 && bottom + 24 < height) {
    await page.setViewportSize({ width, height: bottom + 24 });
    await page.waitForTimeout(300);
  }
}

/** Wait until the page has settled, then save a screenshot. */
export async function shoot(page, { out, fullPage = false, fit = false, selector, wait, theme } = {}) {
  await settle(page, wait);
  if (fit) {
    await fitToContent(page);
    await settle(page, wait); // cards that just came into view may load now
  }
  if (theme) {
    // Mantine writes the resolved scheme onto <html>.
    const applied = await page.evaluate(() =>
      document.documentElement.getAttribute("data-mantine-color-scheme"),
    );
    if (applied && applied !== theme) {
      const pref = await page.evaluate(() => window.MetabaseUserColorScheme);
      console.warn(
        `warning: page rendered "${applied}", wanted "${theme}"; ` +
          `this user's color-scheme setting is "${pref}" (only "auto" follows --theme)`,
      );
    }
  }
  // Let chart transitions finish.
  await page.waitForTimeout(500);
  if (new URL(page.url()).pathname.startsWith("/auth/login")) {
    throw new Error("Landed on the login page: delete auth.json and run again");
  }
  const path = resolve(out);
  if (selector) await page.locator(selector).first().screenshot({ path });
  else await page.screenshot({ path, fullPage });
  console.log(path);
  return path;
}

function parseArgs(argv) {
  const args = { viewport: "1440x900", theme: "light", fullPage: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--full-page") args.fullPage = true;
    else if (a === "--fit") args.fit = true;
    else if (a.startsWith("--")) args[a.slice(2)] = argv[++i];
  }
  if (!args.path || !args.out) {
    console.error("usage: node screenshot.mjs --path <url path> --out <file.png> [options]");
    process.exit(2);
  }
  const [width, height] = args.viewport.split("x").map(Number);
  return { ...args, viewport: { width, height } };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = parseArgs(process.argv.slice(2));
  await withPage(
    async (page) => {
      await page.goto(args.path);
      await shoot(page, args);
    },
    { viewport: args.viewport, colorScheme: args.theme },
  );
}
