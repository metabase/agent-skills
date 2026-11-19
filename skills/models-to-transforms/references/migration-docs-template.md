# Migration docs template

Git carries the transforms and published-table metadata. These docs carry everything else: what changed on the
instance, who is affected, and how to undo it. Write them for two readers: someone auditing the change in six months,
and a user wondering why their model is gone.

Default layout (adapt it to where the user wants the docs):

```
<docs dir>/model-migration/
├── README.md                 # the overview below
├── waves/wave-0.md …         # one section per model, grouped by wave
├── user-changes.md           # what people will notice, written for them
└── runbook.md                # schedules/jobs created, rollback, purge instructions
(kept OUTSIDE git, in ./.scratch/model-migration/notify/: per-user notification lists, because they hold emails)
```

## README.md

```markdown
# Models → Library tables migration (<instance>, <start date> – <end date>)

**Status:** <wave N of M done · X models swapped · Y archived · purge scheduled for <date>>

## Why
Metabase is phasing out models in favor of transforms and published Library tables. Published tables lead the data
picker and are what Metabot's curated mode reads. Each model below was either mapped onto the existing table it wrapped,
or replaced by a transform that materializes its query.

## At a glance
| Outcome | Models |
|---|---|
| Swapped onto an existing table | … |
| Replaced by a new transform | … |
| Archived as unused | … |
| Kept (with reason) | … |
| Excluded (Metabase-managed) | … |

## Pull requests
- #<n> <its title, e.g. "Add transforms for Charges, Scored Issues and 8 more models">: wave 0, <k> transforms
- #<n> <its title, e.g. "Publish 10 tables in the Library and carry the models' column metadata">: wave 0

## What changed for people
See user-changes.md. In short: <freshness>, <bookmarks>, <links>, <action buttons>, <access>.

## Decisions
<every interview answer, named by its subject: policy, choice, who decided, when>
```

## Per-model record (in `waves/wave-k.md`)

```markdown
### <Model name> (card <id>, <entity_id>)
- **Was:** <what it was, in words: "a 1:1 wrapper of `dbt_models.account`" | "a SQL model joining deals and accounts"> in <collection path>, created by <creator>, <views> views, last used <date>
- **Now:** <schema.table> (table <id>), published in Library › <folder>; <existing table | transform "<name>" (id <id>), tag `<tag>` → job "<job>" (<cron>, <tz>), owner <email>>
- **Freshness:** <live | persisted hourly | cached N h> → <refreshed by job at …>
- **Pull requests:** #<n> <title>, #<n> <title>
- **Swap:** replacement run <run_id>, <status>, <n> entities rewritten (<q> questions, <d> dashboards, <m> metrics, …), <date>
- **Dependents, before → after:** each by name, what it read and what it reads now, and whether its results are the same (the plan's `changes.csv` rows, with the outcome filled in)
- **Fixed by hand:** <dashcards replaced on dashboards …>, <filters re-sourced …>, <links/URLs rewritten …>, <alerts recreated …>, <actions re-homed …>, <metric dimensions re-targeted …>
- **Lost / not migratable:** <bookmarks (n holders)>, <model index>, <replacement question <id>, verified>, <upload UI → use `mb upload append <table-id>`>
- **Metadata:** <display names/semantic types promoted to the table | table metadata kept; n columns now show different names>
- **Verification:** <row-count/checksum results, dependents spot-checked>
- **Archived:** <timestamp> · **Purge after:** <date> · **Snapshot:** ./.scratch/model-migration/snapshots/wave-<k>/<id>/
```

## user-changes.md (plain language)

Cover each of these that applies:

- **Where the data lives now:** the Library folder, and a link to the table.
- **Freshness:** "this used to be live; it now refreshes daily at 07:00 UTC".
- **Bookmarks:** "your bookmark on <model> no longer shows; open the verified question '<model name>' in <collection> instead (or the table in the Library)".
  Tables themselves can't be bookmarked.
- **Links:** old `/model/<id>` links show "not found". Here is where each one went.
- **Dashboards:** cards that showed a model now show a question on the table. Action buttons were re-created, or removed (list which).
- **Alerts:** recreated on <question>, or removed. Recipients were notified on <date>.
- **Access:** people who explored a model can explore the table through the Library. If you can't, ask <owner>.
- **Things that no longer exist:** model indexes (record search), list view, upload append/replace from the UI.
- **Column names:** the table's names may differ from the model's local names. These are the columns affected.

## runbook.md

- **Jobs created on the instance** (jobs don't sync): name, cron, timezone, tags, id, and why.
- **Transforms per job**, and their owners. Scheduled runs execute as the owner.
- **How to check health:** transform runs, `mb dependency breaking`, import status (`mb git-sync status`).
- **Rollback**, per `verification-and-rollback.md`, with the snapshot paths.
- **Purge:** the date, the gate query, and the command (`DELETE /api/card/:id` via the helper). Who approved it.

## Notification lists (outside git)

Per model, the people to tell, and what to tell them:

- bookmark holders (`card_bookmark` + `core_user`);
- alert recipients;
- creators and owners of dashboards that had a model dashcard, action buttons, link cards or `/model/` URLs;
- heavy viewers (from `view_log`, last 90 days);
- owners of embeds and public links.

Draft the messages, and leave sending to the user.
