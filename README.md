# agent-skills

A collection of Agent skills for Metabase embedding products. These skills are built for Claude Code but may also work with other AI coding agents (Cursor, Windsurf, etc.). They help perform complex Metabase embedding migrations and upgrades automatically.

> **Important:** Always review and validate the changes made by a skill. Depending on your application's complexity, a skill may not work properly in all cases. Check that your application builds, tests pass, and the embedding works as expected before committing.

## Skills

| Skill                                                                                                                                                                                       | Description                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| metabase-modular-embedding-version-upgrade · [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-version-upgrade-skill-md) · [skills.sh](https://skills.sh/metabase/agent-skills/metabase-modular-embedding-version-upgrade) | Helps upgrade a project's Modular embedding SDK (`@metabase/embedding-sdk-react`) or Modular embedding (web components via `embed.js`) to a newer version. |
| metabase-full-app-to-modular-embedding-upgrade · [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-full-app-to-modular-embedding-upgrade-skill-md) · [skills.sh](https://skills.sh/metabase/agent-skills/metabase-full-app-to-modular-embedding-upgrade) | Helps migrate from Metabase Full App / Interactive (iframe-based) embedding to Modular embedding (web components via `embed.js`).               |
| metabase-static-embedding-to-guest-embedding-upgrade · [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-static-embedding-to-guest-embedding-upgrade-skill-md) · [skills.sh](https://skills.sh/metabase/agent-skills/metabase-static-embedding-to-guest-embedding-upgrade) | Helps migrate from Metabase Static embedding (signed embed iframes) to Guest embeds (web components via `embed.js`).                           |
| metabase-modular-embedding-to-modular-embedding-sdk-upgrade · [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-to-modular-embedding-sdk-upgrade-skill-md) · [skills.sh](https://skills.sh/metabase/agent-skills/metabase-modular-embedding-to-modular-embedding-sdk-upgrade) | Helps migrate from Metabase Modular embedding (web components via `embed.js`) to the Modular embedding SDK (`@metabase/embedding-sdk-react`).  |
| metabase-embedding-sso-implementation · [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-embedding-sso-implementation-skill-md) · [skills.sh](https://skills.sh/metabase/agent-skills/metabase-embedding-sso-implementation) | Helps implement JWT SSO authentication for Metabase embedding, including the signing endpoint, frontend auth layer, and group mappings.         |

## Installation

Install all skills at once:

```sh
npx skills add metabase/agent-skills -a claude-code
```

Or install a specific skill:

```sh
npx skills add metabase/agent-skills --skill metabase-modular-embedding-version-upgrade -a claude-code
```
