# Debug — fix reported misbehavior

Executor: main agent (needs the user dialog).
Input: the user's symptom. Output: a targeted fix in `src/index.tsx`.

Read: `.claude/build-statement.md`, `references/project.md`,
`references/operations.md`, `references/fix-log-rules.md` (its
rules apply), `.claude/fix-log.md`, `references/known-mistakes.md`,
`references/sandbox-restrictions.md`.

Read on demand: `references/api-contract.md` when the cause
involves host props or `checkRenderable`;
`references/sandbox-substitutes.md` when the fix replaces a
blocked API.

1. Run Checks (`project.md`) once; treat errors as fact.
2. Match the symptom against `known-mistakes.md` symptoms; a host
   console message against the messages in `sandbox-restrictions.md`;
   a Metabase error message against `checkRenderable` and setting
   defaults.
3. Read the relevant code and confirm the cause before editing. No
   cause found in the viz code → do not edit; give the user your
   hypotheses and the reproduction steps you need, and stop.
4. Apply the smallest edit that fixes the cause. Run Checks. Append an entry to
   `.claude/fix-log.md`.
5. Fix alters the data shape, settings, opt-outs or colors → update
   `.claude/build-statement.md`.
6. Dev server Check running; ask the user to confirm the fix after
   hot-reload.

Rules:

- Edit only `src/index.tsx`,
  `.claude/fix-log.md`, `.claude/build-statement.md`.
- Never read or edit files outside the project, Metabase source
  included; host behavior is in `api-contract.md`.
- User edits rules apply.
- Same symptom after two fixes → stop, report what was tried and the
  remaining hypotheses.

Return: cause, change made, whether the user confirmed.
