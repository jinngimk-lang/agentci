# AgentCI

AgentCI is an evidence-first CI, reliability, and security-verification project for AI agents and agent-facing execution environments.

The current primary product line is **Agent Sandbox Alpha**: a provider-neutral foundation for discovering sandbox readiness, expressing sandbox evidence, rejecting false-PASS claims, and building toward independently reproducible cross-backend verification.

> **Sandbox providers build the cage. AgentCI verifies what can actually be proved about the cage.**

AgentCI is open source and intentionally adversarial: builders, runtime experts, security reviewers, and external agents are welcome to contribute reproducible counterexamples and corrections.

## Current delivered Alpha

The current `main` delivers two distinct layers.

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

No sandbox backend is currently claimed as certified or secure by AgentCI.

## Sandbox evidence core on `main`

AgentCI now also carries the design-stage S0 evidence core used to harden future sandbox verification:

- `schemas/sandbox-certification-v0alpha1.schema.json`;
- `schemas/sandbox-authority-v0alpha1.schema.json`;
- `scripts/validate_sandbox_evidence.py`;
- execution/runtime-environment attestation helpers;
- canonical sandbox TestCase and synthetic red-control fixtures;
- regression tests for policy epochs, effective attachments, authority/evidence binding, cleanup state, execution causality, backend/environment provenance, and false-PASS mutations.

The canonical integration description is:

- [`docs/architecture/sandbox-s0-v0alpha1-integration.md`](docs/architecture/sandbox-s0-v0alpha1-integration.md)

This S0 evidence core is **not** a released `agentci sandbox certify` command and is **not** proof that a real provider sandbox is secure. Provider-native execution/certification remains a later evidence gate.

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
- untested material capabilities cannot hide inside PASS.

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

This is a strategic direction, not released behavior. The project deliberately keeps deterministic enforcement and external authority even if future UX removes provider-specific configuration burden.

See [`skills/category-reframing-constraint-deletion/SKILL.md`](skills/category-reframing-constraint-deletion/SKILL.md).

## 5-minute quickstart

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
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

Sandbox doctor exits successfully when it can produce a readiness report; the report itself carries `ready`, `not-ready`, `unverified`, missing, broken, timeout/error, and per-candidate facts. Do not reinterpret a successful doctor process exit as a sandbox security PASS.

## For AI agents

Start with public, cheap discovery surfaces:

```text
llms.txt
AGENTS.md
skills/agentci/SKILL.md
agentci --help
agentci test --help
agentci sandbox doctor --help
```

An unfamiliar agent should be able to determine:

- what is actually released;
- what is still experimental/design-stage;
- how to install and make the first useful call;
- where canonical evidence lives;
- which claims remain `UNVERIFIED`;
- how to contribute a counterexample or fix.

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

The former long-running S0 integration work has been reconciled onto `main`; historical PRs remain evidence/history rather than the current product entry point.

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

[`docs/testing/external-agent-verification.md`](docs/testing/external-agent-verification.md) defines the clean-perspective lane: use only public surfaces, do not fill gaps from private project memory, separate environment limitations from project defects, and turn reproducible problems into evidence-backed fixes.

The External Verifier is a perspective, not an approval authority.

## Contributing

Useful contributions include:

- one reproducible false-PASS;
- one RED regression;
- one primary-source-backed runtime semantic correction;
- one safe probe/collector adapter;
- one authority-confusion case;
- one telemetry/cleanup/replay oracle;
- one real cross-backend semantic mismatch;
- one first-run or agent-discoverability improvement.

Builders and breakers are equally useful. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [Contributor call #42](../../issues/42).

## Safety boundary

Do not:

- run kernel/runtime escape exploits on ordinary CI or a developer host;
- commit or publish real credentials/secrets;
- treat provider marketing/configuration as verification;
- publish actionable third-party vulnerabilities before responsible-disclosure readiness;
- weaken tests or evidence gates to obtain green CI;
- claim a backend is certified before real execution evidence and independent review support it.

Destructive sandbox-escape work belongs only in explicitly nested, disposable, bounded environments.

## Growth Pack and publishing boundary

AgentCI still preserves the V0 evidence-to-distribution loop. Canonical research/Growth Artifacts live under:

```text
.company/research/findings/<artifact-id>/
  facts.json
  evidence.md
  sources.json
```

Validate one with `scripts/validate_growth_artifact.py`, then generate a draft **Growth Pack** with `scripts/generate_growth_pack.py` only when the evidence rules pass.

The repository has **no built-in external social-posting API**. Publishing authorization and human/agent distribution boundaries remain documented in [`.company/growth/publishing-authorization.md`](.company/growth/publishing-authorization.md). Public numeric, performance, adoption, and security claims must remain traceable to canonical evidence.

## GitHub governance

Repository **branch protection** is authoritative. The rotating A–E workflow may decide and merge eligible exact heads under Owner authorization, but it must preserve separation of duties, passing CI, expected-head checks, and post-merge verification. Repository administration and secrets remain outside ordinary change-level authority.

## Repository architecture

```text
src/agentci/                 installed CLI + deterministic evals + sandbox doctor
schemas/                     sandbox certification/authority design contracts
scripts/                     evidence validators/attestation + growth tooling
examples/sandbox/            canonical TestCases and synthetic evidence controls
skills/                      reusable agent-facing operating/product skills
docs/architecture/           sandbox/harness architecture contracts
docs/operations/             closed-loop delivery and governance
.company/                    research, strategy, evidence and growth policy
.github/                     CI, issue and PR contracts
tests/                       regression, adversarial and repository-contract tests
llms.txt                     compact public agent discovery entry point
AGENTS.md                    project-wide agent/skill router
```

## Evidence and public claims

Canonical public technical claims must trace to reproducible evidence. Recruitment and open research can begin early. Security/certification claims come late, after the corresponding evidence actually exists.
