# SDK visualization settings

When to pass `visualization` and `visualizationSettings` is in `semantic-layer.md`, _Render a query_. The installed SDK types decide what's legal. The declaration documents each setting family and key in its JSDoc.

## Look settings up

Search the declaration for what you need instead of reading it whole:

```bash
rg -n "export declare type MetabaseCard|declare interface MetabaseCardBase|declare type .*VisualizationSettings|declare type VisualizationSettings" node_modules/@metabase/embedding-sdk-react/dist/index.d.ts
```

For one setting, search the same file for its key, such as `graph.dimensions`, `pie.dimension`, `sankey.source`, or `boxplot.whisker_type`. With an older SDK package, also check the query-object types:

```bash
rg -n "useMetabaseQueryObject|UseMetabaseQueryObjectResult" node_modules/@metabase/embedding-sdk-react/dist/data-app.d.ts
```

## Setting families

| Type | Visualizations |
| --- | --- |
| `CartesianVisualizationSettings` | bar, line, area, combo, row |
| `ScatterVisualizationSettings` | scatter |
| `WaterfallVisualizationSettings` | waterfall |
| `TableVisualizationSettings` | table, pivot, object detail, list |
| `PieVisualizationSettings` | pie (drawn as a donut) |
| `ScalarVisualizationSettings` | scalar, smartscalar, gauge, progress |
| `FunnelVisualizationSettings` | funnel |
| `SankeyVisualizationSettings` | Sankey |
| `BoxplotVisualizationSettings` | box plot |
| `MapVisualizationSettings` | pin and region maps |

## Keep settings few

- Set only the settings that express the requested change. Let Metabase choose dimensions, metrics, colors, and formatting when the query's shape makes them obvious.
- Settings such as `graph.dimensions`, `graph.metrics`, `pie.dimension`, `pie.metric`, `scalar.field`, `sankey.source`, and `scatter.bubble` take result column names. If you're not sure which names the query produces, leave those keys out and use other presentation settings.
- Keep `column_settings`, `series_settings`, row ordering, and per-slice colors minimal: they depend on exact result keys, and break when the query changes.
- Never invent a setting the installed type doesn't expose. A `custom:*` visualization accepts `Record<string, unknown>` settings, but only when the app has a known contract for it.
