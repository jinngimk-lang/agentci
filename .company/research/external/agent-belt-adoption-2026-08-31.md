# External Adoption Assessment — JFrog agent-belt

Date: 2026-08-31
Project: https://github.com/jfrog/agent-belt
License observed from upstream README: Apache-2.0
Decision mode: pattern adoption only; no dependency/integration claim

## Why this project matters to AgentCI

`agent-belt` evaluates the real agent CLI binary a user runs, supports repeated trials, rule/LLM scoring, bundled scenarios, sandbox routing, and a very cheap `belt quickstart` path. It is adjacent to AgentCI but owns a different layer.

AgentCI should not become another generic agent runner merely because this project exposes useful runtime/eval features. The transferable value is mostly in activation design and evidence-shape discipline.

## Adopt now

### 1. First-minute activation

Upstream pattern:

```text
install
→ doctor / quickstart
→ one real runnable bundled scenario
→ next steps
```

AgentCI response:

- #129 / #130: truth-checked showcase catalog packaged into the wheel;
- #131 / #132: `agentci init` generates a deterministic starter config and prints the exact `agentci test` next command;
- clean-wheel CI must exercise the starter flow from an unrelated working directory.

This is adoption of a product pattern, not source-code copying.

### 2. Bundled runnable discovery assets

`agent-belt` makes its showcase available from an installed wheel, not only a source clone. AgentCI should preserve the same property for canonical discovery/evidence assets while keeping one source of truth.

Current AgentCI direction already matches this: the showcase catalog and sandbox resources are installed from canonical repository bytes and clean-wheel tests verify the installed fallback.

## Experiment next

### Execution-result binding

`agent-belt` issue #9 proposes a deterministic post-turn/post-scenario `verify` command. The important AgentCI question is not whether AgentCI should execute such commands itself. It is whether evidence from an external runner can prove exactly **what artifact/tree and execution boundary the verification command actually checked**.

A future provider-neutral fixture should consider binding:

- scenario/run/attempt identity;
- immutable starting workspace/tree digest;
- immutable post-agent workspace/tree digest;
- exact verifier argv + timeout + environment policy;
- route/sandbox identity used for verification;
- verifier exit code and bounded output digest;
- whether verifier and actor shared filesystem/process/network authority;
- terminal/cleanup state;
- explicit claim boundary such as `functional check passed`, not `agent/sandbox certified`.

Do not add this to canonical schemas until a real external artifact or contributor case justifies a falsifiable RED.

## Watch

### Repeated trials / pass^k / paraphrase families

These are valuable for stochastic behavioral reliability. AgentCI currently has a stronger need to keep deterministic evidence validation and sandbox truth boundaries simple.

Watch for a concrete user request or external artifact showing that AgentCI itself must aggregate stochastic trial reliability. Until then, treat pass^k as upstream benchmark evidence that AgentCI may verify, not a required core runner feature.

### Multi-judge consensus

Multiple independent judges can reduce single-judge variance, but LLM judge consensus is still observational evidence. It must not become AgentCI authority by vote count.

If consumed later, preserve each judge identity/output and the aggregation rule rather than storing only the consensus result.

## Reject / not core

### Becoming a black-box CLI agent runner

`agent-belt` already owns this product category well. AgentCI's differentiation is independent evidence/authority/route verification and false-PASS rejection.

Do not duplicate:

- generic agent subprocess adapters;
- provider/model judge plumbing;
- a full scenario runner merely for breadth;
- generic TUI/view surfaces unless first-success/evidence interpretation requires them.

### Treating functional test PASS as security evidence

A post-agent `pytest`/build command can prove useful functionality for the exact tested artifact. It cannot prove isolation, containment, credential safety, cleanup, or backend security.

## Promotion / relationship boundary

A targeted technical comment was attempted on `jfrog/agent-belt#9`, proposing evidence-binding fields for deterministic verify artifacts. The connected GitHub integration returned HTTP 403, so this is **not** counted as external outreach and should not be retried merely for volume.

No AgentCI ↔ agent-belt compatibility, endorsement, integration, or adoption is claimed.

## Revisit trigger

Revisit this assessment when one of these becomes true:

1. an external runner contributes a real execution/verify artifact to AgentCI;
2. an AgentCI user requests stochastic trial aggregation rather than deterministic verification;
3. agent-belt exposes a stable external artifact schema that can be verified without importing its runtime;
4. a shared false-PASS case demonstrates that tree/route/verification binding is missing from AgentCI's current evidence model.
