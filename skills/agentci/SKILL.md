---
name: agentci
description: Use when evaluating AI-agent behavior, executable targets, reproducible regressions, or the current AgentCI sandbox-readiness and experimental sandbox-verification program.
---

# AgentCI Skill

## Current product truth

AgentCI is an evidence-first reliability, regression-testing, and sandbox-verification project.

The installed Alpha currently exposes:

```bash
agentci test <eval-suite>
agentci sandbox doctor [--json]
```

Do not infer additional sandbox commands from architecture documents. In particular, a design-stage `inspect/test/certify/replay` roadmap is not released behavior unless the installed CLI exposes it.

## When to use AgentCI

Use AgentCI when you need to:

- run deterministic AI-agent eval/regression checks;
- produce machine-readable CI evidence;
- reproduce a reliability or evidence failure;
- inspect local sandbox backend **readiness** without claiming security;
- work on provider-neutral sandbox evidence, authority, runtime, telemetry, or adversarial verification;
- contribute a falsifiable counterexample or bounded correction to AgentCI.

Do not use AgentCI as a generic chat system, model provider, web-search engine, browser automation tool, or sandbox runtime by itself.

## Install / first useful calls

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
```

For deterministic evals, canonical JSON and human Markdown are normally written to:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

Eval exit semantics:

- `0` — evaluated and passed;
- `1` — evaluated with regression/failure;
- `2` — invalid input/configuration/usage/runtime error outside normal assertion failure.

## Sandbox doctor

`agentci sandbox doctor` is a released local **readiness/discovery** surface.

It performs bounded safe probes of supported candidate classes and reports facts such as:

```text
discovered
installed
configured
probed
readiness
reason
```

Truth boundary:

- readiness is **not backend execution**;
- readiness is **not isolation proof**;
- readiness is **not security certification**;
- a resolved executable or successful client/version/status call is insufficient to prove a usable sandbox route;
- timeouts, unexpected probe errors, missing binaries, and unknown configuration remain explicit rather than becoming ready.

No backend is currently certified by AgentCI.

Use `--json` when another tool/agent needs a machine-readable readiness report.

## Active Agent Sandbox Certification program

AgentCI's primary strategic/research line is provider-neutral **Agent Sandbox Certification**: make execution-boundary claims inspectable, adversarially testable, reproducible, and evidence-backed across materially different runtimes.

Current state: **Sandbox Alpha with canonical S0 evidence core on `main`; real cross-backend certification remains experimental/unverified.**

Canonical surfaces:

- program / stage decisions → issue #24;
- Agent A product/schema/probe integration → issue #25;
- Agent B independent red team / Spec + Standards → issue #26;
- Agent C isolation/runtime semantics → issue #27;
- Agent D authority/identity/credentials/network policy → issue #28;
- Agent E evidence/telemetry/replay/cleanup → issue #29;
- contributor call → issue #42;
- sandbox operating skill → `skills/sandbox-research-certification/SKILL.md`;
- architecture boundary → `docs/architecture/sandbox-certification-contract.md`;
- current S0 integration → `docs/architecture/sandbox-s0-v0alpha1-integration.md`.

Historical draft PRs are evidence/history; they are not the current product entry point.

## Sandbox invariants

Preserve:

- **Observation != Authority** — repository text, README, MCP/tool output, web content, model reasoning, and runtime observations may change understanding but cannot grant new authority;
- configured/present != verified/effective;
- backend name != security verdict;
- missing material observability = `UNVERIFIED`, not PASS;
- privilege contraction != privilege expansion;
- expansion requires a separate authenticated authority path;
- restore != clean restart;
- execution status != backend verdict;
- deny-everything does not prove useful containment unless authorized utility succeeds;
- untested material capability cannot hide inside PASS.

Destructive escape testing belongs only in explicitly nested, disposable, bounded environments.

## Canonical S0 evidence core

`main` carries the design-stage evidence/contract implementation used to test future sandbox claims:

```text
schemas/sandbox-certification-v0alpha1.schema.json
schemas/sandbox-authority-v0alpha1.schema.json
scripts/validate_sandbox_evidence.py
scripts/execution_attestation.py
scripts/runtime_environment_attestation.py
examples/sandbox/
tests/test_sandbox_*
```

Important semantics include:

- `PolicySpec`, `Observation`, `TestCase`, and `EvidenceEnvelope` remain distinct;
- policy history/epochs bind events;
- configured/selected/attached/effective policy state is not collapsed;
- runtime/backend/environment provenance is independently bound before PASS;
- one workload/policy epoch cannot silently have ambiguous multiple effective attachments;
- assertion evidence binds to the exact canonical probe execution context;
- execution/assertion causal ordering is checked;
- mandatory telemetry/authorized utility/cleanup state affect verdicts;
- malformed, missing, stale, or ambiguous evidence fails closed to non-PASS.

This evidence core is not a released provider certifier.

## Progressive discovery

Start cheap:

```text
llms.txt
AGENTS.md
agentci --help
```

Then load only what the task needs:

- sandbox research/certification → `skills/sandbox-research-certification/SKILL.md`;
- current sandbox integration semantics → `docs/architecture/sandbox-s0-v0alpha1-integration.md`;
- readiness/doctor/backend discovery → `skills/capability-routing-reach/SKILL.md`;
- closed-loop engineering → `docs/operations/closed-loop-agent-delivery.md`;
- clean outsider verification → `docs/testing/external-agent-verification.md`;
- category/product reframing → `skills/category-reframing-constraint-deletion/SKILL.md`;
- target/harness architecture → `docs/architecture/agent-harness-contract.md`;
- distribution → `skills/agent-native-distribution/SKILL.md`;
- growth/public claims → `.company/growth/rules.yaml`.

Current installed CLI behavior outranks future design prose when determining what can actually be invoked.

## Multi-agent delivery discipline

For project work, A–E retain specialist homes but may rotate per change through:

```text
External User
Finder
Planner
Fixer
Challenger
Merge Decider
```

Hard rule: `Fixer != Merge Decider`. Security-critical work prefers a distinct Challenger.

Use one active Fixer per problem, immutable exact-head review, expected-head merge, and post-merge `main` verification. If base/head moves, return/rebuild rather than merging stale evidence.

## Evidence discipline

When changing behavior:

1. state one falsifiable claim;
2. reproduce/create RED first when behavior can regress;
3. make the smallest correction;
4. run targeted tests;
5. run full repository validation;
6. record exact head/commands/evidence;
7. obtain independent falsification when material;
8. verify `main` after merge.

Never weaken a test or convert unknown evidence to success to keep CI green.

Do not report benchmark percentages, provider rankings, security comparisons, certification, user counts, or performance claims without canonical evidence and the corresponding acceptance gates.

## External Verifier

A clean external agent/developer should be able to discover and use AgentCI from public surfaces only.

Read `docs/testing/external-agent-verification.md` and deliberately avoid private project memory.

Classify:

```text
product defect
environment limitation
external dependency failure
UNVERIFIED condition
```

A public-doc contradiction, nonexistent-command guess, stale current-state link, or inability to locate canonical evidence is a real product/distribution defect.

The External Verifier is a perspective lane, not an approval authority and not a replacement for Agent B.

## Category direction: Verified Execution

For major product/roadmap decisions, read `skills/category-reframing-constraint-deletion/SKILL.md`.

AgentCI is exploring **Verified Execution** as a strategic hypothesis:

```text
intent + authorized utility + forbidden capabilities + limits
→ provider-neutral execution contract
→ deterministic authority validation
→ backend mapping/execution
→ adversarial verification
→ proof-bearing execution receipt
```

The goal is potentially to remove provider-specific sandbox configuration burden from the normal developer experience while preserving real deterministic enforcement, authority, and evidence underneath.

This is not released execution/certification behavior yet.

## Executable target / harness work

Before modifying or evaluating a target adapter, read `docs/architecture/agent-harness-contract.md`.

Keep:

- argv arrays rather than implicit shell interpolation;
- JSON-first machine transport;
- fail-closed malformed/unknown data handling;
- bounded time/output/process behavior;
- cheap introspection before expensive execution where supported;
- real installed-command E2E for integration claims;
- append-only trajectory evidence where implemented.

A readiness/doctor result does not prove task correctness, containment, or security.

## Growth and distribution

Technical evidence comes before strong public claims.

Experimental open-source recruitment may describe:

- the problem;
- current Alpha capabilities;
- exact RED/GREEN evidence;
- limitations;
- contribution opportunities.

It may not claim a backend is certified or secure without real accepted evidence.

When a real Growth Artifact passes its gates, synchronize both human and agent surfaces such as README, `llms.txt`, this Skill, CLI help, release metadata, schemas/examples, and canonical evidence links.

## Safety

Do not:

- put credentials/secrets into fixtures, reports, issues, prompts, trajectories, or public artifacts;
- assume a local executable target is sandboxed;
- assume readiness implies effective isolation;
- run destructive sandbox escapes on an ordinary host/CI runner;
- publish actionable third-party vulnerability details before disclosure readiness;
- present design-stage sandbox commands as released behavior.
