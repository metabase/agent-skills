---
skill: metabase-react-sdk-setup
name: JWT setup with a Next.js API route
metabase_version: v1.60.2
---

## User prompt

My Metabase is at http://localhost:13000. I'm building a customer-facing dashboard and need JWT authentication. I'm using Next.js 14 with the App Router.

## Grading criteria

- The agent shows a curl command targeting `/api/session/properties` to detect the Metabase version
- The agent fetches a versioned llms.txt URL containing the detected major version (e.g., `v0.60`)
- The agent guides the user to retrieve the JWT signing secret from the Metabase admin panel
- The agent tells the user to store the secret as a server-side-only environment variable (e.g., `METABASE_JWT_SECRET`)
- The agent scaffolds or describes a Next.js API route (`/api/metabase/auth` or similar) that signs a JWT token
- The agent does not place the JWT secret in a browser-accessible env var (e.g., does not use `NEXT_PUBLIC_` prefix for the secret)
- The agent shows a command to install `@metabase/embedding-sdk-react` at a version compatible with the detected major version
