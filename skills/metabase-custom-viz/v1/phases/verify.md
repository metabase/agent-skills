# Verify — static review of src/index.tsx

Executor: a subagent, or the main agent when subagents are unavailable.
As a subagent, follow only this file; ignore `SKILL.md`. Paths:
`references/…` are under `<skill-dir>` from the handoff; `<sdk>` is
`node_modules/@metabase/custom-viz/dist`; `<mb>` is
`.claude/metabase-src`.
Input: none; reads `src/index.tsx` and `.claude/build-statement.md`.
Output: a findings report. Read-only: never edit a file.

Read before checking:

- `src/index.tsx`
- `.claude/build-statement.md`
- `references/api-contract.md`
- `references/sandbox-restrictions.md`
- every file in `<mb>/frontend/src/metabase/utils/scripts-sandbox/`
- `<mb>/frontend/src/metabase/ui/colors/types/color-keys.ts` and
  `<mb>/frontend/src/metabase/ui/colors/constants/accents.ts`
- `references/known-mistakes.md`

Read each `<mb>` file above whole with the `Read` tool — never `grep`,
`head`, `sed` or `cat | …`. The blocked lists sit mid-file; a partial
read misses entries.

Checks — run all, collect every finding:

1. Sandbox: every tag, attribute, global listener and API call in
   `src/index.tsx` against the lists `sandbox-restrictions.md` names.
2. Colors: every color name is valid, and none sits under a `Legacy`
   comment or is `@deprecated` (`api-contract.md`, Colors).
3. Known mistakes: every `known-mistakes.md` detector.
4. Statement: the data shape, settings, opt-outs, colors and Notes of
   `.claude/build-statement.md` are what the code does.

Rules:

- A matched detector is a finding. Never argue it away because the code
  "should not hit it"; skip only on an exemption the detector itself
  states.
- Never run the dev server or `npm run build`.

Return: `clean`, or findings, one per line:
`<blocker | warning> · <check> · src/index.tsx:<line> · <what is wrong> · <fix, citing the entry or restriction>`.
Blocker: breaks at runtime or violates a detector or restriction.
Warning: a judgment call.
