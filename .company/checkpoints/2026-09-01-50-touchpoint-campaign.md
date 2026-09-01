# 50-Touchpoint Campaign Checkpoint — Cohorts 1–2

Date: 2026-09-01
Current integration base at Cohort 2 start: `bc6fbecbf6cb0fa9ad47c4fb5f1bee89c1bee71a`
Mode: attribution-first, evidence-first, reversible

## Purpose

This checkpoint records the first ten **confirmed external writes** under the current attribution-first 50-touchpoint campaign. It is a campaign recovery point, not an adoption or user-acquisition claim.

Canonical batches:

- `.company/growth/outreach-2026-09-01-50-touchpoint-batch-001.json`
- `.company/growth/outreach-2026-09-01-50-touchpoint-batch-002.json`
- schema: `agentci.outreach.v2`
- expected validator result per batch: 5 successful placements, all initially `posted`

## Cohort 1 — proven-channel concentration

Confirmed placements:

1. LangGraph #8757 — accepted delete vs residual derived embeddings — `terminality-resource-residue`
2. LangGraph #8754 — observation/read creates durable ghost state — `observer-side-effect`
3. LangGraph #8715 — scheduled child failure can be lost while parent closes successfully — `scheduled-failure-false-success`
4. LangGraph #8716 — one failed shared source yields contradictory branch terminal observations — `split-observer-false-success`
5. LangGraph #8705 — in-memory green path does not cross the durable serialization boundary — `durable-path-evidence-gap`

Failed write:

- `ringier-data/nannos#182` — GitHub App 403; recorded under `attempts`, zero successful placements.

Cohort 1 is deliberately concentrated in LangGraph because the strongest evidenced acquisition chain remains:

```text
LangGraph #8582 upstream reproduction
→ AgentCI technical fixture invitation
→ reporter reply
→ AgentCI #123 intake
→ external fork / PR #124
→ verified merge
```

## Cohort 2 — bounded multi-ecosystem expansion

Confirmed placements:

1. Browser Use #5635 — saved-history variable semantics can break requested rerun substitution — `replay-substitution-fidelity`
2. OpenClaw #134999 — stale persisted lock plus PID reuse can masquerade as continuing ownership — `lease-ownership-crash-residue`
3. LangGraph #8768 — shared stream union can underfetch an explicitly unscoped subscriber — `subscription-evidence-completeness`
4. OpenClaw #134895 — payload execution and operator-visible delivery can diverge — `execution-delivery-divergence`
5. OpenClaw #134982 — approval authority can degrade across presentation encodings — `cross-surface-authority-preservation`

Failed write:

- `mastra-ai/mastra#22702` — GitHub issue-comment write returned 403 Blocked; recorded under `attempts`, zero successful placements.

This cohort intentionally expands beyond the proven LangGraph channel while preserving the same technical-value requirement. Browser Use and OpenClaw remain experimental acquisition channels until public downstream evidence appears.

## Campaign progress

Confirmed external technical placements: **10**.

Default design allocation for high-intent external technical-thread placements: approximately **20** of the overall 50 touchpoints. Therefore the campaign has reached 10/20 of the default external-comment allocation, not 10/50 of all touchpoint categories.

The remaining campaign work also includes AgentCI-owned searchable conversion surfaces, ecosystem listings/discussions, and reusable technical assets. Do not convert those categories into extra issue comments merely to satisfy a total count.

Current downstream state at capture: `posted` for all ten canonical placements unless a later batch/checkpoint explicitly upgrades a placement with public evidence URLs. No hidden visit, click, referral, adoption, reply, fork, issue, PR, merge, or repeat-contributor event is inferred from publication alone.

## Product conversion loop

Promotion and product work must stay coupled:

1. preserve high-value upstream failures as canonical provenance;
2. reduce repeated semantic failures into provider-neutral fixtures/validators/showcase assets;
3. make the landing path cheap to understand and run;
4. later promotion should link directly to the relevant technical asset when it exists, rather than only to the repository root.

Current priority remains the LangGraph #8764 admission-vs-durability fixture, because the upstream thread produced a useful semantic clarification: without authoritative external admission evidence, zero checkpoints plus zero user effects is `NOT_ADMITTED_OR_UNKNOWN`; with independent authoritative admission evidence it becomes `ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING`. Blind retry remains `UNVERIFIED`.

## Attribution boundary

Public replies, reactions when recorded, forks, issues, PRs, merges, repeat contributions, stars, and similar events may be recorded as observable signals. They do not automatically prove that an AgentCI comment caused a repository visit or adoption event.

Traffic, referrers, impressions, clicks, and repository visits remain unknown when connected tooling cannot observe them. Do not infer them from temporal proximity or public counters.

Comments inside AgentCI do not count as external promotion. Failed writes, 403s, duplicates, and skipped targets never count as placements.

## Next decision

Next loop order:

1. validate Cohort 2 offline and preserve its RED→GREEN evidence;
2. re-check Cohort 1 and Cohort 2 threads for public downstream evidence before deciding which channel receives the next five placements;
3. rebuild the LangGraph #8764 fixture integration from current main if its prior successor base has become stale;
4. add at least one directly searchable/citable AgentCI technical asset before exhausting the remaining external-comment allocation;
5. update downstream states only from public evidence URLs;
6. keep the campaign total split by touchpoint category so external comments do not crowd out owned search surfaces, ecosystem placements, or reusable assets.

The campaign remains open. Cohorts 1–2 prove ten public technical placements and an auditable accounting mechanism; they do not prove ten acquired users.
