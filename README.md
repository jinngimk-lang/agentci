# AgentCI 0.2 Developer Preview

AgentCI is an evidence-first toolkit for deterministic AI-agent regression testing and provider-neutral sandbox evidence verification.

**AgentCI 0.2 is a pre-alpha Developer Preview / not a security certification.** No sandbox backend is currently claimed as certified or secure by AgentCI.

The project now exposes three installed workflows:

```bash
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

## What AgentCI proves — and what it does not

The Sandbox Program asks:

> A sandbox says an AI agent is contained. How do we prove the effective boundary actually holds?

The working thesis is provider-neutral:

> Sandbox providers build the cage. AgentCI verifies evidence about what the cage actually constrained.

That does **not** mean a backend name, isolation class, configuration file, installed executable, or successful discovery probe is a security verdict. Missing material evidence remains `UNVERIFIED`, not PASS.

## 5-minute quickstart

Requirements: Python 3.11+.

For development:

```bash
python -m pip install -e '.[dev]'
```

### 1. Run deterministic agent regression checks

```bash
agentci test examples/evals.yaml
```

Evidence is written to:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

Eval exit semantics: `0` passed, `1` evaluated with a regression/failure, `2` invalid input/configuration/runtime usage.

### 2. Inspect local sandbox readiness

```bash
agentci sandbox doctor --json
```

`doctor` uses bounded, non-destructive discovery. Default Docker, Podman, bubblewrap, WSL, and Windows Sandbox discovery/version/status probes do not prove a usable runtime route and cannot make those backends certified or secure by themselves.

Readiness is not backend execution, isolation proof, or security certification.

### 3. Validate canonical sandbox evidence

```bash
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

The shipped red control deliberately represents a containment failure. A correct result is conceptually:

```text
valid=true
recorded_verdict=FAIL
expected_verdict=FAIL
certification_claim=false
```

This distinction is central: **valid evidence is not PASS and is not a security certification.** A valid EvidenceEnvelope may correctly prove `FAIL`, `UNVERIFIED`, `PARTIAL`, or `PASS` according to the canonical contract.

Sandbox verify exit semantics:

- `0` — EvidenceEnvelope is valid; inspect `recorded_verdict` separately;
- `1` — evidence is invalid, inconsistent, tampered, or cannot satisfy the contract;
- `2` — usage or I/O error.

See [`docs/releases/0.2.0-developer-preview.md`](docs/releases/0.2.0-developer-preview.md) for the exact release boundary.

## Sandbox contract

The reconciled S0 line models, among other dimensions:

- desired policy vs configured/selected/attached/effective state;
- immutable policy and authority epochs;
- workload identity and policy attachment provenance;
- exact assertion/evidence and probe-execution binding;
- channel-specific network evidence rather than generic “network allowed/blocked” inference;
- authorized utility as a separate proof obligation;
- telemetry health/completeness and immutable TestCase identity;
- cleanup, residue, lifecycle and recovery evidence;
- runtime/environment and execution-ordering attestation fixtures;
- fail-closed authority expansion semantics.

Hard boundaries remain: observation is not authority; behavioral outcome is not automatically Decision→enforcement causation; backend/isolation class is descriptive provenance rather than a verdict.

## Clean-wheel product gate

CI builds a wheel, installs it into a fresh virtual environment, changes to a working directory outside the repository, then runs both:

```bash
agentci sandbox doctor --json
agentci sandbox verify /path/to/v0alpha1-red-control-evidence.json --json --print-digest
```

The wheel ships the same canonical validator code and repository-owned schema/TestCase/fixture-attestation data; it does not maintain a second sandbox IR.

## For AI agents

Start with public, cheap discovery:

```text
llms.txt
skills/agentci/SKILL.md
agentci --help
agentci sandbox --help
```

Canonical agent surfaces:

- [`llms.txt`](llms.txt)
- [`AGENTS.md`](AGENTS.md)
- [`skills/agentci/SKILL.md`](skills/agentci/SKILL.md)
- [`docs/testing/external-agent-verification.md`](docs/testing/external-agent-verification.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

Agent-facing metadata must describe real installed behavior. Do not guess optional commands from design documents.

## Sandbox Program and contribution

The active provider-neutral program is coordinated through:

- [Program / Supervisor #24](../../issues/24)
- [A — product contract/probes #25](../../issues/25)
- [B — adversarial falsification #26](../../issues/26)
- [C — isolation/runtime #27](../../issues/27)
- [D — authority/identity/credentials/network #28](../../issues/28)
- [E — evidence/telemetry/replay #29](../../issues/29)
- [Contributor call #42](../../issues/42)

A useful contribution can be one reproducible false-PASS, one RED regression, one primary-source-backed runtime semantic mapping, one safe collector/probe adapter, one authority/evidence correction, or one clean-install/onboarding defect.

Do not run kernel/runtime escape exploits on ordinary CI or a normal developer host, do not submit real secrets, and do not publish actionable third-party vulnerabilities before responsible-disclosure readiness.

## Operating model

Repository-visible closed-loop delivery lives in [`docs/operations/closed-loop-agent-delivery.md`](docs/operations/closed-loop-agent-delivery.md). The project uses falsifiable claims, RED→GREEN implementation, role-separated challenge for material changes, exact-head merge decisions, and post-merge verification. Same-account role labels are useful technical separation but are not represented as formal verified-principal independence.

## Growth and public evidence

Canonical research/Growth Artifacts live under:

```text
.company/research/findings/<artifact-id>/
├── facts.json
├── evidence.md
└── sources.json
```

Public numeric/security claims must match structured evidence and applicable repository gates. Experimental recruitment may describe exact evidence and limitations; it may not turn a Developer Preview into a backend certification claim.

## Current limitations

AgentCI 0.2 does not claim a production sandbox runtime, hosted dashboard, provider-native attestation service, production key custody/rotation, automated privilege expansion, provider ranking, or cross-provider security superiority. Real backend support remains evidence-driven: if a capability or observer cannot be proven in the current environment, AgentCI reports the corresponding dimension as unavailable/`UNVERIFIED` rather than inferring PASS.
