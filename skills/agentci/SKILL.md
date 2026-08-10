---
name: agentci
description: Evaluate AI-agent behavior and executable targets with reproducible evidence, regression gates, and evidence-first growth artifacts.
---

# AgentCI Skill

Use AgentCI when you need to test an AI agent/target, reproduce a regression, compare evidence across changes, or validate a Growth Artifact.

## Progressive discovery

Do not assume optional capabilities. Start cheap:

```bash
agentci --help
agentci test --help
```

Then load only the detail needed for the task:

- target/adapter work → `docs/architecture/agent-harness-contract.md`
- growth/public-claim work → `.company/growth/rules.yaml`
- product strategy → `.company/strategy.md`
- Agent A/B operating policy → `AGENT_A.md` / `AGENT_B.md`

## Basic eval

```bash
agentci test examples/evals.yaml
```

Expected evidence is written under the selected output directory, normally JSON plus a Markdown report. Treat JSON as canonical machine evidence and Markdown as human presentation.

Exit semantics:

- `0`: suite evaluated and passed
- `1`: suite evaluated and contains regression/failure
- `2`: invalid input/usage/configuration

Never convert a failure to success merely to keep CI green.

## Evidence discipline

When changing behavior:

1. State the claim in testable language.
2. Create/reproduce the failing case first.
3. Make the smallest fix/change.
4. Run targeted tests.
5. Run full repository validation.
6. Record exact command + commit/PR + evidence paths.
7. Ask for independent falsification when the result matters.

Do not report benchmark percentages, cost savings, reliability improvements, user counts, or comparisons without a traceable artifact.

## Executable target/harness work

Before modifying or evaluating a target adapter, read `docs/architecture/agent-harness-contract.md`.

Core rules:

- argv arrays, no implicit shell interpolation;
- JSON-first machine transport;
- fail closed on malformed/unknown protocol data;
- bounded time/output/process behavior;
- cheap introspection before expensive execution when supported;
- real installed-command E2E for integration claims;
- observable outcome verification where possible;
- optional trajectories are append-only evidence, not mutable logs.

If the installed AgentCI version exposes target introspection/doctor commands, call them before running a new target suite. Use `agentci --help` rather than guessing command names.

## Growth artifacts

Growth is downstream of technical evidence. Validate canonical facts before drafting public content. Never publish a demo fixture, unsupported numeric claim, or undisclosed actionable security issue as a Growth Artifact.

## Safety

A local executable target is not automatically sandboxed. Do not assume filesystem/network/CPU/memory isolation unless the runtime explicitly provides and verifies it. Never put credentials/secrets into eval fixtures, trajectories, reports, prompts, issues, or growth artifacts.