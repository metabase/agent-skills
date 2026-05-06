# Agent skills for Metabase

A collection of agent skills for working with your Metabase. These skills are built for Claude Code but may also work with other AI coding agents (Cursor, Windsurf, etc.). They help perform complex Metabase embedding migrations and upgrades, explore data models, and create Metabase content automatically.

## Installation

Install all skills at once:

```sh
npx skills add metabase/agent-skills -a claude-code
```

Or install a specific skill:

```sh
npx skills add metabase/agent-skills --skill metabase-modular-embedding-version-upgrade -a claude-code
```

## Skills

Always review and validate the changes made by a skill. Depending on your application's complexity, a skill may not work properly in all cases. Check that your application builds, tests pass, and the embedding works as expected before committing.

### CLI

[metabase-cli](./skills/metabase-cli/SKILL.md)

Drives a Metabase instance from the terminal via the official `metabase` CLI: authenticate with profiles, list/get/create/update/delete cards, dashboards, transforms, databases, settings, run queries, search content, sync content to and from a remote git repo, manage Enterprise workspaces, translate entity ids. Bundles workspace lifecycle and transform authoring as on-demand reference files.

### Database metadata

[metabase-database-metadata](./skills/metabase-database-metadata/SKILL.md)

Retrieves and caches database metadata (databases, tables, fields, field values) from a Metabase instance for understanding the data model.

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-database-metadata-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-database-metadata)

### Embedding SSO implementation

[metabase-embedding-sso-implementation](./skills/metabase-embedding-sso-implementation/SKILL.md)

Helps implement JWT SSO authentication for Metabase embedding, including the signing endpoint, frontend auth layer, and group mappings.

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-embedding-sso-implementation-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-embedding-sso-implementation)

### Full app to modular embedding upgrade

[metabase-full-app-to-modular-embedding-upgrade](./skills/metabase-full-app-to-modular-embedding-upgrade/SKILL.md)

Helps migrate from Metabase Full App / Interactive (iframe-based) embedding to Modular embedding (web components via `embed.js`).

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-full-app-to-modular-embedding-upgrade-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-full-app-to-modular-embedding-upgrade)

### Modular embedding to modular embedding SDK upgrade

[metabase-modular-embedding-to-modular-embedding-sdk-upgrade](./skills/metabase-modular-embedding-to-modular-embedding-sdk-upgrade/SKILL.md)

Helps migrate from Metabase Modular embedding (web components via `embed.js`) to the Modular embedding SDK (`@metabase/embedding-sdk-react`).

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-to-modular-embedding-sdk-upgrade-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-modular-embedding-to-modular-embedding-sdk-upgrade)

### Modular embedding version upgrade

[metabase-modular-embedding-version-upgrade](./skills/metabase-modular-embedding-version-upgrade/SKILL.md)

Helps upgrade a project's Modular embedding SDK (`@metabase/embedding-sdk-react`) or Modular embedding (web components via `embed.js`) to a newer version.

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-modular-embedding-version-upgrade-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-modular-embedding-version-upgrade)

### Representation format

[metabase-representation-format](./skills/metabase-representation-format/SKILL.md)

Understands the Metabase Representation Format — a YAML-based serialization format for Metabase content (collections, cards, dashboards, documents, segments, measures, snippets, transforms).

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-representation-format-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-representation-format)

### Static embedding to guest embedding upgrade

[metabase-static-embedding-to-guest-embedding-upgrade](./skills/metabase-static-embedding-to-guest-embedding-upgrade/SKILL.md)

Helps migrate from Metabase Static embedding (signed embed iframes) to Guest embeds (web components via `embed.js`).

Marketplace links: [skillsmp.com](https://skillsmp.com/skills/metabase-agent-skills-skills-metabase-static-embedding-to-guest-embedding-upgrade-skill-md) | [skills.sh](https://skills.sh/metabase/agent-skills/metabase-static-embedding-to-guest-embedding-upgrade)
