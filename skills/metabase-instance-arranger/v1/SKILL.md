---
name: metabase-instance-arranger
description: >
  Put a Metabase instance into a described state and screenshot it, then keep adjusting on follow-up prompts and reply with a fresh screenshot each time. Uses the `mb` CLI first and falls back to the Metabase docs plus a Playwright-driven browser for anything the CLI can't reach. Use when the user wants Metabase "set up to look like X", a screenshot of a particular screen or state, a demo or docs or marketing scene staged ("a dashboard with three charts and a filter", "the admin permissions page with a Sales group", "dark mode on a question with a pivot table"), or a tweak to a scene already staged ("make the title shorter", "move the filter left", "show it at mobile width"). Not for data-engineering jobs (`metabase-rde`) or a single `mb` command (`metabase-cli`).
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
metadata:
  version: v1
---

# metabase-instance-arranger

You stage a scene in Metabase and show it. Every turn ends with a screenshot, unless the turn is a question to the user.

Paths: `references/…` and `scripts/…` are under `<skill-dir>`, the directory that holds this `SKILL.md`. `./.scratch/arranger/` is the working directory for this job, in the user's current directory.

## Before any work

1. `cat ./.scratch/arranger/STATE.md`. If it exists, this is a follow-up: read it and go to **Follow-ups**. Never ask again for anything it already records.
2. `mb --version`. If it fails, say the Metabase CLI is required and propose `npm i -g @metabase/cli`; run it once the user agrees. Then `mb auth list --json`: one profile → use it; several → ask which instance; none → ask the user to run `mb auth login`.
3. `mb auth status --profile <profile> --json --fields version,lastProbedAt,lastFailure`. The result is `{kind: "release", tag, major, patch}`, or `{kind: "development", tag}` for a dev build. If `lastFailure` is newer than `lastProbedAt`, the instance can't be reached: say so and stop. Record `tag` and `major` in STATE.md; `major` picks which docs to read (`references/cli-vs-ui.md`).
4. Set up the browser once, following `references/screenshots.md`, "Setup". The user then signs in by hand in a browser window the script opens ("Signing in"). The `mb` login doesn't carry over to the browser. Never ask for a password.
5. Create STATE.md using the schema below.

## The loop

1. **Pin down the target.** Rewrite the request as a checklist of things you can see in the screenshot: which page (its URL path), which objects (names, chart types, filters, what the settings say), viewport size, theme, logged-in user. Fill gaps with sensible defaults (Sample Database, 1440×900, light theme, the admin user) and list those defaults in STATE.md. Ask first only when a gap changes what gets built and no default fits. Ask everything in one message.
2. **Plan each item.** Pick the route for each item: `mb` first, docs plus browser only when the CLI can't do it (`references/cli-vs-ui.md`). Write the plan into STATE.md's `Steps` table before running anything.
3. **Apply.** For `mb`: put `--profile <profile> --json` on every command; read bodies from files in `./.scratch/arranger/` with `--file`; run `mb <cmd> --help` before using a verb for the first time, and `mb skills get core` when you need the conventions. For the browser: write one step script per UI change (`references/screenshots.md`, "UI steps"). Write each id you create and each setting you change into STATE.md as soon as you have it.

   **Leave what was already there alone.** By default, change only objects this job created. When the scene needs an existing object changed (a group that was already there, its permissions on a database that was already there, an existing card or setting), first record the current value in STATE.md's `Changed settings`, or save a screenshot of it for UI-only state such as a permissions row. Bulk scripts (every group, every database) must skip cells that existed before, unless the user asked for them. A value you didn't record can't be restored on reset.
4. **Screenshot.** Run `scripts/screenshot.mjs` on the target path (`references/screenshots.md`, "Taking the shot"). Read the PNG you saved.
5. **Check it against the target.** Go through the checklist against the image, not against what you meant to do. Fix any item that doesn't match and take the screenshot again; give up after two retries per item. Anything still wrong goes into the hand-back.
6. **Hand back.** Give the screenshot's absolute path and render the image if the harness can. List what you changed: ids, settings, and which steps used the UI. Name the defaults you chose and anything that doesn't match. End by asking what to adjust.

## Follow-ups

A follow-up changes the scene; it doesn't rebuild it. Find the smallest set of changes that gets there. Use `update` on objects that already exist and never delete and recreate, because ids are referenced by URLs and dashcards. Add the change as new rows in `Steps`, then run loop steps 3–6. Keep every screenshot (`shot-01.png`, `shot-02.png`, …) so the user can compare. If a follow-up asks for a different scene altogether, ask whether to keep the current objects or archive them first.

## Reset

When the user asks to reset or clean up, archive the objects STATE.md lists as `created`, newest first, and set each `changed` setting back to the `previous` value recorded in STATE.md. Never touch objects this job didn't create. Things that can't be archived (users are deactivated, groups and databases are deleted in Admin) are irreversible, so ask before removing them.

## STATE.md schema

```markdown
# Arranger state
profile: <mb profile>      url: <instance url>      version: <tag> (major <n>, or development)
viewport: 1440x900         theme: light             user: <name of the signed-in browser user>

## Target
- [ ] <one thing you can see in the screenshot per line>

## Defaults assumed
- <default> — <why>

## Steps
| # | item | route (mb / ui) | command or step script | result |

## Created
| kind | id | name | url path |

## Changed settings
| key | previous | new |

## Shots
| file | after step | note |
```
