# AgentCI 0.2 Developer Preview

AgentCI is an evidence-first CI, reliability, and security-verification project for AI agents and agent-facing execution environments.

The current primary product line is **Agent Sandbox Alpha**: a provider-neutral foundation for discovering sandbox readiness, validating sandbox evidence, rejecting false-PASS claims, and building toward independently reproducible cross-backend verification.

> **Sandbox providers build the cage. AgentCI verifies what can actually be proved about the cage.**

**AgentCI 0.2 is a pre-alpha Developer Preview / not a security certification.** No sandbox backend is currently claimed as certified or secure by AgentCI.

## Current delivered Alpha

The installed product exposes three distinct surfaces.

### 1. Deterministic agent evals

```bash
agentci test examples/evals.yaml
```

This writes canonical JSON plus a human-readable report under `artifacts/`.

### 2. Truth-bounded sandbox readiness discovery

```bash
agentci sandbox doctor
agentci sandbox doctor --json
```

`doctor` performs safe, bounded local discovery/readiness probes for supported candidate classes such as Docker, Podman, bubblewrap, WSL, and Windows Sandbox where relevant to the host.

Its truth boundary is deliberate:

- **readiness is not backend execution**;
- **readiness is not isolation proof**;
- **readiness is not security certification**;
- an installed binary or successful version/status probe does not by itself make a backend `ready`;
- unknown configuration or probe failures remain explicit rather than being promoted to success.

### 3. Canonical sandbox evidence verification

```bash
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

`verify` uses the same canonical S0 validator that backs the repository's adversarial sandbox regressions. It validates whether an EvidenceEnvelope faithfully satisfies the contract, including its recorded verdict.

A **valid evidence** result is not the same thing as PASS and is **not a security certification**. The repository's deliberately permissive red control is intentionally valid evidence with:

```text
valid=true
recorded_verdict=FAIL
expected_verdict=FAIL
certification_claim=false
```

Sandbox verify exit semantics:

- `0` — the EvidenceEnvelope is valid; inspect `recorded_verdict` separately;
- `1` — the evidence is invalid, inconsistent, tampered, or cannot satisfy the canonical contract;
- `2` — usage or I/O error.

Missing or materially unavailable evidence remains `UNVERIFIED`/non-PASS rather than being inferred away.

## Sandbox evidence core on `main`

AgentCI carries the S0 evidence core used to harden sandbox verification:

- `schemas/sandbox-certification-v0alpha1.schema.json`;
- `schemas/sandbox-authority-v0alpha1.schema.json`;
- `scripts/validate_sandbox_evidence.py`;
- execution/runtime-environment attestation helpers;
- canonical sandbox TestCases and synthetic red-control fixtures;
- regression tests for policy epochs, effective attachments, authority/evidence binding, cleanup state, execution causality, backend/environment provenance, network-channel semantics, telemetry completeness, authorized utility, and false-PASS mutations.

The canonical integration description is [`docs/architecture/sandbox-s0-v0alpha1-integration.md`](docs/architecture/sandbox-s0-v0alpha1-integration.md).

The installed verifier packages the same canonical validator code and repository-owned schema/TestCase/fixture-attestation files. It does not maintain a second sandbox IR.

## Why AgentCI exists

Sandbox security is often described through configuration:

```text
runtime class
policy file
network allowlist
credential settings
provider name
```

AgentCI treats those as declarations, not proof.

The program keeps these invariants:

- **Observation != Authority**;
- configured/present != selected/attached/effective/verified;
- backend name != security verdict;
- missing material observability = `UNVERIFIED`, not PASS;
- privilege contraction != privilege expansion;
- privilege expansion requires a separate authenticated authority path;
- restore != clean restart;
- execution status != backend verdict;
- deny-everything != useful containment unless authorized utility still succeeds;
- untested material capabilities cannot hide inside PASS;
- behavioral outcome evidence is not automatically Decision→enforcement causation evidence.

## Product direction: Verified Execution

AgentCI is exploring a category-level product hypothesis: developers should eventually express an **authorized task outcome and constraints**, rather than manually understand every provider-specific sandbox mechanism.

Conceptually:

```text
intent + authorized utility + forbidden capabilities + limits
        ↓
provider-neutral execution contract
        ↓
deterministic authority validation
        ↓
backend mapping / execution
        ↓
adversarial verification
        ↓
proof-bearing execution receipt
```

This remains a strategic direction, not a claim that 0.2 executes or certifies arbitrary real providers. The project deliberately keeps deterministic enforcement and external authority even if future UX removes provider-specific configuration burden.

See [`skills/category-reframing-constraint-deletion/SKILL.md`](skills/category-reframing-constraint-deletion/SKILL.md).

## 5-minute quickstart

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

For deterministic evals, default evidence is:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

Eval exit semantics:

- `0` — suite evaluated and passed;
- `1` — suite evaluated and contains a regression/failure;
- `2` — invalid input, configuration, usage, or execution error outside a normal eval assertion.

A successful doctor process exit means it produced a readiness report, not that a sandbox security claim passed. A successful verify process exit means the EvidenceEnvelope is valid, not that its recorded verdict is PASS.

## Clean-wheel product gate

CI builds a wheel, installs it into a fresh virtual environment, switches to a working directory outside the repository, and runs both doctor and verify. This permanently checks that installed behavior does not accidentally depend on an editable checkout or the current working directory.

See [`docs/releases/0.2.0-developer-preview.md`](docs/releases/0.2.0-developer-preview.md) for the exact release boundary.

## For AI agents

Start with public, cheap discovery surfaces:

```text
llms.txt
AGENTS.md
skills/agentci/SKILL.md
agentci --help
agentci sandbox --help
agentci sandbox doctor --help
agentci sandbox verify --help
```

An unfamiliar agent should be able to determine what is actually released, what remains experimental, how to install and make the first useful call, where canonical evidence lives, which claims remain `UNVERIFIED`, and how to contribute a counterexample or fix.

Do not guess commands from architecture documents. Installed CLI help is authoritative.

## Active Sandbox Program

Canonical coordination:

- [Program / Supervisor #24](../../issues/24)
- [Agent A — product contract + probes #25](../../issues/25)
- [Agent B — independent red team #26](../../issues/26)
- [Agent C — isolation/runtime semantics #27](../../issues/27)
- [Agent D — authority/identity/credentials/network policy #28](../../issues/28)
- [Agent E — evidence/telemetry/replay #29](../../issues/29)
- [Contributor call #42](../../issues/42)

Historical S0 PRs are evidence/history. Current product truth comes from `main`, installed CLI help, canonical docs, tests, and exact accepted evidence.

## Multi-agent delivery loop

A–E keep specialist homes but rotate per change through:

```text
External User → Finder → Planner → Fixer → Challenger → Merge Decider → main → post-merge verification
```

Hard rule: **Fixer != Merge Decider**. Security/release-critical changes prefer a separate Challenger. Same-account role separation is useful technical evidence but is not represented as formal verified-principal independence.

See [`docs/operations/closed-loop-agent-delivery.md`](docs/operations/closed-loop-agent-delivery.md).

## External Verifier

[`docs/testing/external-agent-verification.md`](docs/testing/external-agent-verification.md) defines the clean-perspective lane: use only public surfaces, do not fill gaps from private project memory, separate environment limitations from project defects, and verify installed doctor + verify behavior from outside the source tree where possible.

The External Verifier is a perspective, not an approval authority.

## Contributing

Useful contributions include one reproducible false-PASS, one RED regression, one primary-source-backed runtime semantic correction, one safe probe/collector adapter, one authority-confusion case, one telemetry/cleanup/replay oracle, one real cross-backend semantic mismatch, or one first-run/agent-discoverability improvement.

Builders and breakers are equally useful. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [Contributor call #42](../../issues/42).

## Safety boundary

Do not run kernel/runtime escape exploits on ordinary CI or a developer host, commit or publish real credentials/secrets, treat provider marketing/configuration as verification, publish actionable third-party vulnerabilities before responsible-disclosure readiness, weaken tests/evidence gates to obtain green CI, or claim a backend is certified before real execution evidence and independent review support it.

Destructive sandbox-escape work belongs only in explicitly nested, disposable, bounded environments.

## Growth Pack and public claims

AgentCI preserves the evidence-to-distribution loop. Canonical research/Growth Artifacts live under:

```text
.company/research/findings/<artifact-id>/
  facts.json
  evidence.md
  sources.json
```

Open-source recruitment can happen early. Public numeric, performance, adoption, provider-security, and certification claims must remain traceable to canonical evidence and the corresponding gates.

## Repository architecture

```text
src/agentci/                 installed CLI + deterministic evals + sandbox doctor/verify
schemas/                     sandbox certification/authority contracts
scripts/                     canonical evidence validator/attestation + growth tooling
examples/sandbox/            canonical TestCases and synthetic evidence controls
skills/                      reusable agent-facing operating/product skills
docs/architecture/           sandbox/harness architecture contracts
docs/operations/             closed-loop delivery and governance
.company/                    research, strategy, evidence and growth policy
.github/                     CI, issue and PR contracts
tests/                       regression, adversarial and installed-E2E tests
llms.txt                     compact public agent discovery entry point
AGENTS.md                    project-wide agent/skill router
```
