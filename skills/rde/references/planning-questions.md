# Planning questions

Read by `plan-the-build`: how deep a plan goes, who you are talking to, what to ask people to bring, and the entries each situation and domain adds to the plan ([plan-file.md](plan-file.md)), each with the evidence to gather first, its default, who usually answers, and its severity. An entry that a brought file or the profile already settles is listed with its source and ratified at the gate, not asked again.

## Depth and budget

The router decides whether a plan runs (`SKILL.md`, route 9). **Full** when any of these holds: money (billing, payments, a ledger) or a sales pipeline; personal data shown to an audience; embedding for customers; a migration of more than three layers or about twenty models; two sources describing one entity; a named question that needs history ("the plan they were on at the time"). **Light** otherwise. The budget, stated at intake: about five questions for Light, twelve to fifteen for Full; past it, entries stay in the gate's memo with their defaults. Past fifteen, people pick the first option to end the round, and a rushed answer on a High entry is worse than a default named as one.

## Who you are talking to

Infer, never ask: a dbt project, keys, or questions about grain mean a data person; an export, or talk in months and dollars, means finance; plan names and history alone mean a domain expert. It changes vocabulary (dollars and months for finance, columns for a data person), which entries this person is asked (one usually answered by another role is listed for that role unless they say they decide it), and what the plan claims: a domain expert alone yields a partial plan that names the second pass a data person runs. The budget, the order, a proposal with evidence on every question, and the baseline hold for everyone. Procedural entries nobody can answer before a run (a fallback ladder, a tiebreaker order) are decided from the profile, listed, and carry the symptom a wrong default would show in reconciliation.

## What to bring

Asked in the intake message; whatever arrives is read per [extraction-and-gap-report.md](extraction-and-gap-report.md), "Reading what people bring". Arriving with nothing is the same flow with more profiling and more questions.

- Every situation: the export behind any number this must match, at its finest grain (the baseline); definitions documents (Notion, Confluence, Google Docs, through a connector when one is attached, else exported); mapping sheets people maintain (price to plan family, test accounts, exclusions) as CSV, JSON, or a spreadsheet; a previous plan.
- A new source in an existing instance: which existing area the new data should join, in their words.
- A migration: the project (a dbt folder, or `target/manifest.json` with `catalog.json`; LookML files; saved SQL from another tool); which outputs people still use; a sample of those outputs, or the old tables kept live, which is the parity baseline and the source of transform-test cases.

## Universal entries

Each line: entry — evidence first — default — usually answered by — severity.

- What the instance is for (one-off reporting, self-serve analytics, embedded for customers, answers through Metabot) — asked only for a new instance, detected and listed otherwise: `mb setting get` on `enable-embedding-sdk`, `enable-embedding-interactive`, `enable-embedding-static`, `enable-embedding-simple`, the `embedding-app-origins-*` keys, `jwt-enabled`, `saml-enabled` (null means off; `tokenFeatures` in `mb auth list` says what is licensed, not what is used), plus existing dashboards and subscriptions — the reading the settings support — Leadership — High. Embedding for customers adds an entry: the tenant key every table people read carries, with row-level permissions listed for the admin.
- Who reads the numbers and how (SQL, the query builder, dashboards only, customers in an app) — groups and existing content — internal readers on the query builder — Leadership — Medium; it feeds the shape.
- Personal data — columns and rows counted per table, never values — masked, or counts only — Security — High; one checkpoint per job ([collaboration-contract.md](collaboration-contract.md)) that also covers other sensitive fields (salary, health, account numbers). Listed with it, for erasure requests under GDPR and similar laws: history and append tables carry keys and attributes, never personal columns, so an erasure in the source reaches every table on the next full rebuild.
- Source of truth per entity when two systems describe it — the crosswalk probes in [entities-and-time.md](entities-and-time.md) — the system that creates the entity — Data — High.
- History — whether a named question compares periods by an attribute that changes; the history-source hunt in [profiling-catalog.md](profiling-catalog.md) — snapshots start with the first slice, since a day not captured is lost ([entities-and-time.md](entities-and-time.md)) — Data — High; only whether to keep them is asked.
- Test and internal data — identifier domains and outliers — excluded as `dim_exclusion_rule` rows, flagged — Product — Medium.
- Reporting time zone and currency — source values, the basis-and-currency probe — the source's — Finance — Medium.
- The baseline — asked at intake; the validation mode follows from it ([reconciliation.md](reconciliation.md)) and is never asked.

Never asked here, because another rule owns it: the environment (`SKILL.md`), freshness (item 2 of the gate), naming and layer conventions ([layering-and-naming.md](layering-and-naming.md)), the incomplete trailing period (an invariant).

## A new instance with a new database

Nothing to match: rde's naming, layer, and collection defaults are listed as `[DECIDED, reversible]` ([layering-and-naming.md](layering-and-naming.md)); which groups see which collections is listed for the admin, since the CLI sets no permissions; where official numbers live (the Library, or `Definitions`) is listed per [semantic-layer-design.md](semantic-layer-design.md).

## A new source in an existing instance

The instance has transforms, models, or metrics on other databases or schemas, and nothing reads the new one yet.

- How each new table joins what exists — the foreign-key match-rate probe from every candidate column to the existing entity tables — listed when a crosswalk passes 98 percent with no duplicate on the entity side; below that, `no default`, asked with the counts and sample rows — Data — High. Unmatched rows are kept and flagged, never dropped: listed ([entities-and-time.md](entities-and-time.md)).
- Which source wins per attribute of an entity both describe (a customer known to billing and to the product) — attribute agreement on matched rows — the system that creates the entity — Data, Finance for money attributes — High.
- Existing numbers that would move (a revenue metric that would now take in the new source) — the dependents search in [semantic-layer-design.md](semantic-layer-design.md), before and after on three complete periods — existing definitions unchanged, new metrics beside them — the owner named on the metric — High; changing one runs the change flow and is irreversible once published.
- The area's conventions, collections, and groups: found and listed, never asked.

## A migration from another tool

- Translate as it is, or improve while moving — the gap report — as it is first, then improve in a second pass, because parity with the old output is the only reference the build can be checked against — Data — High.
- Scope — dbt `exposures`, the tool's usage data, the dashboards that read each output — the outputs people use; the rest listed and left — Data — Medium.
- Each defect found in the old logic (a filter on a value that no longer occurs, a fan-out) — the finding and the number it moves — kept under as-it-is, fixed under improve — whoever usually answers for that number — High or Medium by what it moves.
- History the old tool captured (dbt `snapshots/`, history tables) — the earliest row per table — `no default`: copied, never recomputed from current state — Data — High.
- Cutover — both run side by side until parity passes; who switches the old pipeline off, and when dashboards repoint — Data — Medium.
- Listed, not asked: dbt data tests (`unique`, `not_null`, `relationships`, `accepted_values`) become the gate's checks ([data-quality-checks.md](data-quality-checks.md)) and dbt unit tests become transform tests ([transform-tests.md](transform-tests.md)); multi-row seeds become reference tables with identifiers kept exactly, single-value seeds `cfg_<domain>` columns; macros and Jinja are inlined; ephemeral models become CTEs; incremental models follow Materialization in [layering-and-naming.md](layering-and-naming.md); LookML derived and persistent derived tables become transforms; LookML measures become measures, and the ones people read as numbers become metrics; explore joins become metadata foreign keys; `access_filter` and user attributes become row-level permissions, listed for the admin.

## Per domain

Entries a fired domain adds; each rule and its default live in the domain file, cited, never restated.

- Subscription revenue ([domains/subscription-revenue.md](domains/subscription-revenue.md)): the recognition basis, list-price or invoice-recognised MRR (Finance, High); the price taxonomy: which prices form a plan family, the main plan of a subscription with add-ons, and the family rank behind upgrades (Finance and Product, High); amortisation of multi-month invoices (Finance, High); coupons, credits, and tax (Finance, High); refunds (Finance, High, `no default`); the stop rule (Finance, High); the customer rollup and the dominant product (Finance, High); plan-shift pairs and the gap threshold (Finance, Medium); test accounts (Product, Medium); currency (Finance, Medium). Listed, and asked only when the readings differ beyond materiality: the line detail source, cadence resolution, true-ups. Every recurrence pair mapping to a named cycle is a check under "How we'll know it's right".
- Event and registration data ([domains/event-and-registration-data.md](domains/event-and-registration-data.md)): which statuses count as registered (Product, High); the completion rule, each path's threshold from its own distribution and how they combine (Product, High); the short-attendance floor (Product, Medium); matching registrants to customers, exact email first and domain only where company-level attribution is accepted (Data, High); the duplicate-customer tiebreaker (Data, Medium).
- Product usage events ([domains/product-usage-events.md](domains/product-usage-events.md)): the activation milestone and window (Product, High); the engagement threshold, N events on M days in a window (Product, Medium); the cohort denominator (Product, Medium); the billing-account to product-account crosswalk (Data, High).
- No domain fired (a sales pipeline, a general ledger): the universal and situation entries only, and the plan says the domain has no note yet.
