# Recovery

When something is not right: find the cause in one read-only pass, explain it plainly, fix what you may, and hand the rest to the user as an exact command. Never guess, never run a failing command a third time, and never touch credentials (`references/collaboration.md`, Files and credentials).

## When it loads

Before anything else, when:

- the user asks why something does not work, which Metabase is in use, or where something went;
- the user says numbers or objects are missing or in the wrong place, or that they cannot log in;
- `mb` fails with an authentication, connection, unknown-command, or unknown-flag error;
- the host in a link you are about to hand back differs from the state file's `url`;
- a search for something you created in this session finds nothing;
- the same command has failed twice.

Stop the work in hand; the playbook resumes at its step once the cause is fixed or handed over.

## 1. The pass

One Bash call, read-only, and nothing said to the user until it is done:

```bash
echo "## mb"; mb --version 2>&1; for m in $(which -a mb); do echo "$m: $("$m" --version 2>&1 | head -1)"; done
echo "## logins"; mb auth list --json --max-bytes 0 --fields profile,url,status 2>&1
echo "## environment"; for v in MB_PROFILE MB_URL; do printenv "$v" >/dev/null && echo "$v=$(printenv "$v")"; done; printenv MB_API_KEY >/dev/null && echo "MB_API_KEY is set"
echo "## installer"; if command -v rde >/dev/null; then rde status --json 2>&1; rde doctor --json 2>&1 | jq -c '.checks[] | select(.status != "skipped") | {id, status, detail, hint, fix}'; else echo "not installed"; fi
echo "## state"; cat ./.scratch/rde-state.md 2>/dev/null || echo "no state file"
```

It shows every `mb` on PATH in order with its version (the first one runs); every Metabase `mb` is logged in to, with its `status` (only `ok` answers and authenticates; `auth-failed` is a login problem; `network-error` and `server-error` mean the Metabase is not answering); whether `MB_PROFILE`, `MB_URL`, or `MB_API_KEY` is set (never print the key's value); the installer's instance and its doctor rows; and the state file's header (instance, `chosen`, format), `## Build`, and `## Recovery`.

Add from this session's own transcript: the `--profile` every `mb` call actually carried, and the hosts in links already handed back. A call without `--profile` went to `MB_PROFILE`'s Metabase or to `default`'s; any call made while `MB_URL` or `MB_API_KEY` was set went to that URL or used that key, whatever `--profile` said (`mb` takes a flag first, then the environment, then the stored login).

Doctor rows (`rde doctor --json`) each carry `id`, `status` (`ok`, `failed`, `skipped`), `detail`, `hint`, and `fix`. A failed row's `hint` names the repair in the installer's words; `fix` names what the installer can re-run, or is null when a person must act. Today's installer has rows such as `mb`, `health`, `api-key`, `mb-profile`, and `skill` (or `skill.<agent>`); newer ones add rows for every `mb` on PATH, the environment overrides, the other Metabases, and every copy of the skill. Use those rows when present and the rest of the pass when not. A command a hint names is a proposal under the login rules; never run `rde doctor --fix`.

## 2. Explain

One short message after the pass, in plain words:

- which Metabases this machine knows, by host, and which of them answer;
- which one this work used, and why, from `chosen` in words ("you set it in your shell", "you named it", "it is your local Metabase", "it is the only one that answers", "you picked it", "an earlier session recorded it");
- what is wrong, and what happens next.

For example: "Your `mb` is 0.2.1 from Homebrew, found before the 0.3.1 the installer set up, so transform tests are not available." A Metabase is its host or "your local Metabase"; never say "profile". When the pass finds nothing wrong, say what was checked and what was found.

## 3. Causes and fixes

Fixes follow `SKILL.md`, Which Metabase (login rules): unasked, the agent runs only the pass; every other fix it runs needs the user's yes through `AskUserQuestion`; the rest are handed over as the exact command for the user's own terminal. Headless: write the needed fix on the state file's `next:` line and stop.

| Cause | Confirm from the pass | Fix, and who runs it |
| --- | --- | --- |
| Work went to the wrong Metabase | A call carried another `--profile` or none, `MB_URL` was set, or a link's host differs from the state file's `url`; `mb <kind> get <id> --profile <profile> --json` on each host shows where an object is (search can lag behind a write) | One `AskUserQuestion`, "Which Metabase should this work be in?", hosts as options. Update `profile`, `url`, and `chosen: asked` in the state file. List what this session created on the wrong one, and any edit it made to existing objects there, from `## Build` and the hand-backs, each with its link. Offering to remove it is a stop; on yes, `mb <kind> archive <id>` (card, dashboard, document, collection, measure, segment) and `mb transform delete <id>` (after `mb transform delete-table <id>` when its table goes too), each with the wrong one's `--profile` |
| An old or shadowed `mb` | More than one `mb` on PATH with different versions, the first older than 0.3.0 or without `transform-test`; the doctor's `mb` row | Show both paths and versions. Propose the doctor's hint, or `npm i -g @metabase/cli@alpha-transform-tests` plus removing the old one with the package manager that owns its path; run on yes. The user edits PATH or shell files, never the agent; a new terminal and a restarted agent session pick up the change |
| The installer's instance is stopped | `rde status --json` `health` is not `healthy`; the doctor's `health` row | Propose `rde start`; run on yes |
| Its login fails | The instance is healthy, and its entry is missing or not `ok`; the doctor's `api-key` or `mb-profile` row | Propose `rde init --only api-key`; run on yes |
| Another Metabase's login fails | Its entry is `auth-failed` | The user runs `mb auth login --profile <name> --url <url>` in their own terminal; re-check with `mb auth list --json` when they say it is done |
| `MB_PROFILE` points elsewhere | It names a Metabase other than the state file's, or than the one the user means | Say which host it points at. Offer to work in that one, or ask the user to unset it in their own terminal (and in their shell file if they export it there) and restart the agent session |
| `MB_URL` or `MB_API_KEY` is set | Either line in the environment section | Every `mb` call goes to that URL or uses that key, whatever `--profile` says. Ask the user to unset them in their own terminal and restart the agent session |
| A stale or duplicate copy of this skill | The doctor's skill rows; without them, `npx -y skills@latest list --json` and `npx -y skills@latest list -g --json` list more than one `rde`, or one whose `source` is not the installer's | Propose `rde init --only agents-skills`; run on yes, then the user restarts the agent session. Without the installer, name each copy by path and ask which to keep |
| The state file's Metabase no longer answers | Its entry is `network-error` or `server-error`, or gone | Say so plainly. Re-run `SKILL.md`, Which Metabase, and switch only with the user's yes |
| Anything the pass cannot explain | | Say what was checked and what was found, and ask the user one `AskUserQuestion` |

## 4. Record the fix

Every cause found gets one line under the state file's `## Recovery` section (`references/state.md`), written when the fix is done or handed over, so the next session does not rediscover it:

```
<yyyy-mm-dd> [<cause>]: <what was wrong>; <what was done, or the command handed over>; by <agent | user | pending (user)>
```

A resumed session reads `## Recovery` first; a `pending (user)` line is re-checked with the pass, and rewritten once the fix has landed.
