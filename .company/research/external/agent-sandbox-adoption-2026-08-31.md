# Agent sandbox/runtime adoption scan — 2026-08-31

Purpose: compare current public agent-execution projects with AgentCI's evidence-first boundary and record only transferable patterns. External projects are evidence inputs, not authorities over AgentCI claims.

## Sources inspected

| Project | Primary source | Transferable pattern | AgentCI decision |
| --- | --- | --- | --- |
| SWE-ReX | https://github.com/SWE-agent/SWE-ReX | One stable runtime interface across materially different local/cloud deployment backends; agent logic is separated from execution infrastructure. | **experiment** — use as a comparison target for a minimal provider-neutral AgentCI execution adapter, not as a core dependency. |
| Kubernetes SIGs Agent Sandbox | https://github.com/kubernetes-sigs/agent-sandbox | Explicit lifecycle resources (`Sandbox`, templates/claims/warm pools) and quickstarts that distinguish basic execution from stronger gVisor/Kata isolation. | **adopt-now** for contribution vocabulary: require backend/runtime class, exact environment, lifecycle and independently observed evidence in intake. **watch** warm-pool orchestration until AgentCI executes real backends. |
| Docker Sandboxes | https://docs.docker.com/ai/sandboxes/ | First-run UX makes workspace scope, network policy, credentials and teardown visible instead of hiding them behind a generic “sandbox” label. | **adopt-now** in evidence intake: require workspace/filesystem, network, credential and cleanup boundaries. Do not inherit provider policy semantics as proof. |
| Anthropic Sandbox Runtime | https://github.com/anthropic-experimental/sandbox-runtime | Lightweight OS-native process sandboxing with filesystem and proxy-mediated network restrictions; useful counterpoint to container/microVM backends. | **benchmark/watch** — valuable as a materially different backend class for future cross-backend S1 experiments; no dependency adoption yet. |
| E2B | https://github.com/e2b-dev/E2B | Simple SDK lifecycle for create → execute → collect result, with cloud/self-hosted runtime implementations behind the user-facing API. | **experiment** — useful lifecycle comparison for an AgentCI adapter contract and independent observation hooks; no cloud dependency or paid service assumption. |
| OpenHands Runtime | https://github.com/OpenHands/docs/blob/main/openhands/usage/architecture/runtime.mdx | Action→observation loop is explicit and runtime execution is separated from agent reasoning/event flow. | **benchmark** — compare observation provenance and execution-state semantics; do not treat Docker runtime configuration as verification. |

Retrieved/checked: 2026-08-31 UTC context. Re-check upstream state before making version-specific claims.

## What AgentCI already does differently

AgentCI is intentionally not trying to win by being the fastest sandbox launcher. Its current differentiator is the verification boundary:

- readiness/configuration is not execution proof;
- observation is not authority;
- valid evidence is not PASS;
- exact route binding is only `ELIGIBLE`, never security certification;
- missing material observability remains `UNVERIFIED`;
- public claims must trace to reproducible evidence.

That distinction should be preserved while borrowing activation and adapter patterns from execution projects.

## Current gaps exposed by the comparison

### P1 — Real backend execution remains absent

The `0.3.0.dev0` S1 route-binding gate can decide whether an authenticated observation matches a requested route, but AgentCI still does not launch a real backend. The next meaningful experiment should execute the same bounded semantic suite on at least two materially different backend classes and feed independently collected route observations into the existing gate.

Smallest experiment candidates:

1. one local process/container-style backend;
2. one materially different OS-sandbox or microVM-style backend;
3. the same authorized-utility + forbidden-capability cases on both;
4. exact route/build/environment/policy identity plus cleanup evidence;
5. explicit `UNVERIFIED` for any unavailable observer or authority material.

Do **not** graduate a backend because its SDK call succeeds.

### P1 — External contributors need a canonical real-backend intake

The project had generic bug/research/benchmark forms and a sandbox-doctor feedback form, but no issue form tailored to a real backend execution package. That creates unnecessary translation work after a contributor arrives.

**Adopted now:** `.github/ISSUE_TEMPLATE/sandbox-backend-evidence.yml` asks for exact runtime/build, environment/policy, safe reproduction, requested/observed route, machine evidence, semantic cases, cleanup and limitations. The form deliberately treats configuration as context rather than proof.

### P1 — Security reporting was not discoverable at repository root

A verification/security project should not make a reporter guess whether an actionable bypass belongs in a normal public issue.

**Adopted now:** root `SECURITY.md` defines a no-public-exploit boundary, private-reporting preference, synthetic-canary rule and supported project states. Kubernetes Agent Sandbox's explicit security-policy entry point is a useful community-health precedent; AgentCI's policy remains project-specific and evidence-first.

### P2 — S1 examples should become cheaper than architecture reading

After the route-binding contract stabilizes, add a small machine-readable example pack that a clean external agent can parse without reading the architecture document. Keep it development-only until a released CLI/API consumes it. This is an activation improvement, not proof of backend execution.

## Adoption decisions

- `adopt-now`: security reporting entry point; structured real-backend evidence intake; explicit network/filesystem/credential/lifecycle fields in contribution evidence.
- `experiment`: minimal provider-neutral backend adapter + independent observation hook, tested on at least two materially different backends.
- `benchmark`: SWE-ReX/OpenHands lifecycle and observation semantics; Anthropic Sandbox Runtime as an OS-native class; E2B lifecycle API.
- `watch`: warm pools, large-scale orchestration, cloud provisioning, automatic provider selection/fallback.
- `reject for now`: adding a core runtime dependency solely to claim provider support; importing provider “secure” labels as AgentCI verdicts; any adapter that can self-assert its own verifier authority.

## Removal criteria

Remove or revise any adopted intake field/process if it produces ceremony without improving reproducibility, independent observation, safety, or contributor activation. Do not retain process merely because an upstream project uses it.
