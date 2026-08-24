# Claude skill for AI governance on Metabase

This Claude skill is a task-completion coach for rolling out AI analytics without giving up
control: who can use Metabot, what it can see, how much it costs, where the model runs, and
the audit trail. It's the companion to AI Analytics Week Session 2, "AI analytics, on your
terms, on your infrastructure."

It asks what brought you in — a specific concern (a security review, a request to cap spend)
or starting from scratch — and whether you're an admin and what plan you're on, then only
walks through what's actually relevant and accessible to you. It's precise about claims that
matter in a compliance review rather than repeating marketing shorthand: "zero data movement"
only holds in the fully self-hosted case, and it says so rather than overstating it. Like its
sibling skill, it's honest about what it can check for real through the Metabase MCP server —
mostly nothing here, since almost everything in this skill is an admin setting, not a queryable
object — versus what it has to take your word for.

This is the governance/rollout side of AI setup, not the data-modeling side. If your actual
question is "is my data good enough for AI" rather than "who gets to use it and what can they
see," you want [`ai-readiness-checklist`](../ai-readiness-checklist/README.md) instead — this
skill hands off to it when that comes up.

## Installation

- Install the included skill in the Claude app.
  - In the Claude app, find the **Customize** section.
  - Click on **Skills** in the top left, then click the **+** button and select **Create
    Skill** > **Upload a skill.**
  - Upload the skill file.

This skill works in Claude chat, Claude Cowork, or Claude Code. Chat can't save progress
between sessions — fine for a single sitting. If you'd rather progress persisted automatically
across sessions, Cowork can do that; Claude Code works too if you're already comfortable with a
more developer-focused tool.

If you have the Metabase MCP server set up, the skill can run one genuine check: testing
whether Metabot actually can't reach data it shouldn't be able to see, rather than just taking
your permissions setup on faith. Learn how [to connect the MCP
server](https://www.metabase.com/docs/latest/ai/mcp). Everything else in this skill is admin
configuration Claude can't inspect either way, so it's useful with or without MCP connected.
