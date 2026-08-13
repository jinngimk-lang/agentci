# AgentCI

AgentCI is an evidence-first CI, reliability, and security-verification project for AI agents and agent-facing execution environments.

The current primary product line is **AgentCI 0.2 Developer Preview / Agent Sandbox Alpha**: a provider-neutral foundation for discovering sandbox readiness, validating canonical sandbox evidence, rejecting false-PASS claims, and building toward independently reproducible cross-backend verification.

> **Sandbox providers build the cage. AgentCI verifies what can actually be proved about the cage.**

AgentCI is open source and intentionally adversarial: builders, runtime experts, security reviewers, and external agents are welcome to contribute reproducible counterexamples and corrections.

## Current delivered Developer Preview

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

Truth boundary:

- **readiness is not backend execution**;
- **readiness is not isolation proof**;
- **readiness is not a security certification**;
- an installed binary or successful version/status probe does not by itself make a backend `ready`;
- unknown configuration or probe failures remain explicit rather than being promoted to success.

### 3. Canonical sandbox evidence verification

```bash
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

`verify` validates one canonical S0 `EvidenceEnvelope` using AgentCI's fail-closed evidence contract.

Critical distinction:

> **Valid evidence is not PASS and is not a security certification.**

The canonical permissive red-control fixture is intentionally expected to be a **valid evidence envelope whose recorded and expected verdict are both `FAIL`**. A verifier exit code of `0` means the evidence envelope is valid under the contract; it does not mean the sandbox passed or is certified. Tampered/invalid evidence returns non-zero.

The installed verifier ships the required canonical schema/TestCase/attestation resources and delegates verdict semantics to the canonical S0 validator rather than maintaining a second verdict engine.

No sandbox backend is currently claimed as certified or secure by AgentCI. Real matched cross-backend execution/certification remains experimental/`UNVERIFIED`.

## Sandbox evidence core on `main`

AgentCI carries the S0 evidence core used to harden future sandbox verification:

- `schemas/sandbox-certification-v0alpha1.schema.json`;
- `schemas/sandbox-authority-v0alpha1.schema.json`;
- `scripts/validate_sandbox_evidence.py`;
- execution/runtime-environment attestation helpers;
- canonical sandbox TestCases and synthetic red-control fixtures;
- regressions for policy epochs, effective attachments, authority/evidence binding, cleanup state, execution causality, backend/environment provenance, and false-PASS mutations.

See [`docs/architecture/sandbox-s0-v0alpha1-integration.md`](docs/architecture/sandbox-s0-v0alpha1-integration.md).

The S0 evidence core plus `sandbox verify` validates evidence; it is **not** a released provider certifier and does not prove a real provider sandbox secure.

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

Core invariants:

- **Observation != Authority**;
- configured/present != selected/attached/effective/verified;
- backend name != security verdict;
- missing material observability = `UNVERIFIED`, not PASS;
- privilege contraction != privilege expansion;
- privilege expansion requires a separate authenticated authority path;
- restore != clean restart;
- execution status != backend verdict;
- deny-everything != useful containment unless authorized utility still succeeds;
- untested material capabilities cannot hide inside PASS.

## Product direction: Verified Execution

AgentCI is exploring a category-level product hypothesis: developers should eventually express an **authorized task outcome and constraints**, rather than manually understand every provider-specific sandbox mechanism.

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

This is a strategic direction, not released backend execution/certification behavior. The project deliberately preserves deterministic enforcement and external authority even if future UX removes provider-specific configuration burden.

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
- `2` — invalid input/configuration/usage/runtime error outside a normal eval assertion.

Sandbox doctor exits successfully when it can produce a readiness report; do not reinterpret process exit as a sandbox security PASS.

Sandbox verify exit semantics:

- `0` — evidence envelope is valid under the canonical contract, regardless of whether its recorded verdict is `PASS`, `FAIL`, `PARTIAL`, or `UNVERIFIED`;
- `1` — evidence is invalid/tampered/inconsistent with the canonical contract;
- `2` — file/usage/IO error.

Again: **valid evidence is not a security certification**.

## For AI agents

Start with public, cheap discovery surfaces:

```text
llms.txt
AGENTS.md
skills/agentci/SKILL.md
agentci --help
agentci test --help
agentci sandbox doctor --help
agentci sandbox verify --help
```

An unfamiliar agent should be able to determine what is actually released, what remains experimental, how to install/run the first useful call, where canonical evidence lives, and which claims remain `UNVERIFIED`.

Do not guess commands from architecture documents. If the installed CLI does not expose a command, treat it as unreleased.

## Active Sandbox Program

Canonical coordination:

- [Program / Supervisor #24](../../issues/24)
- [Agent A — product contract + probes #25](../../issues/25)
- [Agent B — independent red team #26](../../issues/26)
- [Agent C — isolation/runtime semantics #27](../../issues/27)
- [Agent D — authority/identity/credentials/network policy #28](../../issues/28)
- [Agent E — evidence/telemetry/replay #29](../../issues/29)
- [Contributor call #42](../../issues/42)

Historical S0 PRs are evidence/history rather than the current product entry point.

## Multi-agent delivery loop

A–E keep specialist homes but rotate per change through:

```text
External User
→ Finder
→ Planner
→ Fixer
→ Challenger
→ Merge Decider
→ main
→ post-merge verification
```

Hard rule: **Fixer != Merge Decider**. Security-critical changes prefer an independent Challenger as a third role.

See [`docs/operations/closed-loop-agent-delivery.md`](docs/operations/closed-loop-agent-delivery.md).

## External Verifier

[`docs/testing/external-agent-verification.md`](docs/testing/external-agent-verification.md) defines the clean-perspective lane: use only public surfaces, do not fill gaps from private project memory, separate environment limitations from product defects, and turn reproducible problems into evidence-backed fixes.

The External Verifier is a perspective, not an approval authority.

## Contributing

Useful contributions include:

- reproducible false-PASS cases;
- RED regressions;
- primary-source-backed runtime semantic corrections;
- safe probes/collectors;
- authority-confusion cases;
- telemetry/cleanup/replay oracles;
- real cross-backend semantic mismatches;
- packaging/clean-install failures;
- first-run or agent-discoverability improvements.

Builders and breakers are equally useful. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [Contributor call #42](../../issues/42).

## Safety boundary

Do not:

- run kernel/runtime escape exploits on ordinary CI or a developer host;
- commit or publish real credentials/secrets;
- treat provider marketing/configuration as verification;
- publish actionable third-party vulnerabilities before responsible-disclosure readiness;
- weaken tests/evidence gates to obtain green CI;
- claim a backend is certified before real execution evidence and independent review support it.

Destructive sandbox-escape work belongs only in explicitly nested, disposable, bounded environments.

## Growth Pack and publishing boundary

AgentCI preserves the V0 evidence-to-distribution loop. Canonical research/Growth Artifacts live under:

```text
.company/research/findings/<artifact-id>/
  facts.json
  evidence.md
  sources.json
```

Validate one with `scripts/validate_growth_artifact.py`, then generate a draft **Growth Pack** with `scripts/generate_growth_pack.py` only when evidence rules pass.

The repository has **no built-in external social-posting API**. Publishing authorization and human/agent distribution boundaries remain documented in [`.company/growth/publishing-authorization.md`](.company/growth/publishing-authorization.md). Public numeric, performance, adoption, and security claims must remain traceable to canonical evidence.

## GitHub governance

Repository **branch protection** is authoritative. The rotating A–E workflow may decide and merge eligible exact heads under Owner authorization, but it must preserve separation of duties, passing CI, expected-head checks, and post-merge verification. Repository administration and secrets remain outside ordinary change-level authority.

## Repository architecture

```text
src/agentci/                 installed CLI + evals + sandbox doctor/verify adapters
schemas/                     sandbox certification/authority contracts
scripts/                     canonical evidence validator/attestation + growth tooling
examples/sandbox/            canonical TestCases and synthetic evidence controls
skills/                      reusable agent-facing operating/product skills
docs/architecture/           sandbox/harness architecture contracts
docs/operations/             closed-loop delivery and governance
.company/                    research, strategy, evidence and growth policy
.github/                     CI, issue and PR contracts
tests/                       regression, adversarial, installed and repository-contract tests
llms.txt                     compact public agent discovery entry point
AGENTS.md                    project-wide agent/skill router
```

## Evidence and public claims

Canonical public technical claims must trace to reproducible evidence. Recruitment and open research can begin early. Security/certification claims come late, after the corresponding evidence actually exists.
