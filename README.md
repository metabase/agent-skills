# agent-skills

A collection of Agent skills for Metabase embedding products. These skills are built for Claude Code but may also work with other AI coding agents (Cursor, Windsurf, etc.). They help perform complex Metabase embedding migrations and upgrades automatically.

> **Important:** Always review and validate the changes made by a skill. Depending on your application's complexity, a skill may not work properly in all cases. Check that your application builds, tests pass, and the embedding works as expected before committing.

## Skills

| Skill                                                                                                                                                                                        | Description                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [metabase-modular-embedding-version-upgrade](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-version-upgrade-skill-md)                                   | Helps upgrade a project's Metabase Modular embedding SDK (`@metabase/embedding-sdk-react`) or Modular embedding (`embed.js`) to a newer version. |
| [metabase-full-app-to-modular-embedding-upgrade](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-full-app-to-modular-embedding-upgrade-skill-md)                           | Helps migrate from Metabase Full App / Interactive (iframe-based) embedding to Modular (web-component-based) embedding.                        |
| [metabase-static-embedding-to-modular-guest-embedding-upgrade](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-static-embedding-to-modular-guest-embedding-upgrade-skill-md) | Helps migrate from Metabase static embedding (signed embed iframes) to guest embeds (web components via `embed.js`).                           |
| [metabase-modular-embedding-to-modular-embedding-sdk-upgrade](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-to-modular-embedding-sdk-upgrade-skill-md) | Helps migrate from Metabase Modular embedding (`embed.js` web components) to the Modular embedding SDK (`@metabase/embedding-sdk-react`).      |

## Installation

Install all skills at once:

```sh
npx skills add metabase/agent-skills
```

Or install a specific skill:

```sh
npx skills add metabase/agent-skills --skill metabase-modular-embedding-version-upgrade -a claude-code
```
