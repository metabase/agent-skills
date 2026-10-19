# Show Metabase data in a data app

The app reads Metabase through its generated schema, `src/metabase.data.ts`. Each query is a `defineQuery` export in `queries/`, built from the schema's tables, fields, segments, measures, and metrics. `useMetabaseQuery` runs a query for rows your own components render, and `useMetabaseQueryObject` resolves it for a Metabase component to render. Import every helper from `@metabase/embedding-sdk-react/data-app`.

## Rules

These rules add to the ones in `SKILL.md`. The sections after them show how to follow them.

### Sources

- All Metabase context comes from the generated schema file, `src/metabase.data.ts` (or `src/*.metabase.data.ts`): its runtime object, and the `/* metadata: {...} */` comment an entry opens with. Never from Metabase YAML in the repository, MCP tools, or your own API calls.
- Building the UI never creates or changes Metabase content: no new tables, cards, or semantic-layer edits. When the app needs a table, metric, or dimension the schema lacks, stop and tell the user what's missing (_Generate Schema_). Never write a replacement or work around the gap. A table missing from the schema may be unpublished or may not exist, and you don't need to tell which: name what the app needs, and ask the user to publish or create it. Don't look for it through the API, MCP tools, or the database. A missing action is drafted for the user to approve, as in `actions/actions.md`.
- Read data only through `useMetabaseQuery` and `useMetabaseQueryObject`, never through older SDK data hooks.
- Use the generated schema objects, never raw IDs, strings, or lookup helpers: `source: schema.tables.<table>`, its `fields`, `segments`, and `measures`, `schema.metrics.<metric>` in `aggregations`, and the metric's `dimensions`. Give each table a local constant, and pass the schema's table object as `source`: a bare `{ type: "table", id }` runs, but types its rows as empty.
- A metric is an aggregation, never a `source`. Saved questions aren't sources either: the schema has no `schema.questions`, since an app can't copy an existing saved question.
- Never hand-write `DatasetQuery` or MBQL: no `{ type: "query", query: { "source-table": … } }`, no raw `source-table` clauses, and no field, table, or metric IDs passed to a hook or SDK component. Never invent aggregation objects such as `{ name: "count" }` or `{ name: "sum", field }`. Build queries with `filter(...)`, `breakout(...)`, `orderBy(...)`, the `aggregations` helpers, and the generated measures and metrics.
- Prefer the semantic layer to React. A segment, measure, or metric that matches the concept beats rebuilding it from rows with string matching, thresholds, or reconstructed categories. Prefer rich queries (segments, measures, filters, breakouts) to shallow table dumps.

### Queries

- A query's fields, segments, measures, and metrics come from its `source` table. A metric's dimensions reach the source table's own fields and, through a foreign key, a related table's. A query can use them with or without the metric, such as breaking out a `count()` by a related table's name.
- A definition never changes with runtime state. A clause whose value comes from a control goes in the hook's second argument (_Static and dynamic query parts_). Segments and measures work only in the definition.
- A query the user filters (a lookup, a search, a filtered top-N) has no static `limit`, because a static `limit` runs before the dynamic filters. Put its `orderBys` and `limit` in the dynamic part.
- Fixed permission-boundary filters, aggregations, and breakouts stay inside `defineQuery`, baked into its saved question. Never apply them again outside it.
- `filter(...)` takes one value and doesn't fully check value types: `filter(field, "=", [a, b])` compiles, but it isn't an IN filter.
- `contains`, `does-not-contain`, `starts-with`, and `ends-with` match case-sensitively, and `filter(...)` has no option to change that. When a search box feeds one of them, say in the UI that search is case-sensitive, such as in its placeholder. Filter rows in React only when the query returns them all: no `limit`, and a result small enough to load whole.
- Use `fields` only in row-list queries. With `aggregations` and `breakouts`, the breakouts decide the result columns.
- Order with `orderBy(...)`, never `{ field, direction }` literals. To order by a bucketed breakout or an aggregation, pass the same constant to `breakouts` or `aggregations` and to `orderBy`. `orderBy` takes no `unit` or `binning`.
- Write no generics on `defineQuery` or the hooks. Never cast a query to `Parameters<typeof useMetabaseQuery>[0]`, which hides invalid fields, metrics, and breakouts, or to `DefinedQuery`, which hides a query without a saved question.
- Run each query once per render tree. Lift the hook to the highest component that needs the data, and pass `data`, `isLoading`, and `error` down: a second call fires a duplicate request, and the two disagree mid-load. The same query with different filters or breakouts is a different data source. Never call a hook in a loop, a condition, or a callback.
- Render every hook's `error` in its own panel. A query hook's `error` is `unknown`: render `error instanceof Error ? error.message : String(error)`.
- `useMetabaseQuery` returns `isLoading: false` with `data: null` until its first request starts, while the SDK signs in. Treat `data === null` without an `error` as loading, unless you held the query back with `enabled: false`. Show the empty state only when `data.rows` is empty. `useMetabaseQueryObject`'s `isLoading` is already `true` in that window. A query held back with `enabled: false` returns `isLoading: false` from both hooks, with `data` or `query` `null`. Show what the page shows before a choice, such as a prompt to pick an item, never a spinner.

### Rows

- `useMetabaseQuery` rows are objects keyed by result column name, not tuples. Never read `row[0]`, and never silence the type error with `as unknown as [string, number][]`, `DisplayRow`, or another tuple cast. The error is catching a real bug.
- Keys are Metabase column names (`total_amount`, `count`), not schema property names (`totalAmount`). Read `row[ordersTable.fields.orderedAt.name]`, `row.count`, or a named column, never `row.orderedAt`. Index typed rows only with literal keys. A column name taken from `data.columns` at runtime belongs with `rawRows`, by position.
- Before rendering a field, check that the schema emits it and that the query returns it. Never guess a key from the API, from intuition, or from old mock data.
- Values can be null: guard before calling `toFixed`, `toLocaleString`, or string methods.

### Rendering

- Decide per element, never per row or page. A row with one custom tile keeps all its other tiles as SDK components. Matching heights and card chrome come from the container each tile sits in.
- Ask "can Metabase display this at all?", never "which looks closer to the design?" A built-in visualization keeps the instance's theming, accessibility, tooltips, formatting, and drill-through. A chart built in React has none of them, and drifts from every other chart in the app.
  - **Yes:** `useMetabaseQueryObject` with `StaticQuestion` or `InteractiveQuestion`. This covers bar, line, area, combo, row, pie (drawn as a donut), scalar, smartscalar (a number with its trend), gauge, progress, funnel, scatter, waterfall, boxplot, sankey, pivot, map, object and list views, sortable tables, and any other `visualization` the `MetabaseCard` type accepts. It also covers anything where visualization settings carry the presentation (axes, labels, stacking, goals, trend lines, series, formatting), or where users benefit from sorting, column inspection, drill-through, or downloads.
  - **No:** `useMetabaseQuery` and your own component, only when the user asked for a custom visualization or nothing Metabase renders can express it: bespoke scorecards, alert panels, narrative or mixed-content cards, interactions Metabase's chrome can't express, calendar grids, timelines, heat strips, radial views, custom maps, domain-specific diagrams, or one visual unit built from several queries. Keep its row handling typed, and draw with a charting dependency the app already has, or with SVG.
- Styling is never a reason to hand-build. Pass `visualization` for the chart type and `visualizationSettings` for setting-level changes, and theme the SDK for the rest. A pie chart is a Metabase pie chart unless the user asked for a custom one. That's the user's call: don't infer it from a design reference, brand colors, or a screenshot of something bespoke.
- A single-value KPI is a scalar, smartscalar, gauge, or progress visualization. Put whatever Metabase doesn't draw (stars, a caption, a total from a second query) beside it. Hand-build the tile only when the number itself can't come from one query. A number for one selected item, such as one product's average rating, comes from a query filtered to that item in its dynamic part (_Static and dynamic query parts_).
- Give each SDK question a `card` built with `useMemo`: a new `card` object re-runs its query (_Render a query_).
- `StaticQuestion` is the default: it renders the visualization alone. Use `InteractiveQuestion` for an element meant to be explored (drill-through, filtering, chart-type switching, the notebook editor), and pass `isSaveEnabled={false}` unless the app is an editing surface, or viewers get a save-to-collection flow. Its default layout shows the question's title: pass `title={false}` inside a card that already has a heading. Giving `InteractiveQuestion` children replaces that layout, so a composed `<InteractiveQuestion.QuestionVisualization />` shows no toolbar and no Save button.
- Label charts with user-facing names, not opaque IDs such as `franchise_id`. Prefer a related table's name dimension to its foreign key.
- Format values: currency to at most two decimals, counts as whole numbers, dates as readable labels. Render a `null` breakout bucket as "Unknown", or filter it out deliberately, never as the latest point of a time series. A time series needs several ordered buckets, so never fake a sparkline from a scalar or a single point. Series with different units or magnitudes need separate axes or normalization.
- Bound dense results, such as tables, alert lists, logs, and ranked lists, with a top-N slice, grouping, pagination, or a max-height scroll area, so a large result can't stretch the page. Sort and slice rows into a custom ranked list only when it's clearly better than a Metabase row, bar, or table visualization.

### What the numbers mean

- Don't interpret ambiguous business fields such as `margin`, `rate`, `score`, `percent`, `health`, `risk`, or `efficiency`: no `%`, no multiplying by 100, no color-coding, stars, or thresholds, unless the field's `/* metadata */` block states its meaning and scale, or the user asked for it. That block can state them through its `semanticType`, such as `type/Percentage` or `type/Currency`, or its description, such as "Star rating from 1 to 5". Its `unit` key is a date bucket, not a measurement unit. Show the field in an SDK table or chart, leave it out, or ask for curation.
- Make no freshness or operational claims, such as "real-time", "live", "understaffed", or "at risk", that the data or a curated definition doesn't support.
- When no curated schema entry supports a section, leave it out or ask for semantic-layer curation. Never ship placeholder analytics.

### Filters

- Write the page's filter contract before writing a control (_Build the filter bar_).
- A filter in the global bar affects every compatible card, table, KPI, and trend. A filter that can't is section-scoped, visibly, or left out. A KPI and its detail table about the same concept use the same filters, unless the UI says why they differ.
- Show one visible date control per scope. Never put a global date range beside a page-specific date, such as a snapshot date, where one of the two does nothing. A page whose cards use a different date field uses one control for that field.
- Build each card's filters from its own source's fields or compatible metric dimensions. Never reuse a filter array built for another table, and keep one array per queried table when cards use different date fields.
- Every filter defaults to All, or to empty, and runs the unfiltered query. `all`, `""`, `null`, and `undefined` all map to `[]`. A Yes/No/All boolean filter maps both `true` and `false`, and only All maps to no filter.
- Option values come from Metabase at runtime, through an options query in `queries/` with a breakout on the same field or metric dimension the filter applies. A schema field proves only that the field exists, not which values it holds. Hardcode options only for a closed enum the user gave.
- Filter by a stable raw value, such as an id, and show its label. Never filter by display labels when an id exists, and never feed a free-text input straight into an exact-id filter.
- An entity filter, whose value is an id or key while the UI shows a label, is a single searchable combobox, and so is any long runtime option list. It opens its list on click or focus, before any typing. Never use a `<select>` or a search box paired with one, even when today's list is short. A plain `<select>` is only for a short closed enum the user gave.
- All stays selectable while options load, come back empty, or fail. Don't disable the whole control. When the selected value disappears from fresh options, reset the filter to All.
- A date preset bar lists the durations, then All time, then Custom last. Leave Custom out only when the user asked for fixed presets only, or for no range control.
- A custom date range filters only when both ends are set, as `YYYY-MM-DD` strings. A half-picked range means no date filter, never a sentinel date such as `2000-01-01`.
- Pass raw filter state between components and build each query's `filters: [...]` inline with spreads: a shared `ReturnType<typeof filter>[]` array, or one built with `push(...)`, collapses overload inference. The hooks key requests on content, so rebuilding the arrays on each render doesn't refetch.

## Generate Schema

If the schema file exists and covers what the app needs, use it. Otherwise, generate it. It always holds the same content: the published tables of the `Library / Data` tree, the metrics of the `Library / Metrics` tree with the tables they map, and every query action that belongs to no model, under `schema.actions`. Metrics built on a saved question are left out. There is no scope to choose. When the app needs a table the schema lacks, ask the user to publish it to the Data library, or for a metric, to move it into the Metrics library, then regenerate. A missing action is drafted as in `actions/actions.md`, _What's in the schema_.

From the app directory:

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  echo "Not inside the connected git repo — cd into it first." >&2
  exit 1
fi

(
  source "$ROOT/.env.local" 2>/dev/null
  # Fail early (before curl) if either var is missing or placeholder-only.
  if [ -z "$DATA_APP_MB_URL" ] || [ "$DATA_APP_MB_URL" = "mb_replace_me" ] ||
     [ -z "$DATA_APP_MB_API_KEY" ] || [ "$DATA_APP_MB_API_KEY" = "mb_replace_me" ]; then
    echo "Set real DATA_APP_MB_URL / DATA_APP_MB_API_KEY in repo-root .env.local" >&2
    exit 1
  fi
  # -f keeps an error answer, such as a non-admin key's 403, out of the schema file
  curl -fsS \
    -o src/metabase.data.ts.tmp \
    -H "x-api-key: $DATA_APP_MB_API_KEY" \
    -H "Accept: text/typescript" \
    "$DATA_APP_MB_URL/api/apps/generate/schemas" &&
    mv src/metabase.data.ts.tmp src/metabase.data.ts
)
```

An entry with context to give opens with a `/* metadata: {...} */` block of JSON, before its runtime properties: a field's display name, description, and semantic type; a table's database, schema, and real name; a metric's description, filters, and whether it's verified. It's a comment, so it never reaches the bundle. Read it, and never edit or reformat the file.

After the export, check that the schema has every entity the app needs, and tell the user what to publish before building the UI. If the export fails, show the user its error as it is, including the failing ids, names, and message. Don't paraphrase it or retry past it.

## Write every query and action into the app's collection

The app runs every query and action through a copy in its own collection. Read access to that collection lets viewers run the app's cards, but they see data only from tables they can already read: the app grants the collection, not the tables. A production build runs the copies. The dev preview runs the authored tables and actions, so an app works before its copies exist. An inline query, a raw or entity ID, or a hand-built card source defeats that swap, and authored ids bypass the permission boundary.

The CLI finds definitions only in the root-level `queries/` and `actions/` directories, in `.js`, `.jsx`, `.ts`, `.tsx`, `.cjs`, `.cts`, `.mjs`, and `.mts` files. The copies are serialized YAML in the repository, written as a Metabase export writes them:

```
data_apps/<slug>/data_app.yaml                     collection: <entity ID of the app's collection>
collections/data_apps/<collection>.yaml            the app's collection, a root collection of the data-apps namespace
collections/data_apps/<collection>/<name>.yaml     a saved question per query, copies of the metrics they use, and a copy of each action the app runs
```

The collection is named `Data App: <slug>`, and `<collection>` is that name as Metabase slugs it, such as `data_app__sales_ops` for the app `sales-ops`. From the app directory, the folder is `../../collections/data_apps/`. The pull and the CLI find the files by content, not by path: the collection whose `entity_id` the manifest names, and the cards and actions whose `collection_id` is that collection. Nothing changes in Metabase until the repository is pulled.

**`npm run write-resources`** sends the definitions to Metabase, using the credentials in `.env.local`, and regenerates the app's collection folder. It deletes every card and action file of the app's collection, wherever it sits under `collections/data_apps/`, then writes what comes back, printing a `Wrote <path>` line per file:

- a saved question per query, named after the export, with its `savedQuestionEntityId`, holding the query the dev preview runs
- a copy of each action the app runs
- a copy of each metric a query aggregates

It needs no pull first. It refuses a definition without an entity ID, naming it, and drops a metric copy once nothing uses it. Run it after every definition change, and after a source the app uses changes in Metabase. With a non-admin key, it fails with `403`. An item that can't be built or copied (a field that doesn't exist, an action that belongs to a model, a metric or action that reads another card) fails the whole command, and nothing is written or deleted. In either case, stop and tell the user. Never write the files another way.

**`npm run check-resources`** never calls Metabase. It lists every disagreement between the definitions and the collection's files: a manifest that names no collection or one without a file, a definition without its entity ID or naming one no file holds, an invalid or duplicate entity ID, an action definition that names no `schema.actions` entry, a query that names a card that isn't a question, and a question or action no definition names. Then it validates every Metabase YAML file in the repository against the format's schema. `npm run build` runs the first check. Fix what it reports in the definitions or `data_app.yaml`, and run `write-resources` again. Never edit a generated file. The next pull validates everything again. A refused pull fails with `Invalid data app files:` and a line per file: fix the definition or source each line names, run `write-resources`, push, and pull again.

A failure in a file outside `data_apps/<slug>/` and the app's collection isn't the app's to fix: don't edit the file, and tell the user about it. The app's own part of the check is the script's first command, `embedding-sdk-react data-apps check-resources`.

The template's `package.json` wires these: `"write-resources": "embedding-sdk-react data-apps write-resources"`, `"check-resources": "embedding-sdk-react data-apps check-resources && representations validate-schema --folder ../.."` (with `@metabase/representations` as a dev dependency), and `"build": "vite build"`. Add any that an older app lacks.

## Define and run a query

The definition goes in `queries/`, the hook call in a component. The examples from here on leave out `savedQuestionEntityId`, but every real definition carries one.

```ts
// queries/orders.query.ts
import {
  aggregations,
  breakout,
  defineQuery,
  filter,
  orderBy,
} from "@metabase/embedding-sdk-react/data-app";
import schema from "../src/metabase.data";

const ordersTable = schema.tables.orders;
const createdMonth = breakout(ordersTable.fields.createdAt, { unit: "month" });

export const PaidRevenueByMonth = defineQuery({
  savedQuestionEntityId: "<from npx @metabase/representations generate-entity-id>",
  source: ordersTable,
  filters: [
    ordersTable.segments.completed,
    filter(ordersTable.fields.status, "=", "paid"),
  ],
  aggregations: [aggregations.sum(ordersTable.fields.amount)],
  breakouts: [createdMonth],
  orderBys: [orderBy(createdMonth, "desc")],
  limit: 100,
});
```

```tsx
// src/pages/Overview.tsx
import { useMetabaseQuery } from "@metabase/embedding-sdk-react/data-app";
import { PaidRevenueByMonth } from "../../queries/orders.query";

const { data, isLoading, error, refetch } = useMetabaseQuery(PaidRevenueByMonth);
```

The hook infers typed rows from the definition. The schema objects:

- Table: `schema.tables.<table>`, as `source`
- Field, segment, measure: `schema.tables.<table>.fields.<field>`, `.segments.<segment>`, `.measures.<measure>`
- Metric: `schema.metrics.<metric>`, in `aggregations`
- Metric dimension: `schema.metrics.<metric>.dimensions.<group>.<dimension>`

## Static and dynamic query parts

Both query hooks take an optional second argument: the clauses that change while the app runs.

```ts
// queries/revenue.query.ts: static, identical on every render
const orders = schema.tables.orders;

export const RevenueQuery = defineQuery({
  source: orders,
  aggregations: [aggregations.sum(orders.fields.total)],
  breakouts: [
    breakout(orders.fields.createdAt, { unit: "month" }),
    breakout(orders.fields.plan),
  ],
});

// the component supplies only what the UI changes
const { data } = useMetabaseQuery(RevenueQuery, {
  filters: plan === null ? [] : [filter(orders.fields.plan, "=", plan)],
});
```

Split them this way even when nothing seems to depend on it. The first argument is always a `queries/` export, never built at render time. Picking between exports, as in `largeOnly ? LargeOrders : Orders`, is fine. Only the second argument varies with runtime state.

Either part can take `enabled: false` to hold the query back, such as until the user picks a value or a route supplies an id: `useMetabaseQuery(CustomerById, { enabled: id !== null, filters: … })`. A held-back query sends nothing and returns `data: null`.

The dynamic clauses run as their own stage, so they see the **result columns** of the static query, not its source table. That's why `plan` is a breakout above: a control can filter on a source column only if that column survives into the result. If it doesn't, add it as a breakout, or leave the static query unaggregated. In the same way, filter an aggregated static query on `count` or `sum`, not on the fields behind them.

Segments and measures are defined against a table, and the dynamic stage has no table. So `filters: [orders.segments.completed]` and `aggregations: [orders.measures.revenue]` in the second argument are rejected, at compile time and again at runtime. Put the curated definition in the static query, and let the dynamic clause work on what comes out:

```ts
export const CompletedOrders = defineQuery({
  source: orders,
  filters: [orders.segments.completed], // the segment resolves here
  aggregations: [orders.measures.revenue],
  breakouts: [breakout(orders.fields.plan)],
});

const { data } = useMetabaseQuery(CompletedOrders, {
  // a result column, not a segment or measure
  filters: plan === null ? [] : [filter({ type: "column", name: orders.fields.plan.name }, "=", plan)],
});
```

`{ type: "column", name }` names a static result column, typed from that column: an unknown name, or an operator the column's type doesn't take, is a compile error. Use a named breakout's or aggregation's own name. An unnamed field's column carries the database's name for it, so its case depends on the database (`PLAN` on H2, `plan` on Postgres). Write the schema entry's `name`, such as `orders.fields.plan.name`, rather than a literal.

The dynamic part can also aggregate and group the result columns, for example to fold away a breakout added only so a control can filter on it. Fold only additive aggregations, such as sums and counts: a distinct count or an average can't be re-added.

```ts
const { data } = useMetabaseQuery(RevenueByMonthAndCategory, {
  filters: categoryFilters,
  aggregations: [aggregations.sum({ type: "column", name: "revenue" }, { name: "revenue" })],
  breakouts: [{ type: "column", name: "month" }],
  orderBys: [orderBy({ type: "column", name: "month" }, "desc")],
});
```

A control that switches a segment on and off chooses between static queries: define one query per state and pick between them. Each is another saved question in the app's collection. The schema gives a segment's description, not its definition, so never rewrite a segment as a filter of your own. A filter on a result column replaces the per-state queries only when the user states the condition. You can ask, such as whether "In stock" means `in_stock = true`, and then label the control by that condition, not by the segment. A segment can't be negated: for the rows outside it, ask the user for a segment that covers them.

A number for one selected item, such as one product's average rating, needs the item's key in the result, so the dynamic part can filter on it. That puts a key column beside the number. With a curated measure, keep the measure in the static query with a breakout on the key, and filter in the dynamic part. Then point the scalar at the measure's column with `scalar.field`: without it, the scalar shows the first column, which is the key.

```ts
// queries/reviews.query.ts
const productKey = breakout(reviewsTable.fields.productId, { name: "product_id" });
const avgRating = aggregations.measure(reviewsTable.measures.averageRating, { name: "avg_rating" });

export const RatingByProduct = defineQuery({
  source: reviewsTable,
  aggregations: [avgRating],
  breakouts: [productKey],
});

// the component; its memoized card adds visualization: "scalar" and
// visualizationSettings: { "scalar.field": "avg_rating" }
const { query } = useMetabaseQueryObject(RatingByProduct, {
  enabled: productId !== null,
  filters: [filter({ type: "column", name: "product_id" }, "=", productId)],
});
```

Without a measure, leave the static query unaggregated, and filter and aggregate in the dynamic part, which returns the number alone: `{ filters: [filter({ type: "column", name: reviewsTable.fields.productId.name }, "=", productId)], aggregations: [aggregations.avg({ type: "column", name: reviewsTable.fields.rating.name })] }`.

When you memoize the dynamic part instead of writing it at the call, add `as const` to the object: it keeps `aggregations` a non-empty tuple, which `breakouts` require.

## Query recipes

### Tables

```ts
// queries/records.query.ts
const recordsTable = schema.tables.records;
const recordMonth = breakout(recordsTable.fields.createdAt, { unit: "month" });

// a row list
export const RecordStatuses = defineQuery({
  source: recordsTable,
  fields: [recordsTable.fields.id, recordsTable.fields.status],
});

// a grouped summary needs at least one aggregation; segments are filters
export const ActiveAmountByMonth = defineQuery({
  source: recordsTable,
  filters: [
    recordsTable.segments.activeRecords,
    filter(recordsTable.fields.amount, ">", 100),
  ],
  aggregations: [recordsTable.measures.totalAmount],
  breakouts: [recordMonth],
  orderBys: [orderBy(recordMonth, "desc")],
});

// helpers when no curated measure fits
export const AmountByCategory = defineQuery({
  source: recordsTable,
  aggregations: [
    aggregations.count(),
    aggregations.sum(recordsTable.fields.amount),
  ],
  breakouts: [breakout(recordsTable.fields.category)],
});
```

Use a curated segment when it matches the intent exactly. Use `filter(...)` for a threshold, category, date range, text match, boolean, or other narrowing no segment covers.

### Result column names

Each breakout and aggregation needs a distinct result column name, or `npm run write-resources` and the runtime refuse the query with `Breakouts and aggregations need unique column names: …`. By default, a breakout takes its field's name (`CREATED_AT`), and an aggregation its operator's (`sum`, `avg`, and `count` for both `count()` and `distinct(...)`). Name colliding ones with `{ name }`. The name is the row key, and what `orderBy(...)` and the dynamic clauses use. It's not a display label. Never rely on generated names such as `sum_2` or `ID_2`.

| Collision | Fix |
| --- | --- |
| The same helper twice, or `count()` with `distinct(...)` | `aggregations.sum(field, { name })` |
| A measure or metric sharing a name with another aggregation | `aggregations.measure(m, { name })`, `aggregations.metric(m, { name })` |
| One field broken out twice, or same-named fields of two tables | `breakout(field, { unit, name })` |

```ts
const totalAmount = aggregations.sum(recordsTable.fields.amount, { name: "total_amount" });
const totalTax = aggregations.sum(recordsTable.fields.tax, { name: "total_tax" });
const createdMonth = breakout(recordsTable.fields.createdAt, { unit: "month", name: "created_month" });
const createdYear = breakout(recordsTable.fields.createdAt, { unit: "year", name: "created_year" });

export const TaxByPeriod = defineQuery({
  source: recordsTable,
  aggregations: [totalAmount, totalTax],
  breakouts: [createdMonth, createdYear],
  orderBys: [orderBy(createdYear, "desc"), orderBy(totalTax, "desc")],
});
// Rows: { created_month, created_year, total_amount, total_tax }
```

In a query with aggregations, a `{ type: "column", name }` order-by must name one of its breakout or aggregation columns. A `fields` list can't name its columns: two fields with the same name come back as `NAME` and `NAME_2`. Render such a list with an SDK question, whose headers name each field's table, instead of reading its rows. There's no conditional count or ratio: count each subset with its own filtered query, and divide in React.

### Metrics

Pass the table as `source` and the metric in `aggregations`. Filter and break out by the metric's dimensions. Dimensions from the metric's own table work directly. A related table's dimensions, the groups the generated file builds with `pickFields(..., { sourceFieldId })`, work through their foreign key, and they're the only way to reach a related table's fields: a table's `fields` hold only its own columns. A table reached through several foreign keys has one dimension group per key, such as `usersViaCreatedBy` and `usersViaApprovedBy`.

If the metric lacks a dimension the app needs, stop and ask the user to add it on the metric's **Dimensions** tab, under **Available dimensions**, in the group named after the foreign key column, then regenerate the schema. When no metric on the table exists at all, a related table's fields are out of reach in the same way: ask the user for a metric on the table that exposes them. Never assemble a related-table field reference by hand, and never join a second query on the related table in app code instead, whether or not the schema has metrics.

```ts
// queries/revenue.query.ts
const ordersTable = schema.tables.orders;
const revenueMetric = schema.metrics.revenue;
const revenueMonth = breakout(revenueMetric.dimensions.orders.createdAt, { unit: "month" });

export const PaidRevenueByMonthAndFranchise = defineQuery({
  source: ordersTable,
  aggregations: [revenueMetric],
  filters: [filter(revenueMetric.dimensions.orders.status, "=", "paid")],
  // the related table's name, not breakout(revenueMetric.dimensions.orders.franchiseId)
  breakouts: [revenueMonth, breakout(revenueMetric.dimensions.franchises.name)],
  orderBys: [orderBy(revenueMonth, "desc")],
});

// helper aggregations over its dimensions, and the table's segments and measures
export const CompletedRevenueByStatus = defineQuery({
  source: ordersTable,
  filters: [ordersTable.segments.completed],
  aggregations: [
    revenueMetric,
    ordersTable.measures.totalRevenue,
    aggregations.sum(revenueMetric.dimensions.orders.amount),
  ],
  breakouts: [breakout(revenueMetric.dimensions.orders.status)],
});
```

A query can use a metric's dimensions without the metric: a row list's `fields`, or a `count()` broken out by a related table's name.

### Filters, breakouts, and ordering

```ts
filter(ordersTable.fields.quantity, ">", 0);
filter(ordersTable.fields.status, "contains", "paid");
filter(ordersTable.fields.quantity, "between", [10, 20]);
filter(ordersTable.fields.status, "not-empty");

breakout(ordersTable.fields.createdAt, { unit: "month" });
breakout(ordersTable.fields.amount, { binning: { strategy: "num-bins", numBins: 10 } });
breakout(ordersTable.fields.state);
```

| Field type | Operators |
| --- | --- |
| string | `=`, `!=`, `contains`, `does-not-contain`, `starts-with`, `ends-with`, `is-empty`, `not-empty`, `is-null`, `not-null` |
| number | `=`, `!=`, `>`, `>=`, `<`, `<=`, `between`, `is-null`, `not-null` |
| date | `=`, `!=`, `>`, `>=`, `<`, `<=`, `between`, `time-interval`, `is-null`, `not-null` |
| boolean | `=`, `is-null`, `not-null` |

`time-interval` takes `[amount, unit]`, where `[0, "year"]` is the current year. It's relative to when the query runs, so it belongs in the static query: `filter(orders.fields.createdAt, "time-interval", [-24, "month"])`. Only date fields take a `unit`. Other fields break out without one, and numeric fields can take `binning`.

A top-N summary orders by the aggregation, not the source field, through one shared constant:

```ts
// queries/inventory.query.ts
const avgQuantity = aggregations.avg(inventoryTable.fields.quantityOnHand);

export const TopIngredientsByQuantity = defineQuery({
  source: inventoryTable,
  aggregations: [avgQuantity],
  breakouts: [breakout(inventoryTable.fields.ingredient)],
  orderBys: [orderBy(avgQuantity, "desc")],
  limit: 15,
});
```

A sort the user picks is runtime state, so it belongs in the hook's second argument. Map the allowed fields explicitly rather than indexing the whole `fields` object:

```ts
type SortKey = "revenue" | "orders";
type ScorecardField = (typeof scorecardTable)["fields"][keyof (typeof scorecardTable)["fields"]];

const sortFields = {
  revenue: scorecardTable.fields.netRevenue,
  orders: scorecardTable.fields.orders,
} satisfies Record<SortKey, ScorecardField>;

const { data } = useMetabaseQuery(Scorecard, {
  orderBys: [orderBy(sortFields[sortKey], "desc")],
});
```

Here `Scorecard` is the unaggregated `defineQuery({ source: scorecardTable })`, so its source fields survive into the result. To sort an aggregated query by an aggregation the user picks, order by its name, `orderBy({ type: "column", name: sortKey }, "desc")`, with `sortKey` a union of the aggregation names.

## Render a query

For a Metabase component, declare the query in `queries/`, resolve it with `useMetabaseQueryObject`, and pass the `query` it returns in the component's `card` prop. The hook returns `{ query, error, isLoading }`, not rows. Pass only `query`, which may still be `null` while it resolves.

Build the `card` with `useMemo`, keyed on `query`. `StaticQuestion` and `InteractiveQuestion` reload and re-run the question whenever `card` is a new object. So an inline `card={{ query }}` sends the query again on every render of its parent, such as every keystroke in a search box. The hook keeps `query` the same object until the query itself changes.

```tsx
// wrong: the whole hook result, in a new card on every render
const trendQuery = useMetabaseQueryObject(TrendQuery);
<StaticQuestion card={{ query: trendQuery }} />;

// right
const { query } = useMetabaseQueryObject(TrendQuery);
const card = useMemo(() => ({ query }), [query]);
<StaticQuestion card={card} />;
```

Pick the `card` shape:

- `{ query }` when the user named no chart type, and Metabase can infer a sensible display from the query.
- `{ query, visualization }` when the request or design calls for a specific chart type, such as a pie for a distribution.
- `{ query, visualization, visualizationSettings }` only when the user asks for a setting-level change, such as hiding or renaming an axis label, showing values, stacking bars, adding a goal line, ordering table columns, showing pie totals or labels, or controlling series or slice order.

Type a configured card with `satisfies MetabaseCard`. The installed SDK declarations decide what's legal. Search `node_modules/@metabase/embedding-sdk-react/dist/index.d.ts` for `export declare type MetabaseCard`, the relevant `*VisualizationSettings` type, and each setting key, and read their JSDoc. For the chart types, read the `visualization` union of `MetabaseCard`. Never read the whole file, set settings from memory, invent prop names, cast through `any`, or call internal query-resolution helpers. If the SDK says a prop doesn't exist, believe it. `semantic-layer/references/visualization-settings.md` lists the setting families and how to look them up. Sizing a question and theming it are in `setup/setup.md`, _SDK component sizing_ and _Theme rules_.

```tsx
import { StaticQuestion, type MetabaseCard } from "@metabase/embedding-sdk-react";
import { useMetabaseQueryObject } from "@metabase/embedding-sdk-react/data-app";
import { useMemo } from "react";
import { TotalAmountByMonth } from "../../queries/events.query";

function TotalAmountChart() {
  const { query, isLoading, error } = useMetabaseQueryObject(TotalAmountByMonth);

  // above the early returns: a hook can't run conditionally
  const card = useMemo(
    () =>
      ({
        query,
        visualization: "bar",
        visualizationSettings: {
          "graph.show_values": true,
          "graph.y_axis.title_text": "Total amount",
        },
      }) satisfies MetabaseCard,
    [query],
  );

  // PanelError, Spinner and PickPrompt stand for the app's own UI
  if (error) {
    return <PanelError error={error} />;
  }
  if (isLoading) {
    return <Spinner />;
  }
  // only a query held back with `enabled: false` leaves `query` null here:
  // show what the page shows before a choice
  if (!query) {
    return <PickPrompt />;
  }

  return <StaticQuestion card={card} height={360} />;
}
```

For the chart alone, without the toolbar: `<InteractiveQuestion card={card}><InteractiveQuestion.QuestionVisualization height="500px" /></InteractiveQuestion>`.

- A `table` with two breakouts and one aggregation renders as a pivot when one of the breakouts has at most 16 distinct values. Pass `visualizationSettings: { "table.pivot": false }` for one row per group.
- Set a column's header with `column_settings: { '["name","approvers"]': { column_title: "Approvers" } }`, keyed by its result column name.
- A component that wraps `useMetabaseQueryObject` destructures and renders `error`. Reading only `{ query }` makes a failed query look like endless loading. Type its definition prop as `typeof SomeQuery`, or a union for several, never `DefinedQuery`.
- If TypeScript reports duplicate opaque `DatasetQuery` symbols between `useMetabaseQueryObject` and `MetabaseCard`, update the SDK package. Don't cast.

### Rows for your own component

`useMetabaseQuery` returns `data.rows`, keyed by result column name. Map them into an explicit view model before rendering:

```ts
const orderedAtKey = ordersTable.fields.orderedAt.name;

const chartRows = (data?.rows ?? []).map((row) => ({
  label: String(row[orderedAtKey] ?? "Unknown"),
  value: row.count,
}));
```

`data.columns` describes the result. Use it with `rawRows` for a known positional shape, or narrow a key to a literal before indexing `data.rows`. An unnamed aggregation comes back under its operator's name, and a named breakout or aggregation under its name (_Result column names_).

React may group, sort, slice, format, and derive display-only values from the rows.

## Build the filter bar

Filters are ordinary React controls whose state becomes `filter(...)` clauses in the hook's second argument. Before writing one, write the page's filter contract: for each filter, the runtime query that provides its options, the raw value `filter(...)` receives, the cards that accept it (through their own field or metric dimension), and the cards that can't.

| Filter    | Options query                 | Raw value    | Applies to                        | Can't apply to     |
| --------- | ----------------------------- | ------------ | --------------------------------- | ------------------ |
| Franchise | breakout on franchise id/name | franchise id | orders, revenue metric, inventory | none               |
| Plan      | breakout on plan              | plan text    | orders                            | revenue, inventory |

The common date-and-category state:

```tsx
type DatePreset = "30d" | "90d" | "all" | "custom";

const [datePreset, setDatePreset] = useState<DatePreset>("all");
const [customRange, setCustomRange] = useState<[string | null, string | null]>([null, null]);
const [status, setStatus] = useState("all");

const dateRange = useMemo((): readonly [string, string] | null => {
  if (datePreset === "all") {
    return null;
  }
  if (datePreset === "custom") {
    const [start, end] = customRange;
    return start && end ? [start, end] : null;
  }
  return getPresetDateRange(datePreset);
}, [datePreset, customRange]);

const orderFilters = useMemo(
  () => [
    ...(dateRange ? [filter(ordersTable.fields.createdAt, "between", dateRange)] : []),
    ...(status === "all" ? [] : [filter(ordersTable.fields.status, "=", status)]),
  ],
  [dateRange, status],
);
```

`customRange` is exactly what `<DateRangePopover value={customRange} onChange={setCustomRange}>` stores, so nothing needs converting. When you build a control, read `semantic-layer/references/filter-ui-patterns.md` for the options query, the stale-value reset, the searchable combobox, `DateRangePopover`, and the fallback date picker.

## Final checks

- Search the touched files for `useMetabaseQuery(`, `useMetabaseQueryObject(`, and `useAction(`. The first argument must be an identifier imported from `queries/` or `actions/`, or a choice between such identifiers. A `{`, a `defineQuery(`, a `defineAction(`, or a spread there is wrong even when it compiles. The second argument of a query hook is the dynamic object, written at the call or memoized with `as const`.
- Search the touched files for `card={{`. Every SDK question's `card` comes from a `useMemo`.
- Confirm that every definition the app renders sits in `queries/` or `actions/` beside `package.json` and has its entity ID, and that `write-resources`, `check-resources`, and `build` ran after the last change.
- Check that every panel has three states besides its data: a spinner or skeleton until data arrives (for `useMetabaseQuery`, while `data` is `null` without an `error`), its `error`, and an empty state when a query returns no rows.
- Open the preview with every panel mounted, and read the diagnostics feed: in `npm run dev`, a query error is also an `error` entry there.
- Search the touched files for `row[0]`, `row[1]`, `row.orderedAt`, `row.orderDate`, `as unknown as`, `DisplayRow`, `<select`, `type="date"`, `new Date(`, `margin`, `rate`, `score`, `percent`, `%`, `* 100`, and `.toFixed`. Fix positional rows, guessed result keys, entity `<select>` filters, native date inputs in date-range filters, UTC-parsed date labels, and unsupported readings of business fields. An action form's `"Date"` parameter keeps its `type="date"` input (`actions/actions.md`).
- For every visible filter, check that All maps to no filter, that its options come from a runtime query, and that each other option changes every card it claims to affect. Check that every date preset bar ends with Custom, unless the user asked otherwise, that every visible date filter affects the current page, and that no scope has two date filters.