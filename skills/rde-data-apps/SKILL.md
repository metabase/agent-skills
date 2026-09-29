---
name: rde-data-apps
description: >
  Build or change a Metabase data app on an rde machine: settles what the `metabase-data-app-*` skills need from the local setup (the remote-sync repository, the Metabase URL, the API key rde stores, how the app reaches Metabase) and hands the build to them. Use only when an app is asked for explicitly: "build me an app for X", "create a data app", "make an internal tool / portal in Metabase", "add a page / a form / a filter to my data app". A dashboard, a question, or a metric is not an app; those stay with the `rde` skill.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite
---

# rde-data-apps

A data app is a React bundle Metabase serves at `/apps/<slug>` from `data_apps/<slug>/` in the repository connected through remote sync. The `metabase-data-app-*` skills build it. This skill answers their questions from what rde already knows, so the user is asked only what rde cannot know, then hands over.

## 1. The instance

`rde status --json`: `url` is the instance (not a secret) and `version` must be v65+ or a head build. `mb auth list --json` names the profile whose `url` matches; use it as `$PROFILE`. Metabase serves apps only under a license with remote sync and data apps: `rde doctor --json`, row `license`. Without one, the user activates it in their own terminal with `rde init --only license` (or `! rde init --only license` in this session); the token never enters the chat.

## 2. The repository

`contentRepository` in `rde status --json` is the working directory of the remote-sync repository, and the answer to `metabase-data-app-setup`'s Step 1: name it and use it, do not ask. When it is null and the license has remote sync, ask where the repository should live, then run `rde init --only git-sync --git-dir <path> --git-remote local` (a bare remote inside `~/.rde`, no account). A hosted remote needs a git token, so the user runs `rde init --only git-sync` themselves. A repository rde creates already ignores `.env.local`, `node_modules/`, and the rest a data app must not push.

## 3. The credentials

The data-app skills read `DATA_APP_MB_URL` and `DATA_APP_MB_API_KEY` from `.env.local` at the repository root and forbid the key in the conversation. rde stores the API key `mb` uses, and `rde credentials --api-key` prints it alone. When the setup skill reaches its credentials step, or its check prints `MISSING`, fill the file with this command instead of asking the user, `<url>` from step 1 and `<repo>` from step 2. It prints only `creds written`, keeps the file's other lines, and makes sure `.env.local` is ignored:

```bash
ROOT="$(git -C "<repo>" rev-parse --show-toplevel)" && KEY="$(rde credentials --api-key)" &&
{ grep -qxF .env.local "$ROOT/.gitignore" 2>/dev/null || echo .env.local >> "$ROOT/.gitignore"; } &&
{ if [ -f "$ROOT/.env.local" ]; then grep -v -e '^DATA_APP_MB_URL=' -e '^DATA_APP_MB_API_KEY=' "$ROOT/.env.local"; fi
  printf 'DATA_APP_MB_URL=%s\nDATA_APP_MB_API_KEY=%s\n' "<url>" "$KEY"; } > "$ROOT/.env.local.tmp" &&
mv "$ROOT/.env.local.tmp" "$ROOT/.env.local" && chmod 600 "$ROOT/.env.local" && echo "creds written"
```

Never run `rde credentials --api-key` where its output comes back to you, and never print `.env.local`. The key belongs to rde's admin, so the dev preview sees every table; say so when the app is meant for a narrower audience.

## 4. Hand off

One skill per step; follow it for the app's code:

| The step | Skill |
| --- | --- |
| No app yet: create, scaffold, set up | `metabase-data-app-setup` |
| The app reads Metabase tables, metrics, measures, or segments (the generated `metabase.data.ts`) | `metabase-data-app-semantic-layer` |
| More than one page | `metabase-data-app-routing` |
| A write: a form, an update, a delete, a saved action | `metabase-data-app-actions` |

## 5. The data behind it

The app reads what the semantic layer publishes. A number it shows with no metric or measure behind it yet goes back to the `rde` skill first (its semantic-layer playbook, clean tables before that when the source is raw), so the app queries the definition by id and never re-derives it in `queries/`. When the `rde` skill keeps `./.scratch/STATE.md`, record the app's slug and the ids it reads there.

## 6. Delivery

The setup skill ends with a commit and a push. With rde's local remote the push lands in the bare repository inside `~/.rde`; `mb --profile $PROFILE git-sync import --json` then brings the app into Metabase (check `mb git-sync is-dirty` first; mechanics: `mb skills path git-sync`), and the app opens at `<url>/apps/<slug>`. When the instance is a staging one whose changes reach production through review, push to a job branch instead and hand the branch back.
