# Claude skill for learning Metabase

This Claude skill is designed to help you learn the ins and outs of Metabase. Claude walks you through the material, quizzes you, and keeps track of your progress. You can also ask it questions, or tell it what to do (like skip a section you already know).

The main value of an LLM like Claude is that it can ask you questions and then respond to your answer. Claude is very good at being pedantic, so when you give it a vague answer, or one that is partially right and partially wrong, it will tell you which parts you got right and explain what you might have gotten wrong.

The skill runs entirely on Claude, optionally with data pulled from your instance using the Metabase MCP server. Metabase does not receive any information from the skill.

## Installation

The complete skill is available as a `.skill` file from the [Learn Metabase skill page](https://www.metabase.com/learn/cheat-sheets/claude-skill-learn-metabase). It contains the same files as this repo, but combined into a ZIP file for Claude.

To install the skill:

- In the Claude app, select the **Plugins** section in the sidebar
- Click on **Add** in the top right, then click the **Add** button and select **Upload a plugin.**
- Upload the skill file.

If you have the Metabase MCP server set up, the skill will draw from your own tables for questions and examples. We strongly recommend using it if you can, it will make your lessons much more meaningful. Learn how [to connect the MCP server](https://www.metabase.com/docs/latest/ai/mcp).
