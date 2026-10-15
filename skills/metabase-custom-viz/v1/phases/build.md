# Build — write src/index.tsx

Executor: a subagent, or the main agent when subagents are unavailable.
As a subagent, follow only this file; ignore `SKILL.md`. Paths:
`references/…` are under `<skill-dir>` from the handoff; `<sdk>` is
`node_modules/@metabase/custom-viz/dist`.
Input: none; reads `.claude/build-statement.md`. Output: a working
`src/index.tsx` and a report.

Read before writing:

- `.claude/build-statement.md`
- `references/project.md`
- `<sdk>/types/viz.d.ts`, `<sdk>/types/viz-settings.d.ts`, other
  `<sdk>/types/*.d.ts` as needed
- `references/api-contract.md`
- `references/sandbox-restrictions.md`
- `references/known-mistakes.md` — write code that passes every
  detector

Steps:

1. Write `src/index.tsx`: `checkRenderable` enforcing the data shape
   with user-readable errors; settings via `defineSetting`; the
   `project.md` Defaults on every data mark, minus what the statement
   opted out; everything in Notes.
2. Re-read `src/index.tsx` against every `known-mistakes.md` detector;
   fix what fails.
3. Run Checks (`project.md`).

Rules:

- Edit only `src/index.tsx`.
- No comments that explain a fix or argue the code is correct.
- Never start the dev server.
- A feature needs a blocked capability with no clean substitute → stop
  and return the question, citing the restriction label.
- Use only packages in `package.json`. A library would clearly help →
  return it as an open question (`project.md`, Libraries).

Return: what was built, Checks status, open questions.
