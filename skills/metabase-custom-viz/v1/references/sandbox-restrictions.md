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

The exact lists live in `sandbox` of `<sdk>/host-contract.json`, which
matches the installed package. Read the list a section names before
relying on a tag, listener or API. For what to use **instead**, read
`references/sandbox-substitutes.md`.

## Blocked tags

`sandbox.blockedTags`. Rejected by `createElement`/`createElementNS` and
stripped from sanitized HTML; rendering them from JSX throws at runtime.
Among them: `a`, `style`, `link`, `input`, `form`, `iframe`, `video`,
`audio`, and the SVG `use`, `image`, `foreignObject`.

## Allowed tags

Every tag not in `sandbox.blockedTags`. The commonly needed ones are
allowed: `div`, `span`, `button`, `select`, `option`, `label`, `svg`, `g`,
`path`, `rect`, `circle`, `line`, `polyline`, `polygon`, `text`, `tspan`,
`canvas`, `img`.

## HTML string sanitization

`innerHTML`, `outerHTML`, `ShadowRoot.innerHTML`, and `insertAdjacentHTML`
are sanitized with DOMPurify: the blocked tags plus `form`, `a`, `style`,
`frame`, `map`, `area` are stripped, as are the `target`, `formaction` and
`action` attributes; URLs other than `#…`, `/…`, `http(s):` and
`data:image/(png|jpeg|gif|svg+xml|webp)` are removed.

## Blocked attribute assignments

`setAttribute`, `setAttributeNS`, `setAttributeNode(NS)`,
`setNamedItem(NS)`, and the `Attr.value` setter reject:

- any inline event handler attribute (name matching `/^on/i`)
- `javascript:` URLs in the attributes of `sandbox.urlValuedAttributes`

## Blocked global event listeners

`addEventListener` on `document` or `window` throws for the types in
`sandbox.blockedGlobalEventTypes` — keyboard, input, clipboard,
composition and `storage` events.

Assigning the matching `on<type>` handler is blocked too: the
`… set <handler>` labels in `sandbox.blockedApiCalls`. Listening on the
viz's own elements is fine.

## Blocked API calls

`sandbox.blockedApiCalls`. Each entry is exactly the `<label>` that
follows `blocked API call:` in the console. `<handler>` stands for any
`on<type>` from the global event types above; `Navigator.get <key>` is
blocked for every key in `sandbox.blockedNavigatorGetters`.

The groups to expect: network and workers (`window.fetch`,
`window.XMLHttpRequest`, `window.WebSocket`, `window.Worker`,
`FontFace.load`, …), stylesheets (`adoptedStyleSheets`,
`CSSStyleSheet.replace`), document writing and editing, cookies, host
location, storage (`localStorage`, `sessionStorage`, `indexedDB`),
windows and dialogs (`window.open`, `window.alert`, …), navigator,
history, performance, caret, HTML parsing (`DOMParser.parseFromString`, …)
and synthetic clicks and navigation (`HTMLElement.click`,
`HTMLAnchorElement.set href`, …).
