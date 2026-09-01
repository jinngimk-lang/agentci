# 50-Touchpoint Campaign Checkpoint — Cohort 1

Date: 2026-09-01
Base main: `8921b63cb44c49a82008eb15a7e08c9cba294d4e`
Mode: attribution-first, evidence-first, reversible

## Purpose

This checkpoint records the first five **confirmed external writes** after the current attribution-first campaign design. It is a campaign recovery point, not an adoption claim.

Canonical batch:

- `.company/growth/outreach-2026-09-01-50-touchpoint-batch-001.json`
- schema: `agentci.outreach.v2`
- expected validator summary: 5 successful placements, all initially `posted`

## Cohort result

Confirmed placements:

1. LangGraph #8757 — accepted delete vs residual derived embeddings — `terminality-resource-residue`
2. LangGraph #8754 — observation/read creates durable ghost state — `observer-side-effect`
3. LangGraph #8715 — scheduled child failure can be lost while parent closes successfully — `scheduled-failure-false-success`
4. LangGraph #8716 — one failed shared source yields contradictory branch terminal observations — `split-observer-false-success`
5. LangGraph #8705 — in-memory green path does not cross the durable serialization boundary — `durable-path-evidence-gap`

Each placement leads with a falsifiable invariant/evidence shape, discloses AgentCI affiliation, preserves the upstream issue as canonical provenance, and offers a bounded provider-neutral fixture contribution rather than asking for stars.

Current downstream state at capture: `posted` for all five. No reply, fork, issue, PR, merge, or repeat-contributor state is claimed yet for this cohort.

## Failed attempt

`ringier-data/nannos#182` was a high-fit checkpoint/replay-corruption candidate, but the connected GitHub App returned `403 Resource not accessible by integration` when attempting to write.

It is recorded under `attempts`, not `placements`, and contributes zero to successful-placement counts.

## Why this cohort is concentrated in LangGraph

The concentration is intentional rather than a diversity target. The currently strongest fully evidenced acquisition chain is:

```text
LangGraph #8582 upstream reproduction
→ AgentCI technical fixture invitation
→ reporter reply
→ AgentCI #123 intake
→ external fork / PR #124
→ verified merge
```

Until another ecosystem produces comparable downstream evidence, LangGraph replay/state/persistence/terminality failures get priority. Unproven channels remain bounded experiments; ecosystem count is not optimized for appearance.

## Attribution boundary

Public replies, forks, issues, PRs, merges, repeat contributions, stars, and similar events may be recorded as observable signals. They do not automatically prove that an AgentCI comment caused a repository visit or adoption event.

Traffic, referrers, impressions, clicks, and repository visits remain unknown when the connected tooling cannot observe them. Do not infer them from temporal proximity or public counters.

Comments inside AgentCI do not count as external promotion. Failed writes, 403s, duplicates, and skipped targets never count as placements.

## Next decision

Do not expand merely to hit a raw comment quota.

Next loop order:

1. validate and merge this v2 batch/accounting checkpoint;
2. re-check the five upstream threads for downstream public evidence before scaling the same message class;
3. while responses are unknown, turn one high-value upstream failure into a reusable public technical asset/fixture so later placements can link directly to evidence rather than only the repository root;
4. prefer the already scoped LangGraph #8764 admission-vs-durability fixture unless stronger new evidence changes the product priority;
5. update downstream state only from public evidence URLs.

The campaign remains open. Cohort 1 proves five public technical placements and the accounting mechanism; it does not prove five acquired users.
