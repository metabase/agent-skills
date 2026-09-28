# Deliver dashboards and documents

Applies when the user wants something to look at or read: a dashboard, document, subscription, or alert. Produces a content plan, cards composed from definitions or labelled Ad hoc, a complete draft reviewed on screen, a plausibility pass, delivery per audience, and the domain Document.

Read first: `references/dashboards.md`; the `dashboard`, `visualization`, `notification`, and `document` skills as steps name them.

Order: 1 orient, 2 content plan, 3 the offer (stop, low readiness only), 4 cards, 5 the page, 6 draft review (stop), 7 plausibility, 8 delivery, 9 final collection (stop), hand-back.

## 1. Orient

The definitions behind the page's numbers and their readiness; pages the audience already uses (`mb search "<topic>" --models dashboard`, `mb dashboard get <id>`), whose conventions you match. When no domain Document exists (`mb search "How to use" --models document`), create it in Drafts with its sections.

## 2. Content plan

Per `references/dashboards.md` (Start from the audience's questions; Card order and composition).

## 3. The offer on a low-readiness scope

When the page's numbers have no definitions (L0–L1), one `AskUserQuestion` with the plan and two options: define the few metrics this page needs first (Recommended; `playbooks/semantic.md`, a transform only where an invariant demands one; this page, later answers, and the next dashboard reuse them), or build now from raw tables, each card's description opening `Ad hoc:` with what is unchecked. One offer per page; a measured invariant problem (duplicates inflating the headline by 12%) is shown in the ask and fixed in the query either way. Pages on existing definitions get no offer.

## 4. Cards

Per `references/dashboards.md` (Card order and composition; What makes a number actionable), each saved with `mb card create` into Drafts; chart settings only when the automatic pick is wrong (`visualization` skill, "Minimum-viable settings per chart family").

## 5. The page

The text card, the `Definitions` card, and the filters per `references/dashboards.md`, laid out on the 24-column grid (`dashboard` skill); the whole page in one `mb dashboard create` into Drafts, every dashcard pointing at a §4 card or a text card (`card_id: null` with `visualization_settings.virtual_card`).

## 6. Draft review

Print the link, the card list, and the omissions, then one `AskUserQuestion` for reactions to the screen, not approval of a list: looks right (Recommended) / change cards / change layout or filters.

## 7. Plausibility pass

Per `references/dashboards.md`. Stale dropdowns: `mb db rescan-values <db-id>`.

## 8. Delivery per audience

Per `references/dashboards.md`, Delivery per audience (`mb subscription create`, `mb document create`, `mb alert create`); `mb alert send <id>` to yourself first; real recipients are a stop.

## 9. Final collection

Moving the page where its audience reads it is a stop with the plausibility result and the destination; on yes, `mb dashboard update <id> --body '{"collection_id":<final-collection-id>}'` (dashcard ids survive, so subscriptions do). The domain Document moves with the first delivered page.

## The domain Document

One per domain, `How to use <domain> numbers`, created in Drafts at the first proposal point with its decisions section, filled out here from the objects, and moved to the domain's business collection with the first delivered page: per final table its one row per what, scope, caveats; definitions with meaning, trust label, owner; decisions open (with defaults) and decided (with who); the dashboards; each headline embedded as its card; how to ask a new question; what to do when a number looks wrong. It carries a receipt at each milestone and session end (what changed, the evidence, what was decided, what is open, what comes next). Its how-to section belongs to readers; update the rest in place (`mb document update`, read-modify-write), never a second document.

## Practice debt

Ad hoc cards and repeated computations are raised only when they matter (the user asks about that number again, edits that page, or it is computed a second way: "this is the third card computing revenue, three ways; define it once?"). At most one suggestion per hand-back; a declined one becomes a decided line, never raised again.

## Done when

Every card traces to a question and composes a definition or is labelled Ad hoc; text card, date filters, and definitions card are on the page; the plausibility pass is clean; every audience has its delivery; the page is in its final collection; the domain Document is current. Hand-back: the cards in reading order by the question each answers, what was left off and why, each KPI's comparison and target, links.
