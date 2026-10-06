# Plan the build

Applies: the router sends a planning situation here (a new instance with a new database, a new source in an instance that already has modeled data, a migration from another tool), the user asks to plan or re-plan, or a plan comes back with answers (step 9). Produces `plans/<dataset>-plan.md`, approved at the pre-create gate, and STATE.md with `plan:` set. Nothing is written to Metabase.

Checklist: `1 orient` `2 intake` `3 brought files` `4 profile` `5 shape` `6 draft` `7 no default` `8 gate` `9 returns` `reply`.

Read first: [`plan-file.md`](../references/plan-file.md), [`planning-questions.md`](../references/planning-questions.md), [`state.md`](../references/state.md), [`profiling-catalog.md`](../references/profiling-catalog.md), and the domain file STATE.md names; with files brought, [`extraction-and-gap-report.md`](../references/extraction-and-gap-report.md); at step 5, [`layering-and-naming.md`](../references/layering-and-naming.md), "Choosing the shape".

## Commands you will run

Every `mb` line also takes `--profile $PROFILE --json`; `./.scratch/q` is the probe from `references/state.md`.

```bash
mb db list; mb db get $DB --include tables; mb collection tree; mb git-sync status
mb transform list --fields id,name,description,target                      # empty on a new instance
mb search --models dataset,metric,measure,segment --limit 50                # the whole instance: what exists, on which database
mb table list --db-id $DB --fields id,name,schema,data_layer,data_source    # dbt_, stg_, mart_ tables no transform built: another tool's project
mb setting get enable-embedding-sdk         # and -interactive, -static, -simple, embedding-app-origins-sdk, jwt-enabled, saml-enabled; null is off
mb auth list --json --max-bytes 0 | jq '.data[] | select(.profile == "<profile>") | .tokenFeatures'   # no --profile; what the license allows, not what is used
mb search "<metric the new source could change>" --models card,dashboard,metric,document   # dependents
./.scratch/q "SELECT count(*) AS left_rows, count(e.<key>) AS matched FROM <new_schema>.<table> n LEFT JOIN <existing_entity_table> e ON e.<key> = n.<candidate>"
cp plans/<dataset>-plan.md ./.scratch/<dataset>-plan.base.md                # after every write to the plan
diff ./.scratch/<dataset>-plan.base.md plans/<dataset>-plan.md              # what people changed since
```

## 1. Orient

Run the discovery once and write it into STATE.md as `explore-raw-data.md` step 3 would (`db_id`, `engine`, schemas, layer vocabulary, collection ids, existing models and metrics, environment, domain), with `stage: plan-the-build`; no later playbook re-discovers. Data not yet landed: land it per `explore-raw-data.md` step 1, the one step read from there. Decide from the evidence, and say why: the situation (no transforms or metrics anywhere and a new database: a new instance; transforms, models, or metrics on other databases or schemas and nothing reading this one: a new source in an existing instance; another tool's project brought or found in the warehouse: a migration), the domain by the router's table-name test, and the depth per `planning-questions.md`. Situation and depth head the plan when it is drafted (step 6). A job the router should not have sent (one question over a few tables, no money, no personal data) says so in one line and continues at `explore-raw-data.md` step 2, discovery done. An `unknown field path` error is an older server: drop `data_layer,data_source` from `--fields`.

## 2. Intake

One message, in place of `explore-raw-data.md` step 2: the situation and depth found and why; that a plan comes before building, at `plans/<dataset>-plan.md`, with about N questions, and that anything left unanswered keeps a default named as one; which questions this must answer, in the order they matter (each verbatim into STATE.md Questions); whether a number you will build already exists, and its export at the finest grain; what to bring for this situation, per `planning-questions.md`; that entries usually answered by someone else (finance on what counts as revenue, security on personal data) can be left for them, said as a statement, never a question about who owns definitions; and "say 'skip the plan' to go straight to a draft", which continues at `explore-raw-data.md` step 4, whose memo and gate still run. Documentation is welcome, never required.

## 3. Read what they brought

Per `extraction-and-gap-report.md`, "Reading what people bring": classify each input once; every claim becomes an entry with its provenance and citation; two sources disagreeing make the entry a `contradiction` carrying both claims. A migration runs the extraction rules and the gap report there; the report becomes the plan's Migration section and its open items become entries. Nothing brought: skip.

## 4. Profile

Per `profiling-catalog.md` and the domain file's probes, on the tables on a named question's path only. Add: personal-data columns counted per table, never listed; for a new source, the match rate of every candidate key against the existing entity tables, and the dependents of each existing metric the new source could change. A zero-row table on a question's path, an unreachable source, or a permission error stops when found, per the contract.

## 5. Shape

Per `layering-and-naming.md`, "Choosing the shape": recommend one shape from the profile and from what the plan says the numbers are for, written as one entry with what the alternative would cost. The inventory (one row per what, key, sources) is the plan's Shape section, in place of `explore-raw-data.md` step 6.

## 6. Draft the plan

Write the whole plan per `plan-file.md` before asking anything: every entry the bank, the brought files, and the profile produce, each with its proposal or `no default`, severity, what it affects, provenance, who usually answers, and status. Planning writes nothing to Metabase, so an entry drafted the moment its fact is found is raised in time; a fact that stops the plan itself (step 4) is still a checkpoint. Set STATE.md `plan:`, and refresh the base copy after this and every later write.

## 7. Entries with no default

Ask each entry whose value must come from the profile or a person, one checkpoint each in the contract's form, before the gate; where the question tool takes several questions in one call, up to four at once (the contract's walk-through exception). Write each answer into the plan in the response that receives it.

## 8. The gate

The pre-create gate in `SKILL.md`, in its planning form, asked once. Print the memo: every remaining open entry as one line under its id (the record, the default and where it came from, what changes if it is wrong), grouped by who usually answers. Then one checkpoint carrying items 1 and 2 of the gate as their own questions, with ids in chat since the plan holds none, and the memo question, which names the list above by id: walk through the High entries (Recommended in Balanced, with their count) / accept all as listed (Recommended in Just go) / review each (Recommended in Check with me). The walk-through goes by severity; within one severity, `no default`, then `contradiction`, then the rest; an entry others depend on before them, and the first slice's entries first; up to four per call, within the budget stated at intake. Offer "Leave it for <role>" only when that role differs from the person's, its description saying the cost: the numbers it touches stay Draft and unpublished until it is answered. Past the budget, entries stay in the memo, and "accept as listed" records them as decided by whoever accepted. Each answer lands in the plan in the response that receives it. The gate returns after the last answer, and the header reads `approved by <name>, <date>`. Only an entry with no default, or an irreversible one, blocks, and only the models it affects; an entry left for a role stays `PROVISIONAL`, named in the plan, and approving the plan with it listed answers the contract's more-than-three stop until a new one appears. Nobody to answer (a headless run): write the plan, set `next` to the gate, and stop; the plan is what gets forwarded. A harness mode that forbids writing files: the plan goes in the reply and is written once writes are allowed. Then the first slice: the plan's first Build-order question through [`build-clean-tables.md`](build-clean-tables.md), labelled Draft.

## 9. Returns

A plan comes back (a path, a file dropped into chat, pasted answers), or the plan on disk differs from the base copy. Compare it with `./.scratch/<dataset>-plan.base.md`; with no base copy (a teammate's machine), take only signed `Answer:` lines and new entries as input, and say that other edits were not looked for. A signed answer is `decided` by its signer; an unsigned one is attributed to whoever returned the plan and confirmed in the session. An answer equal to the default already built on changes only the status; one that differs runs the change flow (`semantic-layer-design.md`, "Own, file, change, retire", and `build-clean-tables.md` step 8) as one checkpoint naming what moves, before anything is rebuilt. Every other edit is a proposed change, all of them confirmed in one checkpoint; an edit to an entry someone else decided is `disputed`, and the decided reading stands until answered. An entry a person added gets the next id. Never re-ask an answered entry. When someone who usually answers joins the session, walk through only the entries waiting on them. Every answer and change lands in its entry and the change log in the response that receives it.

Finished example, two memo lines and the gate's memo question:

```
D3. sub_4471 was cancelled on 30 July and paid through 31 August. Default: it counts in August, from the billing system's paid-through date. If it stopped in July, August churn would go from 41 to 48. Usually answered by Finance.
D7. 31 prices carry 99.4% of trailing revenue; the plan groups them into four plan families by name. Default: the grouping in section 5. A wrong family moves upgrades and downgrades, not MRR. Usually answered by Finance and Product.
question: D1–D9 above are the plan's open decisions, 4 of them High. Walk through the High ones, accept all as listed, or review each?
options:
  - Walk through the 4 High ones (Recommended): about 4 questions; the rest keep their defaults, named in the plan.
  - Accept all 9 as listed: the defaults become decisions, recorded as yours.
  - Review each: 9 questions, up to four at a time.
```

## Done when

`plans/<dataset>-plan.md` holds every section, applicable or marked not, and every entry with its status; entries with no default are answered or name the models they block; the gate returned and the header names who approved it, or a headless run left `next` at the gate; STATE.md `plan:` is set and the base copy matches the plan.

## Reply

The five-part hand-back in `collaboration-contract.md`; part one names the plan file and who it is for; under part three: the situation, the depth and why, the shape, and each entry decided by the build that moves a number; part five: the first slice.
