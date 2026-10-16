# Sandbox restrictions

Custom visualizations run inside a `@locker/near-membrane-dom` sandbox.
Everything below fails **at runtime**, not at compile time — TypeScript
will not catch any of it. When code hits a restriction, the host console
shows one of:

- `[plugin <id>] blocked API call: <label>`
- `[plugin <id>] blocked createElement: <tag>`
- `[plugin <id>] blocked setAttribute for inline event handler: <name>`
- `[plugin <id>] blocked setAttribute with javascript: URL: <name>`
- `[plugin <id>] blocked addEventListener for global event type: <type>`
- `[plugin <id>] DOMPurify stripped content from <source>: […]` (a log, not
  an exception — content silently disappears)

The lists live in the sandbox source, `<mb>/frontend/src/metabase/utils/scripts-sandbox/` (`<mb>`: `.claude/metabase-src`). This file says how each list applies and where it is; read
the list itself before relying on a tag, listener, attribute or API. For
the Metabase way to do what a blocked API would, read `api-contract.md`,
Metabase ways.

## The host page is invisible

The viz mounts inside a subtree marked `data-plugin-sandbox="<pluginId>"`;
DOM nodes outside it come back as detached decoys (`document.body`,
sibling dashcards, tree walkers and MutationObservers rooted at
`document`). Only query and observe inside your own mount.
`document.activeElement` returns `null` while focus is on host UI.

## Tags

`BLOCKED_TAGS` in `<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions-dom-mutate.ts` are rejected by `createElement`/`createElementNS`;
rendering one from JSX throws at runtime. Every other tag is allowed.

## HTML string sanitization

`innerHTML`, `outerHTML`, `ShadowRoot.innerHTML`, and `insertAdjacentHTML`
are sanitized with DOMPurify. It applies `PURIFY_CONFIG` in
`<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions-dom-mutate.ts`: strips its
forbidden tags and attributes and removes URLs that don't match its
allowed URL pattern.

## Attribute assignments

`setAttribute`, `setAttributeNS`, `setAttributeNode(NS)`,
`setNamedItem(NS)`, and the `Attr.value` setter reject:

- any inline event handler attribute (name matching `/^on/i`)
- `javascript:` URLs in the attributes of `URL_VALUED_ATTRS` in
  `<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions-dom-mutate.ts`

## Global event listeners

`addEventListener` on `document` or `window` throws for the types in
`GLOBAL_BLOCKED_EVENT_TYPES` in `<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions-event.ts`.
Assigning the matching `on<type>` handler is blocked too. Listening on the viz's own elements is fine.

## API calls

`<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions-blocked-apis.ts` registers every
blocked API with the `<label>` that follows `blocked API call:` in the
console, including `NAVIGATOR_BLOCKED_GETTERS`;
`<mb>/frontend/src/metabase/utils/scripts-sandbox/distortions.ts` blocks host storage.
