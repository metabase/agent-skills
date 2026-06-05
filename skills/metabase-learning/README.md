# Claude skill for learning Metabase

This Claude skill is designed to help you learn the ins and outs of Metabase. Claude is able to walk you through the material, quiz you, and keep track of your progress. You can also ask it questions, or tell it what to do (like skip a section you already know).

The main value of an LLM like Claude is that it can ask you questions and then respond to your answer. Claude is very good at being pedantic, so when you give it a vague answer, or one that is partially right and partially wrong, it will tell you which parts you got right and explain what you might have gotten wrong.

The skill runs entirely on Claude, optionally with data pulled from your instance using the Metabase MCP server. Metabase does not receive any information from the skill. When Claude asks you questions about how hard a session felt, etc., that is purely for its own use.

## Installation

It is best to run this skill in *Claude Cowork*. Claude chat can't store your progress between sessions. If you leave the learn session open, that's not an issue of course. If you're planning on breaking the learning up over a longer period of time (or to conserve tokens), Cowork is the better choice.

We have tested the skill with both Sonnet and Opus models and have found that Opus tends to be a better teacher. If you can, use Opus. That said, Sonnet does a good job as well, but is more variable.

This first step applies whether you're using Claude chat or Cowork:

- Install the included skill in the Claude app.
  - In the Claude app, find the **Customize** section.
  - Click on **Skills** in the top left, then click the **+** button and select **Create Skill** > **Upload a skill.**
  - Upload the skill file.

If using Claude Cowork:

- Switch to Claude Cowork
- Open or create a folder that you are comfortable giving Claude permission to access to. (the skill will only store a tiny file recording your progress in a `.claude` subfolder).
- Ask Claude to `Teach me Metabase` or similar, and it will walk you through the rest of the process.

If you have the Metabase MCP server set up, the skill will draw from your own tables for questions and examples. Learn how [to connect the MCP server](https://www.metabase.com/docs/latest/ai/mcp).
