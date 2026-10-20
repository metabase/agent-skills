# Iterate — live edits

Executor: main agent (needs the user dialog).
Input: a change request, or none right after build. Output: edited
`src/index.tsx`.

Read: `.claude/build-statement.md`, `references/project.md`,
`references/operations.md`, `references/fix-log-rules.md`
(its rules apply), `.claude/fix-log.md`.

Read on demand, before the edit that needs it:

- edit touches `onClick`, `onHover`, `renderingContext`,
  `checkRenderable` or settings → `references/api-contract.md`
- edit touches the root element, hooks, hover or click handlers, popovers
  or colors → the matching `references/known-mistakes.md` entries
  (Contents at the top)
- the request needs a browser API, tag or global listener →
  `references/sandbox-restrictions.md`, then `references/api-contract.md`
  Metabase ways
- the request names a library, or one would clearly help →
  `references/project.md` Libraries

1. Dev server: Check running (`operations.md`). First time in this
   session → also give the user the Connecting Metabase requirements,
   dev-mode steps and live check.
2. One user request — one focused edit to `src/index.tsx`; saves
   hot-reload.
3. After every edit that changes logic, markup or props (not only
   literal style values): run Checks (`project.md`).
4. Change alters the data shape, settings, opt-outs or colors → update
   `.claude/build-statement.md`.
5. Rename request → Renaming.
6. The user asks for a check, or `src/index.tsx` has changes you did
   not make (`operations.md`, User edits) → return `verify`.

Rules:

- Edit only `src/index.tsx`, `public/assets/icon.svg`,
  `.claude/build-statement.md`, `.claude/fix-log.md`, plus the files
  Renaming lists; `package.json` changes only through a Libraries
  install.
- User edits rules apply.
- Never run `npm run build`.

Return: `misbehavior: <symptom>` when the user reports a bug or quotes an
error — do not fix it here; `verify` per step 6; `done` when the user signals done ("ship
it", "looks good").
