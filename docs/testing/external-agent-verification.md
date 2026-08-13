# External Agent / Developer Verification

Status: active public verification lane. This lane simulates a clean external developer or external agent and is **not** an independent GitHub identity, a replacement for Agent B, or a certification authority.

## Purpose

AgentCI should be understandable, runnable, falsifiable, and contributable by someone who has no private project memory. Internal agents can miss problems because they already know the intended architecture. The External Verifier deliberately starts from public surfaces only and asks what an unknown developer/agent would actually infer.

The lane is especially useful for finding stale/contradictory public contracts, undocumented setup assumptions, broken first-run or clean-wheel paths, machine-discovery gaps, design-stage capabilities that look released, unreproducible evidence, false-PASS paths, and contribution routes that require hidden context.

## Clean-perspective rule

Read public surfaces in this order when available:

1. `README.md`;
2. `llms.txt`;
3. `AGENTS.md`;
4. `CONTRIBUTING.md`;
5. installed CLI help and machine-readable outputs;
6. linked architecture / issue / PR evidence.

Do not use private conversation memory to fill a public documentation gap. If a correct answer requires hidden context, that is itself a discoverability defect.

## AgentCI 0.2 clean-product check

AgentCI 0.2 is a **pre-alpha Developer Preview / not a security certification**. For a release/installation claim, prefer a built wheel installed into a fresh environment and invoked from a working directory outside the repository.

At minimum verify:

```bash
agentci --help
agentci sandbox --help
agentci sandbox doctor --json
agentci sandbox verify /path/to/v0alpha1-red-control-evidence.json --json --print-digest
```

Required outsider conclusions:

- `doctor` may report installed/missing/unverified candidates but default discovery/version probes cannot turn a backend into a security verdict;
- readiness is not backend execution, isolation proof, or security certification;
- `sandbox verify` works from the installed wheel without the source repository as current working directory;
- the permissive red control is **valid evidence** with `recorded_verdict=FAIL`, `expected_verdict=FAIL`, and `certification_claim=false`;
- valid evidence does not mean PASS;
- malformed/tampered evidence is rejected rather than normalized into PASS;
- unavailable material capability or evidence remains `UNVERIFIED`/non-PASS.

If an installed package cannot locate its canonical schema/TestCase/attestation resources outside the source tree, treat that as a product/packaging defect, not a documentation caveat.

## Clone/API fallback

When normal `git clone` / clean checkout is unavailable, use public repository/file APIs where possible and report `UNVERIFIED` for execution-dependent checks that cannot be run. DNS/network failure is an environment limitation unless the product itself caused it.

## Verification loop

```text
public entry point
→ falsifiable outsider claim
→ exact reproduction
→ RED regression when repository behavior is wrong
→ smallest correction
→ exact GREEN head
→ CI / installed-path evidence
→ handoff to Agent B / owning role when security semantics are involved
→ record remaining UNVERIFIED
```

Do not self-certify because the External Verifier authored a fix.

## Routing

- **Agent A** — canonical product/schema/probe implementation and public product behavior;
- **Agent B** — adversarial falsification and security/certification claims;
- **Agent C** — isolation/runtime enforcement semantics;
- **Agent D** — authority/identity/credentials/network policy;
- **Agent E** — evidence/telemetry/replay/cleanup semantics;
- **Supervisor** — stage gates, conflicts, WIP, and final program decisions.

The External Verifier is a perspective/lane, not a seventh authority role.

## What counts as a useful finding

Prefer small, reproducible findings: one stale statement, one clean-install command failure, one missing discovery link, one contradictory stage/role description, one unsupported public claim, one safe false-PASS mutation, or one hidden environment/backend assumption.

For code/behavioral fixes use RED→GREEN. For important documentation contracts, add a repository test so the drift cannot silently return.

## Safety and claim boundaries

- External-verifier output is observation, not authority.
- It cannot grant privileges or approve privilege expansion.
- It cannot replace B's Spec + Standards review.
- It cannot call a sandbox/provider certified or secure without normal evidence gates.
- Destructive escape testing remains limited to explicitly nested, disposable, bounded environments.
- Do not publish actionable third-party vulnerabilities before responsible-disclosure readiness.
- Do not place real secrets in fixtures, logs, issues, or artifacts.

## Verification log

### EXT-2026-08-12-001 — public role-routing drift

**Tested public main:** `d49a038cdc5391d8e2a8e9eddd3a1f382dc80c55`.

**Clean acquisition attempt:** normal clone failed because the verifier runtime could not resolve `github.com`; classified as an environment limitation, while public API/text checks continued.

**Finding:** public role/routing surfaces still exposed an obsolete two-agent model after the Sandbox Program expanded.

**RED:** PR #43 head `f4e515b909f09f99a61615471ab01595c7382033`; CI `31553785950` failed exactly the repository-contract regression.

**Historical limitation:** that verifier runtime could not perform a clean local install. AgentCI 0.2 now makes clean-wheel doctor + verify an explicit CI/release requirement; future verifier runs should use it whenever the environment can build/install the wheel.
