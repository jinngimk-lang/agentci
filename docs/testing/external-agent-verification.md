# External Agent / Developer Verification

Status: active public verification lane. This lane simulates a clean external developer or external agent and is **not** an independent GitHub identity, a replacement for Agent B, or a certification authority.

## Purpose

AgentCI should be understandable, runnable, falsifiable, and contributable by someone who has no private project memory. Internal agents can miss problems because they already know the intended architecture. The External Verifier deliberately starts from public surfaces only and asks what an unknown developer/agent would actually infer.

The lane is especially useful for finding:

- stale or contradictory README / `llms.txt` / `AGENTS.md` / CLI-help contracts;
- undocumented setup assumptions;
- broken first-run or clean-wheel paths;
- machine-discovery gaps;
- design-stage capabilities that look released;
- evidence that cannot be reproduced from public instructions;
- false-PASS or false-confidence paths visible to a clean consumer;
- contribution routes that require hidden project context.

## Clean-perspective rule

For each verification cycle, behave as if you know nothing beyond the public repository state being tested.

Read in this order when available:

1. `README.md` for human-facing orientation;
2. `llms.txt` for cheap machine discovery;
3. `AGENTS.md` for agent routing;
4. `CONTRIBUTING.md` for contribution workflow;
5. installed CLI help and public machine-readable outputs;
6. only then follow linked architecture / issue / PR evidence.

Do not use private conversation memory to fill a public documentation gap. If a correct answer requires hidden context, that is itself a discoverability defect.

## AgentCI 0.2 clean-product check

AgentCI 0.2 is a **pre-alpha Developer Preview / not a security certification**. For a release/installation claim, the preferred clean-room check is a built wheel installed into a fresh environment and invoked from a working directory outside the repository.

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
- `sandbox verify` must be available from the installed wheel without depending on the current working directory being the source repository;
- the canonical permissive red control must be **valid evidence** with `recorded_verdict=FAIL`, `expected_verdict=FAIL`, and `certification_claim=false`;
- valid evidence does not mean PASS;
- malformed/tampered evidence is rejected rather than normalized into PASS;
- unavailable material capability or evidence remains `UNVERIFIED`/non-PASS.

If an installed package cannot locate its canonical schema/TestCase/attestation resources outside the source tree, that is a product/packaging defect, not an acceptable documentation caveat.

## Clone/API fallback

A clean agent may not always have working GitHub DNS or a git client. Verification should distinguish environment failure from project failure.

Preferred acquisition order:

1. normal `git clone` / clean checkout when available;
2. GitHub repository/file API or equivalent public text retrieval when clone is unavailable;
3. report `UNVERIFIED` for checks that require local execution but cannot be performed.

A DNS/network failure must not be mislabeled as an AgentCI defect. It should be recorded as an environment limitation together with which public checks remained possible.

## Verification loop

Use the same evidence discipline as the rest of AgentCI:

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

Do not self-certify merely because the External Verifier authored the fix.

## Routing

External findings are routed by domain:

- **Agent A** — canonical product/schema/probe implementation and public product behavior;
- **Agent B** — independent falsification and security/certification claims;
- **Agent C** — isolation/runtime enforcement semantics;
- **Agent D** — authority/identity/credentials/network policy;
- **Agent E** — evidence/telemetry/replay/cleanup semantics;
- **Supervisor** — stage gates, conflicts, WIP, and final program decisions.

The External Verifier is a perspective/lane, not a seventh authority role.

## What counts as a useful finding

Prefer small, reproducible findings:

- one stale public statement;
- one command that fails from a clean checkout or wheel;
- one missing machine-discovery link;
- one contradictory role or stage description;
- one public claim that cannot be traced to evidence;
- one safe adversarial input that produces a false-PASS;
- one environment/backend assumption that should be explicit.

For code or behavioral fixes, use RED→GREEN. For pure documentation corrections, add a repository-contract test when the drift is important enough to regress.

## Safety and claim boundaries

- External-verifier output is observation, not authority.
- It cannot grant privileges or approve privilege expansion.
- It cannot replace B's Spec + Standards review.
- It cannot call a sandbox/provider certified or secure without the normal AgentCI evidence gates.
- Destructive escape testing remains limited to explicitly nested, disposable, bounded environments.
- Do not publish actionable third-party vulnerabilities before responsible-disclosure readiness.
- Do not place real secrets in fixtures, logs, issues, or artifacts.

## Verification log

### EXT-2026-08-12-001 — public role-routing drift

**Tested public main:** `d49a038cdc5391d8e2a8e9eddd3a1f382dc80c55`.

**Clean acquisition attempt:** normal `git clone https://github.com/jinngimk-lang/agentci` failed in the verifier runtime because `github.com` DNS could not resolve. Classified as an environment limitation, not an AgentCI product defect. Public GitHub API/file retrieval remained available, so documentation/discovery checks continued.

**Finding:** README already described the active Sandbox Program and linked specialist work, but still contained the legacy heading `The two-agent operating loop`; `AGENTS.md` formally routed only A, B, and Supervisor and did not route C/D/E or a clean external-verification lane. A new external agent could therefore infer an obsolete coordination model.

**RED:** PR #43 head `f4e515b909f09f99a61615471ab01595c7382033`; GitHub CI run `31553785950` failed exactly at `test_public_agent_surfaces_route_current_sandbox_roles_and_external_verifier` with `1 failed, 51 passed`.

**Required correction:** synchronize README, `AGENTS.md`, and `llms.txt`; preserve C/D/E ownership; expose this verification protocol; make clear that External Verifier is a clean-perspective lane rather than independent review authority.

**Historical limitation:** local clean-install/CLI execution was unavailable in that verifier runtime. AgentCI 0.2 subsequently makes clean-wheel doctor + verify an explicit CI/release requirement; future verifier runs should use it whenever the environment can build/install the wheel.
