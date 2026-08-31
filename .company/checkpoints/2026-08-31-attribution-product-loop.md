# AgentCI Attribution + Product Loop Checkpoint

Date: 2026-08-31
Base main at checkpoint creation: `12c4825b2203f898bcb2ecd25d998e91d2e11183`
Mode: autonomous, evidence-first, reversible, attribution-first

## Why this checkpoint exists

This file is a durable recovery point for long-running product, research, and distribution work. When chat/session context becomes long or unavailable, recover from repository evidence rather than memory.

Recovery order:

1. read latest `main` and recent merged/open PRs;
2. read this checkpoint;
3. read `.company/roadmap.md` and `.company/strategy.md`;
4. read the newest files under `.company/research/external/`;
5. inspect current external outreach threads before posting, to avoid duplicate promotion;
6. continue the smallest evidence-producing loop rather than restarting strategy from scratch.

## Verified acquisition path

The strongest currently verified contributor-acquisition path is not generic promotion. It is a technical upstream issue with a reproducible failure that naturally maps to an AgentCI evidence fixture.

Observed chain:

```text
LangGraph #8582: reproducible Send + UntrackedValue checkpoint/resume fidelity problem
→ context-specific AgentCI comment proposes a portable replay/restore fixture
→ reporter explicitly replies that they want to contribute and asks for the fixture format
→ AgentCI #123 defines a bounded provider-neutral intake contract
→ reporter forks AgentCI
→ reporter opens AgentCI #124 from that fork
→ #124 is independently reviewed/validated and merged
```

Canonical links:

- upstream provenance: https://github.com/langchain-ai/langgraph/issues/8582
- AgentCI intake: https://github.com/jinngimk-lang/agentci/issues/123
- external contribution: https://github.com/jinngimk-lang/agentci/pull/124

This is the current reference funnel for technical outreach because it has downstream contribution evidence. Stars, raw comment count, and similarity of subject matter are weaker signals.

## Attribution-first growth rule

External promotion should begin by asking how a qualified user or contributor would encounter the problem AgentCI solves.

Preferred path:

```text
real framework/runtime failure
→ public issue/reproduction/search path
→ AgentCI contributes a useful falsifiable invariant or fixture shape in that context
→ bounded invitation to preserve the case as portable evidence
→ repository visit/fork/issue/PR
→ independent verification/merge
```

Rules:

- Do not count comments inside `jinngimk-lang/agentci` as external acquisition.
- Do not use a raw outreach quota as the primary objective.
- Do not expand a channel because it is merely adjacent to AI agents/security.
- Before writing externally, check the thread for an existing AgentCI comment and skip duplicates unless there is meaningful new downstream activity to answer.
- Prefer reporters with self-contained reproductions, observable wrong outcomes, and a clear portable invariant.
- Every outreach comment should add technical value before mentioning AgentCI.
- The CTA should be concrete: fixture, validator, reproduction, adapter, or benchmark contribution—not a generic “check out our project.”
- Preserve the upstream issue as canonical provenance and credit the reporter/contributor.
- Disclose affiliation and do not imply target-project compatibility, endorsement, or certification.
- Record downstream evidence when visible: reply, fork, issue, PR, merged contribution, repeat contribution.
- Traffic/referrer data must remain unknown when the connected tooling cannot read it; never infer visits from stars/forks.

## Current channel evidence

### Proven

**LangGraph replay/checkpoint/restore failures**

Why it converts:

- reporters already have a minimal reproduction;
- wrong behavior is often silent and therefore naturally fits AgentCI's evidence-first positioning;
- checkpoint/replay identity can be expressed provider-neutrally;
- the first contribution can be a static fixture + validation test rather than a large integration;
- the reporter receives durable provenance and public credit without needing AgentCI to claim LangGraph compatibility.

Keep expanding this channel selectively around replay fidelity, checkpoint immutability, resume identity, fork isolation, duplicate effects, and restore semantics.

### Promising, not yet proven

**Sandbox/runtime lifecycle and cleanup failures**

Relevant invariants include:

- kill/terminate acknowledgement vs actual residual processes;
- cleanup state vs live sockets/ports/resources;
- pause/resume vs process identity and inventory;
- transport termination vs sandbox lifecycle state;
- resource-limit configuration vs effective enforcement.

New 2026-08-31 targeted outreach:

- E2B #1031: https://github.com/e2b-dev/E2B/issues/1031 — process/port survives auto-pause/resume while `commands.list()` loses management identity. AgentCI comment proposes a portable lifecycle-fidelity fixture that compares pre-pause managed identity and independent port observation with post-resume inventory/effects.
- LangGraph #8748: https://github.com/langchain-ai/langgraph/issues/8748 — live mutable checkpoint containers allow a later superstep to alter an earlier async checkpoint, then replay duplicates work. AgentCI comment proposes immutable snapshot/digest/replay evidence as a provider-neutral fixture.

These are experiments until they produce downstream evidence such as a reporter reply, fork, contribution, or repeat engagement.

## External-product scan: transferable patterns

See `.company/research/external/eval-security-product-patterns-2026-08-31.md` for the detailed scan.

Current synthesis:

- **Promptfoo:** extremely cheap first success (`init → eval → view`) and an obvious local results surface.
- **Inspect AI:** large prebuilt evaluation corpus plus strong AI-agent documentation discovery (`llms.txt` family).
- **AgentDojo:** explicit task-suite × attack × defense benchmark model and public results browsing.
- **MCP Inspector:** one shared inspection core exposed through CLI/TUI/Web and backed by real composable test servers/showcase configs.
- **garak:** enumerated probe catalog, selective execution by category, detailed JSONL run evidence.
- **Sandbox/runtime projects scanned earlier:** strong execution/lifecycle primitives but generally weaker independent proof boundaries than AgentCI; this supports AgentCI's verifier role rather than becoming another launcher.

## Current product gap ordering

### P1 — Activation and showcase corpus

AgentCI's evidence semantics are stronger than its first-mile activation.

The next bounded product work should make it easy to answer, without reading architecture documents:

- What classes of failures can AgentCI verify today?
- Which canonical examples are runnable now?
- What is the one command for this exact case/category?
- What evidence file/result should I expect?
- Is this fixture-only, independently reproduced, or backed by a real external execution observation?

Preferred direction: a tested, machine-readable showcase/fixture catalog generated from or validated against repository truth, with human and agent-readable views. Do not hand-maintain an unverified marketing inventory.

### P1 — Project state consistency

`.company/roadmap.md` must track actual delivered/main-only/experimental state. Avoid old V0/V1 language that makes current sandbox S0/S1 work look absent or implies unreleased capabilities are shipped.

### P1/P2 — Real backend evidence experiment

Continue the previously identified experiment: run the same bounded semantic suite on at least two materially different real backend classes with independently collected route observations. A provider name/configuration is not evidence. Keep results `UNVERIFIED` until the required observations exist.

### P2 — Corpus growth from external failures

Convert successful upstream outreach into reusable provider-neutral fixtures when the reporter/contributor participates or the provenance/licensing boundary is clear. Prefer semantic classes that recur across runtimes:

- replay/restore fidelity;
- duplicate non-idempotent effects;
- cleanup/terminality;
- residual process/socket/resource state;
- execution identity drift;
- policy/authority binding;
- checkpoint/state immutability;
- advertised/configured capability vs effective capability.

### Watch / not now

- hosted dashboards without activation/adoption evidence;
- large provider dependency matrix just to claim integrations;
- provider security/certification badges without independent real execution evidence;
- broad social posting disconnected from a Growth Artifact or attributable user path;
- UI work that does not improve first success, evidence interpretation, or contribution conversion.

## Next loop order

1. Keep external outreach bounded: one or two high-fit, non-duplicate threads per loop.
2. Record replies/forks/issues/PRs as channel evidence; do not infer hidden traffic.
3. Maintain the external project radar and classify transferable patterns as `adopt-now`, `experiment`, `benchmark`, `watch`, or `reject`.
4. Implement the highest-value low-risk gap in a separate testable change—currently the showcase/fixture catalog and first-run discovery path.
5. Independently verify behavior and claim boundaries before merging.
6. Feed validated corpus items back into outreach with a concrete contribution path.
7. Re-read this checkpoint when context grows instead of reconstructing the strategy from chat history.

## Safety / stop boundaries

Continue autonomously for normal reversible repository work and evidence-backed external technical outreach. Stop/escalate for credentials/secrets, spending, legal commitments, destructive/irreversible operations, actionable undisclosed security vulnerabilities, or external publication that would violate platform/community rules.

Do not weaken evidence gates for growth. The durable objective is qualified adoption and better evidence, not visible activity.
