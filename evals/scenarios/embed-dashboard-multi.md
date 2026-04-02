---
skill: metabase-react-sdk-docs
name: Embed multiple dashboards with a shared provider
metabase_version: v1.60.1
---

## User prompt

I need to embed three dashboards in my React app: a sales overview, a user growth chart, and a top products report. The sales one should be interactive so users can filter it. My Metabase is at http://localhost:13000. I'm using API key auth — my key is in `METABASE_API_KEY`.

Assume the following dashboards already exist in Metabase:
- Sales Overview → dashboard ID 12
- User Growth → dashboard ID 15
- Top Products → dashboard ID 23

## Grading criteria

- The agent shows a curl command targeting `/api/session/properties` to detect the Metabase version
- The agent fetches a versioned llms.txt URL containing the detected major version (e.g., `v0.60`)
- The agent generates three separate React components (one per dashboard)
- The agent generates a single shared `MetabaseProvider` (or equivalent) rather than repeating the provider in each component
- The sales overview component uses `InteractiveDashboard` (since filtering is requested)
- The other two components use `StaticDashboard` or `InteractiveDashboard` — not a plain iframe
- All three components import from `@metabase/embedding-sdk-react`
- All `dashboardId` props are passed as integers, not strings
- The agent asks about or infers auth configuration rather than assuming
