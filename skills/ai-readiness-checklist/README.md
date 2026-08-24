# Claude skill for getting your Metabase data AI-ready

This Claude skill is a task-completion coach for the groundwork Metabot and the Metabase MCP
server need to give trustworthy answers: modeling your data, adding context, defining metrics
once, marking what's canonical, verifying a real answer, and turning AI on everywhere. It's
the companion to AI Analytics Week Session 1, "Is your data AI-ready?"

It's a single guided pass, not a course — Claude asks where you're starting (already tried
Metabot and hit a snag? haven't tried anything yet? want the full walkthrough?) and whether
you're an admin and what plan you're on, then only walks you through what's actually relevant
and accessible to you. It's honest about what it can check for real via the Metabase MCP
server versus what it has to take your word for — it won't imply it verified something it
didn't.

## Installation

- Install the included skill in the Claude app.
  - In the Claude app, find the **Customize** section.
  - Click on **Skills** in the top left, then click the **+** button and select **Create
    Skill** > **Upload a skill.**
  - Upload the skill file.

This skill works in Claude chat, Claude Cowork, or Claude Code. Chat can't save progress
between sessions — that's fine for a single sitting, and the skill says so plainly rather than
treating it as broken. If you'd rather progress persisted automatically across sessions,
Cowork can do that; Claude Code works too if you're already comfortable with a more
developer-focused tool.

If you have the Metabase MCP server set up, the skill will run real checks against your own
instance — confirming a query actually works, or that a table/metric is findable by name —
instead of relying entirely on you to self-report. Learn how [to connect the MCP
server](https://www.metabase.com/docs/latest/ai/mcp). It's still useful without it; verification
just becomes fully self-reported.
