# Explore raw data

Applies when orient finds raw schemas with nothing curated over them (L0–L1), or data must be landed first. Produces the questions in order, a profile of every table on a question's path, identities resolved, an inventory in the company's vocabulary, every decision recorded with its default, and the first slice started once the proposal point returns.

Read first: `references/profiling.md`; `references/modeling.md` (Layers, Names) before the inventory; the fired domain note's Questions for the owner and Traps.

Order: 1 land, 2 ask (stop), 3 discover, 4 count, 5 profile, 6 identities, 7 inventory, 8 proposal point (stop), 9 first slice, hand-back.

## 1. Land data not yet in the warehouse

With a loader, the user lands it untouched, then `mb db sync-schema <db-id> --wait`. Without one, and when the user asked to load the file (otherwise ask first, naming where it will land), a file under 50 MB goes through `mb upload csv --file <path> --collection <id>` when `mb setting get uploads-settings` has a non-null `.value.db_id`; its refresh is a manual `mb upload replace <table-id> --file <path>` on the reporting cadence, stated in the hand-back and guarded by the freshness check. Stop until `mb db get <db-id> --include tables` lists the tables.

## 2. Ask the owner

One `AskUserQuestion`, only for what the request and the instance leave open: who owns what the numbers mean ("I do" / someone else, named in free text); which questions matter, in order (likely ones read off table names as a multi-select, free text for theirs), each written verbatim into the questions table; whether a reference figure exists and at what grain (ask for the finest); which database, only when several could hold the data. Documentation is welcome, never required.

## 3. Discover

`mb search "<each question's wording>" --models metric,measure,segment,dataset,table --db-id <db-id>`: a question something already answers is marked `exists`. Existing transforms, their collections, and target tables are the conventions to match. Record the fired domain notes.

## 4. Count every table

One query over every table in the schemas the questions name (above ten million rows a statistics view may stand in, marked approximate):

```bash
source ./.scratch/probe.sh
mb table list --db-id "$DB" --fields id,name,schema --max-bytes 0 --profile "$PROFILE" --json \
  | jq -r --arg q "'" '.data[] | select(.schema | IN("<schema>", "<schema>")) | "SELECT \($q)\(.schema).\(.name)\($q) AS t, count(*) AS n FROM \(.schema).\(.name)"' \
  | sed '$!s/$/ UNION ALL/' > ./.scratch/counts.sql && q "$(cat ./.scratch/counts.sql)"
```

Zero rows on a question's path is a stop naming the number it blocks.

## 5. Profile only what a question touches

Per table on a path, per `references/profiling.md`: columns, meaning separated from loader plumbing, the probes, the probes its Questions for the owner name and each of its Traps that applies. No grain without a measured duplicate count, no join without a match rate, no literal from anywhere but the data. Note whether the loader keeps history; none makes history capture a memo item.

## 6. Resolve identities

Two sources describing one thing get one entity (`references/time-and-entities.md`, Conformed entities); the match rate goes in the memo and the hand-back.

## 7. Inventory

Per model, in the company's vocabulary: layer, name, one row per what, key, sources; final tables as entities, events, rollups; a composite grain as one key column; the flat default for a small company under a deadline, decided and shown. Choose the first slice's grain so the next question does not force a redo. Every table on a path feeds a model; the rest stay raw with row counts. Confirm every proposed name is free (no existing table or transform output).

## 8. The proposal point

1. Write each memo item to the state file as an open decision line.
2. Print the inventory as a short plain table ("Customers: one row per customer, from billing and the app, matched on email for 97%").
3. Print the decision memo as a numbered list, one line each, grouped by who answers (the owner's definitional choices first): the question, the default and its source, what the alternative changes in the headline (both figures when traced). Include the domain note's owner questions this data raises, colliding transforms (replace, supersede, or build alongside), the freshness the data supports (last complete period and its watermark), history capture when needed, and the materiality defaults.
4. One `AskUserQuestion` about the list by number ("Build the first slice on 1–7 as listed?": accept all (Recommended) / show the ones that move the headline most / walk through each / change the scope); a decision with no default gets its own question in the same call. Nothing runs after it in that response.

After the answer: items become decided lines, and the domain Document is created in the domain's Drafts collection (`mb document create`, titled `How to use <domain> numbers`) holding the decisions section, open and decided.

## 9. First slice

The first question, its tables only, into `playbooks/build.md` on the answered defaults, labelled Draft.

## Done when

Every table on a path is counted, profiled, inventoried; every decision is recorded open or decided; the proposal point returned (or, headless, is recorded unanswered); the slice started. Hand-back: the inventory in the user's terms, identity match rates, what stays raw with row counts, which question the slice delivers first and when.
