# Roadmap

This roadmap is a truth-bounded product map, not a feature wish list. Keep released behavior, `main`-only experimental behavior, and future experiments separate.

## Delivered / released foundation

- Deterministic fixture eval CLI with canonical JSON/report artifacts.
- GitHub-native CI and repository operating contracts.
- Evidence-gated growth/research workflow.
- Agent-facing discovery through `llms.txt`, `AGENTS.md`, and `skills/agentci/SKILL.md`.
- Agent Sandbox Alpha `doctor` readiness discovery.
- Agent Sandbox Alpha `verify` for canonical S0 evidence envelopes, including fail-closed false-PASS controls and optional strict receipt binding.
- Public contribution/security intake paths for reproducible failures and real-backend evidence.

Released evidence validation is not real backend certification. `doctor` readiness is not proof of isolation or execution.

## Current `main` / pre-release work

- S1 provider-neutral execution contract and route-binding eligibility gate (`0.3.0.dev0` on `main`).
- Authenticated external route observation binding with verifier-pinned trust.
- Replay/restore fidelity fixtures that preserve external provenance without making unsupported provider claims.
- Expanded authority, identity, cleanup, lifecycle, resource, and evidence-boundary regressions.

`ELIGIBLE` is not PASS. Main-only work must not be described as released CLI behavior unless the installed public entrypoint exposes it.

## P1 — Activation + showcase corpus

Make AgentCI's existing evidence value cheap to discover before adding a large capability surface.

Target outcomes:

- a tested, machine-readable catalog of canonical AgentCI examples/fixtures/cases;
- explicit semantic categories such as replay/restore, cleanup/terminality, route/identity binding, authority/policy, resource enforcement, state/serialization integrity, capability drift, and false-PASS controls;
- exact currently released command(s) for each runnable item;
- clear maturity/provenance fields distinguishing fixture validation, upstream report, independent reproduction, and real execution evidence;
- human-readable README/docs entry points and agent-readable discovery built from the same truth;
- first useful success without requiring architecture-document reading.

The catalog must be generated or contract-tested against repository files/CLI behavior. Do not create a marketing-only inventory or a second verdict engine.

## P1 — Attribution-first contributor growth

Use the verified LangGraph #8582 → AgentCI #123 → external PR #124 → merge chain as the reference acquisition funnel.

Expand selectively where users already encounter failures AgentCI can make portable:

- replay/checkpoint/restore fidelity;
- duplicate non-idempotent effects;
- cleanup/terminality and residual resources;
- execution identity / management inventory drift;
- policy/authority/route binding;
- state immutability and persistence corruption.

External promotion must add technical value in context, avoid duplicate comments, disclose affiliation, preserve upstream provenance, and offer a bounded fixture/validator/benchmark contribution path. Raw outreach count is not a roadmap KPI.

See `.company/checkpoints/2026-08-31-attribution-product-loop.md`.

## P1/P2 experiment — real backend evidence

The next meaningful backend experiment is not “support many providers.” It is to run the **same bounded semantic suite** on at least two materially different real backend classes while collecting independently attributable route/execution observations.

Required boundary:

```text
requested contract
→ independently bound route/execution observation
→ semantic evidence
→ fail-closed verdict
```

A provider name, configuration, installed SDK, successful launch, or provider self-report is insufficient. Keep results `UNVERIFIED` when material identity/route/effect evidence is missing.

Prefer optional adapters/sidecars and bounded experiments before any new core runtime dependency.

## P2 — External failure corpus

Grow AgentCI's defensible corpus from reproducible real-world failures and independent contributions.

For each accepted external case preserve:

- canonical upstream provenance and contributor credit;
- the smallest provider-neutral falsifiable claim;
- exact fixture/evidence maturity;
- secret/value exclusion where appropriate;
- accepted outcomes including explicit `UNVERIFIED` when proof is unavailable;
- focused regression validation;
- no compatibility/certification claim unless independently supported.

## P2 — Agent/human discoverability

Continue progressive disclosure rather than duplicating documentation:

```text
README / llms.txt / agent skill
→ showcase catalog / exact first command
→ CLI help / canonical example
→ evidence artifact
→ architecture/testing contract for deeper work
```

The same capability facts and limitations must agree across human and agent surfaces.

## Watch / evidence-gated expansion

These remain legitimate future directions but are not justified by novelty alone:

- provider adapters beyond bounded real-backend experiments;
- broader real traces and model comparisons;
- MCP security scanning/integration surfaces;
- hosted team dashboards/results collaboration;
- Web/TUI visualization over the verifier core;
- ecosystem registries/certification programs.

Graduate them only when user/adoption evidence or a falsifiable research need justifies the added maintenance, dependency, security, and claim surface.

## Not now

- large provider dependency matrices just to advertise integrations;
- security/certification badges based on configuration or fixture-only evidence;
- hosted services before the local first-success path is strong;
- UI that introduces separate verdict semantics;
- vanity corpus counts, vanity outreach counts, or marketing features disconnected from qualified adoption;
- copying adjacent projects' identity instead of adopting independently verified patterns.

## Continuous external intelligence loop

Run continuously as part of normal project operation:

```text
scan relevant projects/issues/research
→ inspect primary evidence + license
→ identify transferable pattern
→ compare with AgentCI baseline
→ classify: adopt-now / experiment / benchmark / watch / reject
→ make the smallest reversible change
→ independently falsify/verify
→ keep/revise/remove
→ record source + outcome
→ update roadmap/checkpoint when direction changes
```

When context becomes long, use the newest `.company/checkpoints/` file and `.company/research/external/` records as the recovery source rather than reconstructing the roadmap from chat memory.
