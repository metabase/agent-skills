---
type: llm
focus: trace
weight: 1
---

The plan asks for one approval that covers the whole migration, all waves included: it states up front, per model and for each dependent (question, dashboard, metric, filter, action), what it reads now and what it will read afterwards and what changes for it, lists the user's own steps as only accepting the plan, merging the named pull requests (or nothing, if the agent merges) and confirming the purge, and never asks the user to approve a wave or batch separately or to run any command
