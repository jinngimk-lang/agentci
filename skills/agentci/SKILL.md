---
name: agentci
description: Use when evaluating AI-agent behavior, executable targets, reproducible regressions, sandbox readiness, canonical sandbox evidence, or truth-bounded AgentCI showcase discovery.
---

# AgentCI Skill

## Current product truth

AgentCI is an evidence-first reliability, regression-testing, and sandbox-verification project.

The released 0.2 Developer Preview / Sandbox Alpha exposes:

```bash
agentci test <eval-suite>
agentci sandbox doctor [--json]
agentci sandbox verify <evidence.json> [--json] [--print-digest] [--receipt <output.json> --receipt-bundle <bundle-dir>]
```

Do not infer additional sandbox commands from architecture documents. Future `inspect/test/certify/replay` roadmap surfaces remain design-stage/experimental unless the installed CLI exposes them.

No backend is currently certified by AgentCI.

### Main-only development surfaces

Development after `v0.2.0` is versioned `0.3.0.dev0`.

It includes a truth-checked showcase discovery surface:

```bash
agentci showcase list
agentci showcase list --json
agentci showcase show <id>
agentci showcase show <id> --json
```

Showcase entries expose evidence maturity, the current represented CLI command, local repository paths where applicable, and a claim boundary. The catalog is discovery metadata only: it does not execute a backend, create a second verdict engine, or certify a sandbox. Fixture entries cannot claim certification. Source checkouts and installed wheels load the same canonical catalog bytes.

Development also contains the first S1 falsifiable route gate, `S1-EXEC-ROUTE-001`. It compares a signature-authenticated completed execution observation with an exact provider-neutral contract and attempt binding. Signatures are verified against verifier-supplied pinned authority/key/epoch policy; the default trust policy is empty, so caller-asserted trust fails closed. Missing, ambiguous, stale, fallback, degraded, context-mismatched, or route-mismatched evidence remains `UNVERIFIED`.

**ELIGIBLE is not PASS.** The S1 gate only allows later semantic evidence evaluation to continue. It does not execute a backend and exposes no backend verdict, isolation, containment, security, or certification field. There is no S1 execution CLI. S1 remains UNVERIFIED until the same semantic suite has externally observed evidence from at least two materially different real backends.

Use `docs/architecture/s1-execution-route-binding.md` for the contract boundary and `src/agentci/sandbox/execution_route.py` for the development API. Do not infer backend execution from the presence of these schemas.

## When to use

Use AgentCI to:

- run deterministic AI-agent eval/regression checks;
- produce machine-readable CI evidence;
- inspect local sandbox backend **readiness** without claiming security;
- validate a canonical sandbox `EvidenceEnvelope` without conflating evidence validity with PASS;
- discover current AgentCI capabilities/fixtures and their evidence maturity from a canonical catalog;
- reproduce reliability/evidence failures;
- work on provider-neutral sandbox authority, runtime, telemetry, replay, or adversarial verification.

Do not use AgentCI as a generic chat/model/browser service or as a sandbox runtime by itself.

## Install / first useful calls

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci --help
agentci test examples/evals.yaml
agentci sandbox doctor --json
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
agentci showcase list --json
```

`showcase` is a main-only `0.3.0.dev0` surface until a later release includes it; do not attribute it to `v0.2.0`.

## Showcase discovery

Use `agentci showcase list` when the first question is “what canonical cases or current capabilities can this checkout truthfully represent?” Use `--json` for machine routing.

Use `agentci showcase show <id>` to inspect one entry's maturity, represented command, repository path when present, and claim boundary.

Do not reinterpret:

- catalog presence as execution evidence;
- `released-capability` maturity as a backend security result;
- `fixture` maturity as provider-native execution or certification;
- a represented command as proof that its outcome will be PASS.

The catalog is intentionally small until entries can satisfy repository-path, unique-ID, CLI-surface, packaging, and claim-boundary contracts.

## Sandbox doctor

`agentci sandbox doctor` is readiness/discovery only.

Truth boundary:

- readiness is **not backend execution**;
- readiness is **not isolation proof**;
- readiness is **not a security certification**;
- installed binaries or successful version/status calls do not by themselves prove a usable runtime route;
- timeout/error/missing/unknown configuration remains explicit rather than becoming ready.

## Sandbox verify

`agentci sandbox verify` validates one canonical S0 `EvidenceEnvelope` using the same fail-closed validator semantics as the repository evidence core.

Critical distinction:

> **Valid evidence is not PASS and is not a security certification.**

Always inspect:

```text
valid
recorded_verdict
expected_verdict
errors
artifact_digest (when requested)
```

The canonical permissive red-control fixture is intentionally expected to be a **valid evidence envelope whose recorded and expected verdict are `FAIL`**. A verifier exit code of `0` means the envelope is valid under the contract; it does not mean a sandbox passed. Tampered/invalid evidence returns non-zero.

The installed verifier ships wheel-safe copies of canonical schema/TestCase/attestation resources and delegates verdict semantics to one canonical validator; do not create a second, divergent verdict engine.

### Strict fixture receipt profile

The released verifier can optionally bind canonical evidence to an explicit signed fixture observer/cleanup bundle:

```bash
agentci sandbox verify examples/sandbox/v0alpha1-pass-evidence.json \
  --receipt verification-receipt.json \
  --receipt-bundle examples/sandbox/receipt-bundles/pass-sensitive-read-denied-001 \
  --json
```

`--receipt-bundle` requires `--receipt`. The bundle is loaded explicitly and non-recursively. Trust roots are verifier-pinned; keys supplied by the bundle or receipt are not authoritative. The resulting content-addressed receipt is a **fixture binding manifest** for deterministic manifest revalidation; it is not provider execution proof, provider-native attestation, independent identity, or a security certification. `certification_claim` is always `false`.

`Replay` here means deterministic revalidation of the self-contained fixture-binding manifest. It does not rerun a sandbox, provider, workload, or external observer. No `agentci sandbox replay` command is released.

## Active Agent Sandbox Certification program

Primary strategic line: provider-neutral **Agent Sandbox Certification** and longer-term Verified Execution.

Current state: **Sandbox Alpha / Developer Preview with canonical S0 evidence core; real matched cross-backend certification remains experimental/UNVERIFIED.**

Canonical routing:

- program/stage decisions → #24;
- Agent A product/schema/probe integration → #25;
- Agent B independent red team / Spec + Standards → #26;
- Agent C isolation/runtime semantics → #27;
- Agent D authority/identity/credentials/network policy → #28;
- Agent E evidence/telemetry/replay/cleanup → #29;
- contributor call → #42;
- sandbox skill → `skills/sandbox-research-certification/SKILL.md`;
- S0 integration → `docs/architecture/sandbox-s0-v0alpha1-integration.md`;
- architecture boundary → `docs/architecture/sandbox-certification-contract.md`.

Historical draft PRs are evidence/history, not the current product entry point.

## Sandbox invariants

Preserve:

- **Observation != Authority**;
- configured/present != selected/attached/effective/verified;
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

Important semantics include separate `PolicySpec` / `Observation` / `TestCase` / `EvidenceEnvelope`; policy epochs; configured/selected/attached/effective distinction; independent runtime/backend/environment provenance; unique effective attachment per workload/policy epoch; exact execution binding; signed causal ordering; mandatory telemetry; authorized utility; cleanup state; and fail-closed malformed/missing/stale/ambiguous evidence.

This evidence core plus `sandbox verify` validates evidence. It does **not** certify a provider.

## Progressive discovery

Start with:

```text
llms.txt
AGENTS.md
agentci --help
agentci showcase list --json
```

Then load only what the task needs:

- one current capability/fixture → `agentci showcase show <id> --json`;
- sandbox research/certification → `skills/sandbox-research-certification/SKILL.md`;
- readiness/backend discovery → `skills/capability-routing-reach/SKILL.md`;
- closed-loop engineering → `docs/operations/closed-loop-agent-delivery.md`;
- external clean-perspective testing → `docs/testing/external-agent-verification.md`;
- major category reframing → `skills/category-reframing-constraint-deletion/SKILL.md`;
- growth/public claims → `.company/growth/rules.yaml`.

Installed CLI behavior outranks future design prose when deciding what can actually be invoked.

## Multi-agent delivery discipline

A–E retain specialist homes but may rotate per change through:

```text
External User
Finder
Planner
Fixer
Challenger
Merge Decider
```

Hard rule: `Fixer != Merge Decider`; security-critical changes prefer a distinct Challenger. Use one Fixer/problem, immutable exact-head review, expected-head merge, and post-merge `main` verification. Base/head drift means RETURN/rebuild, not stale merge.

## Evidence discipline

For behavior changes:

1. state one falsifiable claim;
2. RED first when behavior can regress;
3. make the smallest correction;
4. run targeted tests;
5. run full CI plus installed/wheel smoke when shipping a CLI surface;
6. record exact head/evidence;
7. obtain independent falsification when material;
8. verify `main` after merge.

Never weaken a test or convert unknown evidence to success to keep CI green.

## External Verifier

Read `docs/testing/external-agent-verification.md`. A clean external agent/developer must use public surfaces only and classify failures as product defect, environment limitation, external dependency failure, or `UNVERIFIED` condition. Public-doc contradictions, nonexistent-command guesses, stale state, packaging failures, and inability to locate evidence are product/distribution defects.

External Verifier is a perspective lane, not an approval authority or replacement for Agent B.

## Category direction: Verified Execution

Before major roadmap/category changes, read `skills/category-reframing-constraint-deletion/SKILL.md`.

Strategic hypothesis:

```text
intent + authorized utility + forbidden capabilities + limits
→ provider-neutral execution contract
→ deterministic authority validation
→ backend mapping/execution
→ adversarial verification
→ proof-bearing execution receipt
```

Goal: potentially remove provider-specific sandbox configuration burden from the normal developer experience while preserving deterministic authority, enforcement, evidence, and independent verification. This is not yet released backend execution/certification behavior.

## Growth and safety

Recruit contributors early, but make strong security/certification claims late and only from canonical evidence. Never fabricate provider evidence, commit secrets, run destructive escapes on an ordinary host/CI runner, publish actionable third-party vulnerabilities before disclosure readiness, assume readiness implies isolation, or present unreleased design commands as product behavior.
