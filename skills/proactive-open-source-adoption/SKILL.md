---
name: proactive-open-source-adoption
description: Use when supervising or researching AgentCI and a public GitHub skill, tool, framework, benchmark, protocol implementation, developer workflow, or open-source project may materially improve product value, reliability, security, activation, research, community growth, or distribution.
---

# Proactive Open-Source Adoption

The owner has pre-authorized proactive discovery and reversible deployment of useful public GitHub skills/projects. Do not wait for the owner to supply every link.

## Discovery scope

Prioritize projects relevant to agent eval/reliability, MCP/tool protocols, agent security, tracing/observability, coding agents, CLI/harness design, testing/debugging/review, agent skills/instructions, public-web research, capability routing/doctor semantics, GitHub/CI tooling, open-source community mechanics, and evidence-backed developer distribution.

Do not chase repositories merely because they are trending.

## Workflow

```text
discover
→ inspect primary repo/docs/releases
→ verify license + attribution
→ identify transferable pattern
→ compare with AgentCI baseline
→ classify risk/value
→ adopt low-risk part or define bounded experiment
→ notify A/B when their work is affected
→ B independently falsifies important claims
→ keep / revise / remove
→ record source + rationale
→ update durable Master Skill lessons
```

## Required questions

Before deploying, answer:

1. What concrete AgentCI problem does this solve?
2. Is the capability already covered?
3. Durable engineering pattern or hype/noise?
4. Maintenance status and latest meaningful activity?
5. License/NOTICE/attribution obligations?
6. New dependencies, permissions, network access, secrets, or attack surface?
7. Can the value be captured as a Skill, test pattern, contract, optional sidecar, adapter, or benchmark instead of a core dependency?
8. What evidence proves it beats the current baseline?
9. What is the smallest reversible deployment?
10. What evidence would justify removing it later?

## Classification

Use:

`adopt-now | experiment | benchmark | watch | reject | remove-existing`

- `adopt-now`: low-risk Skill/docs/test/contract/process improvement with clear value.
- `experiment`: plausible value requiring bounded implementation evidence.
- `benchmark`: useful as an external target/comparison, not necessarily an integration.
- `watch`: promising but immature, unstable, redundant, or premature.
- `reject`: wrong boundary, unsafe, license-incompatible, or no proven value.
- `remove-existing`: new evidence makes a prior choice inferior.

## Direct deployment authority

Without per-change owner approval, deploy reversible, evidence-backed, license-compliant improvements such as:

- reusable Skills;
- context/instruction routing;
- tests/review/debugging disciplines;
- schemas/contracts/templates;
- research provenance rules;
- bounded optional integrations;
- rollback-friendly CI checks;
- external benchmark fixtures;
- docs/community improvements.

For new core runtime dependencies, major architecture replacement, persistent external services, privileged credentials, paid services, or large migrations, use:

```text
bounded experiment
→ Agent B falsification
→ evidence review
→ graduate only if superior
```

Authorization to act is not authorization to skip validation.

## A/B coordination

If a discovered project changes implementation direction, Agent A receives the external signal, transferable pattern, bounded scope, acceptance criteria, baseline comparison, attribution requirements, and non-goals.

Agent B receives independent reproduction requirements, adversarial cases, baseline/competitor comparison, attack-surface review, and instructions to verify whether the external advantage is real.

Never accept an upstream project's benchmark or marketing claim as AgentCI evidence without independent reproduction.

## Preserve AgentCI identity

Adopt ideas, not identities. Do not turn AgentCI into a clone or dependency bundle.

Every adoption must measurably improve at least one of:

`user value | reliability | security | activation | reproducibility | observability | defensibility | community contribution | distribution | commercial usefulness`

If none improves, do not deploy.

## Master Skill self-improvement

When an external project reveals a durable cross-project operating lesson, add it to `skills/autonomous-owner-multi-agent-master/SKILL.md` and the portable Master Skill artifact. Keep project-specific implementation details out of the Master Skill.

A durable addition should still help a new agent operating another owner project six months from now. Otherwise keep it in AgentCI-specific docs.
