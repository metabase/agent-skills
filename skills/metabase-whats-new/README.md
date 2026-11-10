# Claude skill for what's new in Metabase

This skill finds out which Metabase version you're on, then teaches you what's new: features in your own release you might not be using yet, and what you'd get by upgrading. It teaches one feature at a time, with examples matched to how you use Metabase, and lets you steer (guided tour, a menu, or a quick summary).

If you don't know your version, it shows you how to find it. If you're several versions behind, it groups features by theme (AI, Data Studio, dashboards, metrics, embedding, admin) instead of walking through every release.

## What it covers

Release notes from Metabase 48 onward are bundled in `references/`, one file per release. Each time it runs, the skill also checks [metabase.com/releases](https://www.metabase.com/releases) for anything newer and summarizes the new release page for that conversation. It only reads public pages on metabase.com and doesn't send Metabase anything about you or your instance.

It knows the difference between open source (`v0.x`) and paid plans (`v1.x`), and says when a feature is on Pro and Enterprise only.

## Installation

In Claude Code:

```sh
npx skills add metabase/agent-skills --skill metabase-whats-new -a claude-code
```

In the Claude app:

- Find the **Customize** section.
- Click **Skills** in the top left, then click **+** and select **Create Skill** > **Upload a skill**.
- Upload a zip of this folder.

Then ask something like "what's new in Metabase?", "we're on 1.61, what did we miss?", or "should we upgrade?"

The skill needs web access to check for releases newer than its bundled notes. Without it, it still works from the bundled notes.
