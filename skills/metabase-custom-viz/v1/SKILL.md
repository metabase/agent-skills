---
name: metabase-custom-viz
description: Build, change, debug, and package Metabase custom visualizations — React plugins made with `@metabase/custom-viz` and uploaded to Metabase as a `.tgz`. Use when the user asks to create a custom visualization or chart type for Metabase, scaffold one with `npx @metabase/custom-viz init`, change its look, settings, drills or tooltips, fix it when it renders wrong or the host console shows `blocked API call` or `blocked createElement`, connect it to a local Metabase, or package it for upload.
metadata:
  version: v1
  sdk: "@metabase/custom-viz ^2"
---

# Metabase custom visualizations

You orchestrate. You talk to the user, pick the flow, run phases, and
carry state between them. You do not write viz code outside a phase.

Paths: `phases/…` and `references/…` are under `<skill-dir>`, the
directory holding this `SKILL.md`. `<sdk>` is
`node_modules/@metabase/custom-viz/dist` in the project. Other paths are
relative to the project root. Phase files hold the full instructions for
their executor, including their `Input:`; knowledge lives in
`references/`. Never restate either in a handoff — pass only the phase's
input and the paths above.

## Setup

1. Project: the working directory has `metabase-plugin.json` and
   `@metabase/custom-viz` in `package.json` → use it. Otherwise take a
   name from the request (ask only if there is none), run
   `npx @metabase/custom-viz@latest init <name>`, and work in `<name>/`.
2. `node_modules/` missing → `npm install`.
3. `<version>` is `version` in
   `node_modules/@metabase/custom-viz/package.json`. Its major is not 2 →
   tell the user this skill targets `@metabase/custom-viz` 2.x and stop.
4. Metabase source: the host rules (sandbox, colors, column types) live
   in the public Metabase repo. `<ref>` is `custom-viz-v<version>`, the
   tag the installed SDK was released from. Download each file
   below, keeping its path and overwriting an older copy, with `curl`
   (never a web fetch tool: it summarizes); a file missing at `<ref>`
   comes from `master`:
   `curl -fsSL --create-dirs -o .claude/metabase-src/<path> https://raw.githubusercontent.com/metabase/metabase/<ref>/<path> || curl -fsSL --create-dirs -o .claude/metabase-src/<path> https://raw.githubusercontent.com/metabase/metabase/master/<path>`
   - `frontend/src/metabase/utils/scripts-sandbox/distortions-dom-mutate.ts`
   - `frontend/src/metabase/utils/scripts-sandbox/distortions-event.ts`
   - `frontend/src/metabase/utils/scripts-sandbox/distortions-blocked-apis.ts`
   - `frontend/src/metabase/utils/scripts-sandbox/distortions.ts`
   - `frontend/src/metabase/ui/colors/types/color-keys.ts`
   - `frontend/src/metabase/ui/colors/constants/accents.ts`
   - `frontend/src/metabase-lib/v1/types/utils/isa.ts`

   `<mb>` is `.claude/metabase-src`. Add `.claude/metabase-src/` to the
   project `.gitignore` when the line is missing. Now read the four `scripts-sandbox`
   files, `color-keys.ts` and `accents.ts`, each whole with the `Read`
   tool — never `grep`, `head`, `sed` or `cat | …`. The blocked lists sit
   mid-file; a partial read misses entries and the viz breaks at runtime.
   `isa.ts` on demand.

Then read `references/project.md` and `references/operations.md`.

## Phases

- `phases/refine.md` — you
- `phases/build.md` — a subagent: spawn it with the `Agent` tool and tell
  it to read and follow that file. Never write `src/index.tsx` yourself:
  build needs a fresh context holding only the build statement and its
  references.
- `phases/iterate.md` — you
- `phases/debug.md` — you
- `phases/ship.md` — you

When executing a phase yourself, follow that file only; skip reading
files whose content is still in your context. Only when the `Agent` tool
is unavailable, run build yourself.

## References

- `project.md` — files, build statement format, libraries, defaults, checks
- `api-contract.md` — host behavior the types cannot express
- `known-mistakes.md` — bugs with symptoms, fixes, detectors
- `sandbox-restrictions.md` — what the sandbox blocks at runtime
- `operations.md` — dev server, connecting Metabase, reading a question,
  renaming, user edits
- `fix-log-rules.md` — format and rules of `.claude/fix-log.md`

## State

- `.claude/build-statement.md` — the build statement; written by refine,
  kept current by iterate and debug. Missing while `src/index.tsx` is
  already a viz → reconstruct it from the code in the `project.md`
  format, confirm with the user, write it.

## Start

Route:

- `src/index.tsx` is still the scaffold's thumbs-up/down template (no
  viz built yet) and the user wants a viz → **Create**
- Change, new setting, restyle, rename → iterate
- Misbehavior report → debug
- "ship it", "package it", "build the archive" → **Ship**
- Question about the viz, the API or the setup → answer from the
  references and the code; no phase

## Create

refine → build → iterate. Build returns open questions → ask the user,
fold the answers into `.claude/build-statement.md`, re-run build.

## Ship

Run Checks (`project.md`). Failures → fix them first (debug). Then run
ship.

## Phase exits

- iterate returns `misbehavior` → debug; `done` → **Ship**
- debug returns → iterate
