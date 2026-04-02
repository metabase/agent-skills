---
skill: metabase-embed-dashboard
name: Embed a single sales dashboard
metabase_version: v1.52.3
---

## User prompt

Embed a sales overview dashboard in my React app. My Metabase is at http://localhost:13000. I'm using API key auth and my key is already in `NEXT_PUBLIC_METABASE_URL` / `METABASE_API_KEY`.

## Grading criteria

- The agent shows a curl command targeting `/api/session/properties` to detect the Metabase version
- The agent fetches a versioned llms.txt URL containing the detected major version (e.g., `v0.52`)
- The agent uses MCP or describes using MCP tools to search for an existing "sales" dashboard before creating one
- The agent generates a React component named something like `SalesOverviewDashboard`
- The generated component imports from `@metabase/embedding-sdk-react`, not from an internal Metabase path
- The component uses `StaticDashboard` or `InteractiveDashboard`, not a plain iframe
- The `dashboardId` prop in the component is passed as a number (integer), not a string
- The component reads the instance URL and credentials from environment variables, not hardcoded values
