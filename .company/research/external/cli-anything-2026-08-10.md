# External Signal: HKUDS/CLI-Anything

Date reviewed: 2026-08-10
Source: https://github.com/HKUDS/CLI-Anything
Decision: **adopt selected harness-engineering patterns; do not turn AgentCI into a GUI-to-CLI generator.**

## Why it matters to AgentCI

CLI-Anything treats a command-line harness as the stable, machine-readable boundary between an agent and real software. Its strongest ideas overlap with AgentCI's core problem: if an agent target is not inspectable, deterministic, bounded, reproducible, and tested end-to-end, an eval result is not trustworthy.

The useful strategic move is therefore not to copy CLI-Anything's product. It is to make AgentCI the reliability/evaluation layer that can validate CLI-style agent harnesses and other executable targets.

## Patterns adopted

### 1. Harness-first contract

A target should expose a small, explicit, versioned machine contract instead of relying on ambiguous prose or shell behavior. AgentCI will evolve its local/executable target around a documented Target Harness Contract.

### 2. Inspect before act

CLI-Anything emphasizes probe/info/status commands so agents can understand state before mutation. AgentCI should similarly support cheap target introspection (`doctor`/`info`) before executing a suite, and should make capability discovery machine-readable.

### 3. JSON-first agent interface

Machine-readable output is a first-class requirement. AgentCI already uses structured evidence; future target adapters should negotiate a JSON protocol and preserve human-readable reports as a separate presentation layer.

### 4. Real end-to-end execution

A subprocess returning exit code 0 is not sufficient evidence. Adapter tests should invoke the installed AgentCI CLI and a real executable target, then verify the resulting AgentCI evidence/artifacts. External integration adapters should have dedicated true-backend E2E coverage rather than only mocks.

### 5. Test plan before implementation

For new target adapters, write a small adapter test plan before implementation: contract cases, failure modes, real workflow, resource limits, platform assumptions, and final-output verification. Append actual results after execution.

### 6. Agent-discoverable skill documentation

AgentCI now maintains `skills/agentci/SKILL.md` as a compact entry point. The skill should teach agents how to discover capabilities progressively rather than loading all operational detail at once.

### 7. Trajectory as an append-only evidence object

CLI-Anything's live-preview trajectory idea maps naturally to AgentCI traces. AgentCI should support an optional append-only trajectory/event stream associated with a run, while keeping current result summaries cheap to inspect. This becomes a future foundation for tool-call evals, trace grading, replay, and regression comparison.

### 8. Truthful artifacts

Generated artifacts or traces must reflect the real target execution. AgentCI should not treat a mocked or synthetic artifact as proof of a real integration unless the eval explicitly declares itself synthetic.

## Patterns intentionally NOT adopted

- GUI-to-CLI code generation as a product scope.
- Application-specific rendering/export layers.
- A branded REPL skin as a core requirement.
- Reimplementing third-party software behavior inside AgentCI.
- A general CLI package registry at this stage.
- Visual preview infrastructure unless a future eval type actually needs it.

These would dilute AgentCI's positioning as reliability/eval infrastructure.

## Integration sequence

### H0 — Contract and operating standards (integrated now)
- Target Harness Contract design.
- Target manifest and trajectory schemas.
- AgentCI SKILL.md.
- Adapter test-plan template.

### H1 — Stabilize executable target
- Finish and independently accept the current local-command work and its P1/P2 fixes.
- Do not expand the already-large PR solely to chase this external signal.

### H2 — Harness introspection and conformance
- Add a versioned manifest/capability surface.
- Add `agentci target doctor` (or equivalent) to validate executable resolution, protocol compatibility, limits, and machine output.
- Add installed-entrypoint E2E from an arbitrary working directory.

### H3 — Trajectory evidence
- Add optional JSONL trajectory/event ingestion.
- Validate ordering, run identity, size bounds, malformed events, and artifact references.
- Keep summary inspection cheap; do not force full trace loading for every eval.

### H4 — Adapter ecosystem only after demand
- Contract-test reusable adapters.
- Consider a registry/discovery layer only when real adoption shows multiple independently maintained adapters/targets.

## Success criteria

This integration is successful if AgentCI becomes better at answering:

1. Can this agent harness be invoked reliably and safely enough for evaluation?
2. Can another developer reproduce the run through the installed CLI?
3. Can AgentCI inspect target capabilities before execution?
4. Are result/trajectory artifacts structurally trustworthy and bounded?
5. Can regressions be compared without depending on GUI state or undocumented behavior?

The external project is architectural inspiration only; no source code is copied into AgentCI by this decision.