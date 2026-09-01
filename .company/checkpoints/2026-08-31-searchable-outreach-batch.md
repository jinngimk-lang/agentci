# Searchable External Outreach Batch — 2026-08-31

Status: published; downstream attribution pending
Parent strategy checkpoint: `.company/checkpoints/2026-08-31-attribution-product-loop.md`

## Purpose

Record one bounded batch of real external promotion in public threads where qualified users are already searching for agent evaluation, sandbox, authority, terminality, and observability failures.

A post counts here only when the GitHub write succeeded. Readable-but-nonwritable repositories and failed connector calls are not counted as promotion.

## Successful public placements

1. **agent-glovebox #5142** — https://github.com/AlexanderMattTurner/agent-glovebox/issues/5142#issuecomment-5475835097
   - Search/problem path: agent sandbox evaluation, cross-sandbox parity, sandbox failure diagnosis.
   - AgentCI value: provider-neutral differential fixture binding workload identity, reference/candidate observations, failure phase, evidence completeness, and an `UNVERIFIED` boundary.
   - Initial attribution state: `POSTED / DOWNSTREAM_PENDING`.

2. **OrchordsAI #79** — https://github.com/ORCHORDS/OrchordsAI/issues/79#issuecomment-5475839928
   - Search/problem path: MCP/workspace tool approval, model-assisted review, authority boundaries.
   - AgentCI value: adversarial authority-binding fixture where reviewer output remains evidence and deterministic policy remains authority.
   - Initial attribution state: `POSTED / DOWNSTREAM_PENDING`.

3. **hermes-agent #236** — https://github.com/RyderFreeman4Logos/hermes-agent/issues/236#issuecomment-5475843888
   - Search/problem path: agent lifecycle, bounded execution, completion/checkpoint discipline, false completion.
   - AgentCI value: terminality/evidence-completeness fixture comparing declared completion with workspace, commit, and verification facts.
   - Initial attribution state: `POSTED / DOWNSTREAM_PENDING`.

4. **Mastra #21941** — https://github.com/mastra-ai/mastra/issues/21941#issuecomment-5475852307
   - Search/problem path: agent observability, trace environment/provenance, missing/stale traces.
   - AgentCI value: provenance-binding fixture where syntactically valid trace metadata is semantically false because launch-surface identity is conflated with runtime environment variables.
   - Initial attribution state: `POSTED / DOWNSTREAM_PENDING`.

5. **Mastra #22346** — https://github.com/mastra-ai/mastra/issues/22346#issuecomment-5475860337
   - Search/problem path: guardrails, TripWire, processor tracing, false-success telemetry.
   - AgentCI value: false-PASS evidence fixture comparing equivalent abort behavior across execution paths and requiring consistent terminal/error/retry evidence.
   - Initial attribution state: `POSTED / DOWNSTREAM_PENDING`.

## Explicitly excluded failed writes

The following high-fit threads were readable, but the connected GitHub integration returned HTTP 403 for issue-comment writes. They are **not** counted as placements:

- `fitlab-ai/agent-infra#936`
- `Gentleman-Programming/gentle-ai#2702`
- `GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK#466`
- `pmcfadin/cqlite#3650`

Do not retry these merely to increase volume unless repository permissions or thread state materially changes.

## Measurement contract

For each successful placement, update status only from observable downstream evidence:

```text
POSTED
→ REPLIED
→ REPO_ACTION (fork / AgentCI issue)
→ CONTRIBUTION (PR / fixture / benchmark)
→ MERGED
→ REPEAT_CONTRIBUTOR
```

A reaction may be recorded as engagement but is not equivalent to a repository visit or contribution. Hidden traffic/referrer data remains unknown unless tooling exposes it.

## Batch decision

Five high-fit placements are enough for this loop. Do not add another fifteen comments merely to reach a round number. First re-check this batch for downstream evidence, compare semantic classes, and then expand the channels that show real response.

The next product-side conversion improvement is AgentCI #131 / PR #132: a one-command starter configuration so a user who arrives from one of these threads can reach a deterministic first result with `agentci init` followed by `agentci test`.
