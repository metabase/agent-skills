# Reading Fetched Docs

After `scripts/fetch-docs.sh` fetches all available doc pages and snippets, here's how to read them effectively.

## Snippet files

The script automatically fetches snippet files referenced via `{% include_file %}` directives. These are saved as `{prefix}-snippet-{Name}.md`.

Each snippet file contains a prop table between marker comments:
```
<!-- [<snippet properties>] -->
(prop table here)
<!-- [<endsnippet properties>] -->
```

Include snippet content verbatim in the analysis — do not summarize away props. Step 3 needs the complete list to cross-reference against project usage.

For older versions where snippets don't exist, props are documented inline in the doc pages themselves (look for `## ... props` headings and the tables/lists that follow).

## Theme/CSS changes

When the project uses appearance or theme customizations, check the fetched docs for:

- `theme` prop structure changes (prop names, nesting, value types)
- CSS custom property renames/removals (variables like `--mb-*`)
- Theme configuration moves (e.g., from `MetabaseProvider` props to a separate config object)

These changes are documented in the appearance/config doc pages and the changelog.
