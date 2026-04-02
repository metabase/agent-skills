---
skill: metabase-react-sdk-docs
name: Embed a single sales dashboard
metabase_version: v1.60.1
---

## User prompt

Embed a sales overview dashboard in my React app. My Metabase is at http://localhost:13000. I'm using JWT SSO auth — the signing endpoint is already set up at `/api/metabase/auth`. The Sales Overview dashboard already exists in Metabase with ID 7.

## Grading criteria

- The agent shows a curl command targeting `/api/session/properties` to detect the Metabase version
- The agent fetches a versioned llms.txt URL containing the detected major version (e.g., `v0.60`)
- The agent acknowledges the provided dashboard ID (7) and does not attempt to create a new dashboard from scratch
- The agent generates a React component named something like `SalesOverviewDashboard`
- The generated component imports from `@metabase/embedding-sdk-react`, not from an internal Metabase path
- The component uses `StaticDashboard` or `InteractiveDashboard`, not a plain iframe
- The `dashboardId` prop in the component is passed as a number (integer), not a string
- The component reads the instance URL and credentials from environment variables, not hardcoded values
- The agent does not suggest or use API key authentication
