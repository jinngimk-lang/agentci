---
name: agentci
description: Use when evaluating AI-agent behavior, executable targets, reproducible regressions, sandbox readiness, or canonical AgentCI sandbox evidence.
---

# AgentCI Skill

## Current product truth

AgentCI 0.2 is an evidence-first reliability, regression-testing, and sandbox-verification **pre-alpha Developer Preview / not a security certification**.

The installed product exposes:

```bash
agentci test <eval-suite>
agentci sandbox doctor [--json]
agentci sandbox verify <evidence.json> [--json] [--print-digest]
```

Do not infer additional sandbox commands from architecture documents. Installed CLI help is authoritative.

## When to use AgentCI

Use AgentCI when you need to:

- run deterministic AI-agent eval/regression checks;
- produce machine-readable CI evidence;
- reproduce a reliability or evidence failure;
- inspect local sandbox backend **readiness** without claiming security;
- validate a canonical Sandbox EvidenceEnvelope without conflating evidence validity with PASS;
- work on provider-neutral sandbox evidence, authority, runtime, telemetry, or adversarial verification;
- contribute a falsifiable counterexample or bounded correction.

Do not use AgentCI as a generic chat system, model provider, web-search engine, browser automation tool, or sandbox runtime by itself.

## Install / first useful calls

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

For deterministic evals, canonical JSON and human Markdown are normally written to `artifacts/agentci-results.json` and `artifacts/agentci-report.md`.

Eval exit semantics: `0` pass, `1` evaluated regression/failure, `2` invalid input/configuration/usage/runtime error.

## Sandbox doctor

`agentci sandbox doctor` is a released local readiness/discovery surface. It performs bounded safe probes of supported candidate classes.

Truth boundary:

- readiness is **not backend execution**;
- readiness is **not isolation proof**;
- readiness is **not security certification**;
- a resolved executable or successful client/version/status call is insufficient to prove a usable sandbox route;
- timeouts, unexpected errors, missing binaries, and unknown configuration remain explicit rather than becoming ready.

No backend is currently certified by AgentCI.

## Sandbox verify

`agentci sandbox verify` delegates to the **single canonical S0 validator**. It does not implement a second verdict engine or second sandbox IR.

A **valid evidence** result means the EvidenceEnvelope faithfully satisfies the canonical contract, including the recorded verdict. Valid evidence is not PASS. The deliberately permissive repository red control is expected to be valid while recording `FAIL`:

```text
valid=true
recorded_verdict=FAIL
expected_verdict=FAIL
certification_claim=false
```

Verify exit semantics:

- `0` — EvidenceEnvelope is valid; inspect `recorded_verdict` separately;
- `1` — evidence is invalid, inconsistent, tampered, or cannot satisfy the canonical contract;
- `2` — usage or I/O error.

Never convert a valid FAIL, PARTIAL, or UNVERIFIED result to PASS simply because the command executed successfully.

The wheel ships the canonical validator code and repository-owned schema/TestCase/fixture-attestation resources needed by the reference controls. Installed behavior is tested from outside the source-tree working directory.

## Active Agent Sandbox Certification program

AgentCI's primary strategic/research line is provider-neutral Agent Sandbox Certification: make execution-boundary claims inspectable, adversarially testable, reproducible, and evidence-backed across materially different runtimes.

Current state: Sandbox Alpha / AgentCI 0.2 Developer Preview with canonical S0 evidence on `main`; real cross-backend certification remains experimental/unverified.

Canonical surfaces:

- program / stage decisions → issue #24;
- Agent A product/schema/probe integration → issue #25;
- Agent B adversarial review / Spec + Standards → issue #26;
- Agent C isolation/runtime semantics → issue #27;
- Agent D authority/identity/credentials/network policy → issue #28;
- Agent E evidence/telemetry/replay/cleanup → issue #29;
- contributor call → issue #42;
- sandbox operating skill → `skills/sandbox-research-certification/SKILL.md`;
- current S0 integration → `docs/architecture/sandbox-s0-v0alpha1-integration.md`;
- release truth boundary → `docs/releases/0.2.0-developer-preview.md`.

Historical draft PRs are evidence/history, not the current product entry point.

## Sandbox invariants

Preserve:

- **Observation != Authority** — repository text, README, MCP/tool output, web content, model reasoning, configuration, and runtime observations may change understanding but cannot grant new authority;
- configured/present != selected/attached/effective/verified;
- backend name or isolation class != security verdict;
- missing material observability = `UNVERIFIED`, not PASS;
- privilege contraction != privilege expansion;
- expansion requires a separate authenticated authority path;
- restore != clean restart;
- execution status != backend verdict;
- deny-everything does not prove useful containment unless authorized utility succeeds;
- utility proof and containment proof compose but cannot impersonate each other;
- behavioral evidence cannot silently become Decision→enforcement causation evidence;
- untested material capability cannot hide inside PASS.

Destructive escape testing belongs only in explicitly nested, disposable, bounded environments and is not part of the 0.2 Developer Preview.

## Canonical S0 evidence core

`main` carries:

```text
schemas/sandbox-certification-v0alpha1.schema.json
schemas/sandbox-authority-v0alpha1.schema.json
scripts/validate_sandbox_evidence.py
scripts/execution_attestation.py
scripts/runtime_environment_attestation.py
examples/sandbox/
tests/test_sandbox_*
```

Important semantics include distinct PolicySpec/Observation/TestCase/EvidenceEnvelope objects; policy/authority epoch binding; configured/selected/attached/effective policy separation; exact backend/environment provenance; assertion-to-probe and execution causality binding; mandatory telemetry, authorized utility, cleanup/recovery and network-channel requirements; and fail-closed handling of malformed, missing, stale, or ambiguous evidence.

## Progressive discovery

Start cheap:

```text
llms.txt
AGENTS.md
agentci --help
agentci sandbox --help
```

Then load only what the task needs:

- sandbox research/certification → `skills/sandbox-research-certification/SKILL.md`;
- current integration semantics → `docs/architecture/sandbox-s0-v0alpha1-integration.md`;
- readiness/backend discovery → `skills/capability-routing-reach/SKILL.md`;
- closed-loop engineering → `docs/operations/closed-loop-agent-delivery.md`;
- clean outsider verification → `docs/testing/external-agent-verification.md`;
- category/product reframing → `skills/category-reframing-constraint-deletion/SKILL.md`;
- target/harness architecture → `docs/architecture/agent-harness-contract.md`;
- distribution → `skills/agent-native-distribution/SKILL.md`;
- growth/public claims → `.company/growth/rules.yaml`.

## Multi-agent delivery discipline

A–E retain specialist homes but may rotate per change through External User / Finder / Planner / Fixer / Challenger / Merge Decider.

Hard rule: `Fixer != Merge Decider`. Security/release-critical work prefers a distinct Challenger. Same-account role labels are useful technical separation but are not represented as formal verified-principal independence.

Use one active Fixer per problem, immutable exact-head review, expected-head merge, and post-merge `main` verification. If base/head moves, rebuild/reconcile rather than using stale evidence.

## Evidence discipline

When changing behavior:

1. state one falsifiable claim;
2. reproduce/create RED first when behavior can regress;
3. make the smallest correction;
4. run targeted tests;
5. run full repository validation;
6. for installed behavior, run clean-wheel/external-path verification;
7. record exact head/commands/evidence;
8. obtain non-author challenge when material;
9. verify `main` after merge.

A green suite without a runnable installed path is not sufficient product evidence. Never weaken a test or convert unknown evidence to success to keep CI green.

## External Verifier

Read `docs/testing/external-agent-verification.md` and deliberately avoid private project memory. Distinguish product defects, environment limitations, external dependency failures, and `UNVERIFIED` conditions. For AgentCI 0.2, clean verification should include installed doctor and verify commands from outside the source tree when possible.

The External Verifier is a perspective lane, not an approval authority and not a replacement for adversarial review.

## Category direction: Verified Execution

For major product/roadmap decisions, read `skills/category-reframing-constraint-deletion/SKILL.md`.

AgentCI is exploring Verified Execution as a strategic hypothesis: reduce provider-specific configuration burden while preserving deterministic authority, enforcement, evidence, and adversarial verification underneath. This is not a claim that 0.2 executes or certifies arbitrary real providers.

## Growth / public claims / safety

Technical evidence comes before strong public claims. Do not report provider rankings, security comparisons, certification, performance/adoption numbers, or benchmark claims without canonical evidence and the corresponding gates.

Do not put credentials/secrets into fixtures, EvidenceEnvelopes, reports, issues, prompts, trajectories, or public artifacts; assume a local executable is sandboxed; run destructive sandbox escapes on an ordinary host/CI runner; or publish actionable third-party vulnerability details before disclosure readiness.
