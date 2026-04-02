---
skill: metabase-react-sdk-setup
name: API key setup in a Next.js project
metabase_version: v1.60.1
---

## User prompt

My Metabase instance is at http://localhost:13000. I'd like to add embedded analytics to my Next.js 14 app. Let's use API key auth for now.

## Grading criteria

- The agent shows a curl command targeting `/api/session/properties` to detect the Metabase version
- The agent fetches a versioned llms.txt URL that contains the detected major version number (e.g., `v0.60`)
- The agent guides the user to create an API key via the Metabase admin UI or the `/api/api-key` endpoint
- The agent instructs the user to store the key in an environment variable (e.g., `METABASE_API_KEY` in `.env.local`)
- The agent shows a command to install `@metabase/embedding-sdk-react` at a version compatible with the detected major version
- The agent does not generate any React component code (embedding components are out of scope for setup)
- The agent does not hardcode any API key value in code examples
