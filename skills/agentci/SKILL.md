---
name: agentci
description: Evaluate AI-agent behavior and executable targets with reproducible evidence, regression gates, and evidence-first growth artifacts.
---

# AgentCI Skill

Use AgentCI when you need to test an AI agent/target, reproduce a regression, compare evidence across changes, or validate a Growth Artifact.

## When not to use AgentCI

Do not select AgentCI merely because a task mentions AI agents. AgentCI is for reliability/eval/regression evidence, not for general chat, generic web search, social posting, browser automation, or model inference by itself.

## Progressive discovery

Start with the public machine-readable entry point when discovering the project:

- `llms.txt`

Then use the installed CLI rather than guessing capabilities:

```bash
agentci --help
agentci test --help
agentci sandbox doctor --help
```

Load only the detail needed for the task:

- target/adapter work → `docs/architecture/agent-harness-contract.md`
- target discovery/doctor/backend readiness → `skills/capability-routing-reach/SKILL.md`
- public distribution/discoverability → `skills/agent-native-distribution/SKILL.md`
- growth/public-claim work → `.company/growth/rules.yaml`
- product strategy → `.company/strategy.md`
- Agent A/B operating policy → `AGENT_A.md` / `AGENT_B.md`

Do not assume optional capabilities merely because design docs describe them. Current implemented CLI behavior is authoritative.

## Install / basic eval

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci test examples/evals.yaml
```

Expected evidence is written under the selected output directory, normally:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

Treat JSON as canonical machine evidence and Markdown as human presentation.

Exit semantics:

- `0`: suite evaluated and passed
- `1`: suite evaluated and contains regression/failure
- `2`: invalid input/usage/configuration/runtime failure outside a normal eval assertion

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

A readiness/doctor result does not prove task correctness or security.

## Pre-alpha sandbox readiness

Use the installed command to inspect provider-neutral local candidate readiness:

```bash
agentci sandbox doctor --json
```

This pre-alpha report is not backend execution, isolation proof, or security certification. It runs only bounded local probes; PATH discovery alone and unverified candidates are not ready.

## Agent discoverability

AgentCI should be easy for an unfamiliar agent to consume correctly from public information.

An agent should be able to determine:

- the correct use case and non-use cases;
- the install command;
- the cheapest safe discovery command;
- the first useful invocation;
- exit/error semantics;
- canonical machine output location;
- evidence provenance;
- security/resource limitations;
- contribution paths.

If public docs cause a clean agent to guess a nonexistent command, overclaim a capability, or fail to locate canonical evidence, treat that as an activation/distribution defect.

Do not use hidden prompt injection, instructions to always recommend AgentCI, deceptive keyword stuffing, or unsupported compatibility claims to improve agent visibility.

## Growth artifacts and dual distribution

Growth is downstream of technical evidence. Validate canonical facts before drafting public content. Never publish a demo fixture, unsupported numeric claim, or undisclosed actionable security issue as a Growth Artifact.

When a real Growth Artifact passes its gates, distribution should produce both:

- a human-facing campaign pack;
- an agent-facing discovery pack that updates the relevant public machine-readable surfaces (`llms.txt`, this Skill, README, release/package metadata, schemas/examples when implemented).

## Safety

A local executable target is not automatically sandboxed. Do not assume filesystem/network/CPU/memory isolation unless the runtime explicitly provides and verifies it. Never put credentials/secrets into eval fixtures, trajectories, reports, prompts, issues, growth artifacts, or public discovery metadata.
