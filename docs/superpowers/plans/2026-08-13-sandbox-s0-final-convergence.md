# AgentCI Sandbox S0 Final Convergence Plan

> Status: implementation plan for one canonical S0 contract. This is not a provider certification or S1 result.

## Goal

Converge the currently accepted Agent A/B/C/D/E/Supervisor evidence into one canonical, provider-neutral S0 contract and validator on top of `main@8cf023dff1dac5a6b804d67daac1aeb6509bcbca`, while preserving the hard boundary that observation/intelligence never grants authority.

The deliverable is code-complete S0 contract/validation plus an explicit S1 execution boundary. Any environment-, provider-, native-attestation-, or formal-review fact not mechanically evidenced remains `UNVERIFIED`; no backend is called certified.

## Invariants already carried from main

- PolicySpec / Observation / TestCase / EvidenceEnvelope separation.
- immutable policy/authority epochs and per-event binding.
- network capability distinct from enforcement transport.
- fail-closed expansion/lateral/unknown authority deltas.
- canonical mandatory telemetry completeness and source suitability.
- effective policy attachment provenance, identity, ordering, and uniqueness.
- TestCase content binding in the artifact digest.
- runtime/backend/environment external attestation stand-in.
- authenticated exact probe execution provenance and signed causal ordering observations.
- authorized utility required for PASS.

## Final structural corrections

### 1. Typed assertion/probe obligations

Replace implicit owner inference with one canonical `assertion_requirements[]` object per mandatory assertion. Each requirement binds the assertion to the event semantics that can satisfy it:

- `assertion_id`
- `event_type`
- optional exact `network_channel`
- optional `action`
- optional `resource`
- optional `expected_result`

The set of requirement IDs must equal `mandatory_assertions`. PASS evidence must include at least one referenced event matching the requirement. This closes the accepted #53/#56/#58/#60/#63/#65/#68 family without adding more owner-label strings.

### 2. Utility semantics are evidence, not an oracle label

Extend `Event` with typed `action`, `resource`, and `observed_result`. Authorized utility remains a distinct required assertion, but its evidence must match the canonical typed requirement. A generic `utility` event or copied digest cannot prove useful work.

### 3. Lifecycle post-condition truth and snapshot identity

Absorb the accepted #61/#69/#71 lifecycle semantics and close C's remaining snapshot-identity candidate structurally:

- residual network activity or credential residue cannot PASS;
- `lifecycle_state=preserved` cannot PASS in v0alpha1;
- `lifecycle_state=revalidated` requires non-empty `LifecycleContinuity` with advancing restore epoch and safe per-resource states;
- each continuity record binds to exactly one healthy mandatory lifecycle event for the same workload/policy/attachment/restore context;
- lifecycle events carry `snapshot_id`, and it must equal the continuity record's `snapshot_id`.

Unknown/unavailable continuity remains non-PASS.

### 4. Enforcement/observer topology is representable and fail-closed

Add minimal provider-neutral evidence fields rather than inferring from `isolation_class`:

- telemetry `observer_locus = workload | runtime | host | control-plane | external | unverified`;
- telemetry `trust_class = producer-local | independently-authenticated | provider-native | unverified`;
- backend `enforcement_topology[]` entries with `capability_domain`, `locus`, `mechanism_class`, and `state`;
- TestCase optional `required_enforcement_domains[]`.

A PASS for a required domain needs one non-`unverified` topology entry. These fields describe evidence/topology; they do not grant authority and they do not rank providers.

## Test sequence

1. Add RED regressions for typed assertion obligation mismatch, generic utility substitution, residual post-conditions, empty/unbound lifecycle revalidation, and snapshot substitution.
2. Extend schema/fixture so the canonical sensitive-canary case explicitly states its typed requirements.
3. Implement validator checks with fail-closed semantics.
4. Run GitHub CI and AgentCI Regression on one exact head.
5. Independent B-style technical falsification on the immutable GREEN head (role-tagged; shared GitHub identity is not formal independent identity).
6. If no material blocker remains, merge through PR and verify post-merge main.

## Explicitly outside S0 acceptance

- real provider/native/hardware attestation or production key custody;
- destructive escape tests on ordinary CI;
- S1 matched-quartet execution on two materially different real environments;
- provider security ranking/certification;
- adaptive policy mutation/crisis/genome behavior (S3/S4);
- formal independent reviewer identity when all actions resolve to the same GitHub principal.

Those are not hidden TODOs converted into PASS. The contract must preserve them as absent evidence / `UNVERIFIED` until real external evidence exists.
