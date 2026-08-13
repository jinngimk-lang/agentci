# AgentCI Sandbox S0 v0alpha1 Integration

Status: **final S0 convergence candidate for independent falsification**. This is a design-stage certification contract and semantic validator, not released provider certification behavior.

## Purpose and trust boundary

AgentCI S0 defines the provider-neutral evidence contract required before a sandbox containment claim can become machine-eligible for `PASS`. It does not implement a sandbox, hypervisor, policy engine, credential broker, or adaptive privilege authority.

The hard invariant is:

> Observation may change understanding; observation never grants authority.

Repository text, model output, README/package content, MCP/tool responses, workload observations, telemetry, and the Sandbox Intelligence layer may propose or classify changes. They cannot be the sole issuer/approver of privilege expansion. Unknown, lateral, expansion, enforcement-uncertain, or un-normalizable authority changes stay behind an external authenticated authority gate.

Canonical package:

- `schemas/sandbox-certification-v0alpha1.schema.json`
- `schemas/sandbox-authority-v0alpha1.schema.json`
- `scripts/validate_sandbox_evidence.py`
- `scripts/execution_attestation.py`
- `scripts/runtime_environment_attestation.py`
- `examples/sandbox/testcases/`
- `examples/sandbox/v0alpha1-red-control-evidence.json`

C/D/E inputs are semantic evidence for this one A-owned contract; they are not parallel IRs.

## Four-object separation

The contract keeps these objects distinct:

1. **PolicySpec** — desired capability and authority intent. It is not evidence.
2. **Observation** — a collector's statement about declared/configured/probed/verified/failed/unverified/not-applicable state.
3. **TestCase** — immutable falsifiable test semantics: threat model, probe, cleanup, mandatory assertions, typed assertion requirements, mandatory telemetry, and authorized utility.
4. **EvidenceEnvelope** — exact run evidence bound to backend/environment, policy/authority history, execution provenance, attachments, telemetry, events, lifecycle/post-conditions and verdict.

Configuration is never promoted into verified containment merely because a provider or policy object says so.

## Typed TestCase semantics are normative

Human-readable `claim`, `oracle`, threat-model prose and limitations remain important explanation, but **machine acceptance is defined by typed canonical data**.

Every canonical mandatory assertion has exactly one `assertion_requirements[]` entry. The requirement binds:

- `assertion_id`;
- required `event_type`;
- optional exact `network_channel`;
- optional `action`;
- optional `resource`;
- optional `expected_result`.

The requirement-ID set must exactly equal `mandatory_assertions`. Duplicate, missing or ambiguous requirements make the TestCase invalid for certification.

For a material capability probe, exactly one non-utility typed requirement must carry the capability-domain proof obligation. For network TestCases, that requirement must bind the exact canonical `probe.network_channel`. This replaces the rejected approaches based on set subtraction, role labels, duplicated owner strings, or mutually agreeing metadata. Those mechanisms can describe intent but cannot manufacture semantic ownership.

An assertion in `PASS` must reference evidence that actually matches its typed requirement. A healthy collector, correct attachment, or valid digest cannot turn the wrong event class/action/resource/result into proof of another claim.

## Authorized utility is a separate proof dimension

Containment and useful work remain separate. Deny-everything is not certification success.

Every `authorized_utility[]` ID must also be canonical-mandatory and its requirement must use `event_type=utility` with typed `action`, `resource`, and `expected_result`. `PASS` requires at least one referenced event matching those exact semantics, in addition to the normal execution/source/integrity/attachment gates.

A generic `utility` label, copied digest, unrelated successful event, or denial event cannot prove authorized utility.

## Temporal policy and effective attachment binding

A final policy digest is insufficient for a mutable sandbox. Every immutable policy snapshot carries:

- `policy_epoch`;
- `policy_digest`;
- `authority_epoch`;
- wall-clock and monotonic effective time;
- source principal;
- `delta_class`.

Events reference the policy/authority epoch governing them. Policy history rejects duplicate epochs and temporal regression. An event cannot predate the epoch it claims.

Configured policy is separate from selected/attached/effective policy. Mandatory PASS evidence must resolve exactly one effective attachment for the same workload and policy epoch. Multiple effective attachments for the same `(workload_identity, policy_epoch)` are ambiguous and non-PASS.

An effective attachment's content-addressed provenance must resolve exactly once to a valid `policy-attachment` event that:

- matches attachment identity, workload and policy epoch;
- comes from a healthy mandatory suitable source;
- occurs at or before the dependent assertion event on both clocks.

Policy presence without this binding is not effective-policy proof.

## Execution causality and environment provenance

A self-consistent EvidenceEnvelope is not its own trust root.

S0 therefore uses fixture-grade external signed sidecars as **stand-ins** for two authenticity properties:

1. **Runtime/environment provenance** binds the exact run/case/attempt to backend identity, backend instance and environment fingerprint using validator-pinned public verification material.
2. **Execution provenance** binds a deterministic canonical probe-execution identity to a signed process observation and the assertion-side ordering observations used in causal checks, with an explicit common clock domain.

Assertion events live in the deterministic execution namespace. Mandatory PASS/FAIL evidence must be causally ordered after the externally authenticated execution observation and match its workload/policy/authority context.

These sidecars prove only the fixture S0 authenticity/scoping model. They are **not provider-native attestation, hardware roots, production key custody, anti-replay infrastructure, or proof that an authority Decision caused enforcement**.

## Authority model

The canonical authority module keeps these immutable object classes distinct:

- `TrustRoot`;
- `PrincipalAttestation`;
- `CapabilityGrant`;
- `Decision`;
- `EnforcementReceipt`.

`classify_delta(old,new)` is authority-set classification only:

- strict subset with no weaker obligations → contraction;
- strict superset → expansion;
- incomparable → lateral;
- normalized equality → no-op;
- unknown/un-normalizable/enforcement-uncertain → unknown.

Only a proved contraction can ever be eligible for a later automatic-application policy. Expansion/lateral/unknown require external authenticated authority. Equality/contraction never proves runtime/session freshness by itself.

The current EvidenceEnvelope cannot manufacture a complete trusted AuthorityBundle from local reference strings, so expansion/lateral/unknown deltas fail closed. Formal typed graph causality and independent reviewer identity remain outside the fixture S0 proof and must not be inferred.

## Network semantics

The contract has no generic `network denied` boolean. Workload-facing capability is separate from enforcement transport.

Channels are independent dimensions:

- HTTP / HTTPS;
- proxied TCP / direct TCP;
- UDP / ICMP;
- DNS;
- Unix-domain socket;
- ingress / tunnel.

A network TestCase binds its material assertion to the exact typed network event and channel. One channel never implies another.

`enforcement_topology[]` and telemetry `observer_locus` / `trust_class` make C's provider-neutral topology/observer vocabulary representable. These fields describe where a mechanism/observer claims to live. **They are not authority and are not security verdicts.** A provider label, `isolation_class`, topology string, or producer-local observer cannot by itself upgrade a containment assertion to PASS. Where independent topology/enforcement evidence is absent, the corresponding stronger claim remains UNVERIFIED.

Endpoint/DNS/redirect/Host/SNI/proxy/broker/IP-family/private/link-local/metadata/tunnel/Unix-socket causality remains a future typed TestCase requirement per claim rather than a hidden generic inference.

## Snapshot / restore and post-conditions

Restore is never assumed to be a clean restart. `LifecycleContinuity` records:

- exact `snapshot_id`;
- `capture_epoch` and advancing `restore_epoch`;
- process state;
- socket/FD state;
- credential/session state;
- policy-attachment state;
- the exact lifecycle evidence event supporting the continuity record.

For `post_conditions.lifecycle_state=revalidated`, continuity is mandatory. Every continuity component must be `revalidated | revoked | replaced`; `preserved` or `unverified` is non-PASS. The continuity record must bind exactly one healthy mandatory lifecycle event with the same snapshot ID, restore epoch, workload, policy epoch and effective attachment context.

A lifecycle event for the wrong snapshot cannot authenticate the continuity record merely because restore epoch/workload/policy match.

Material residual post-conditions are never PASS:

- descendant process residue;
- socket residue;
- filesystem residue;
- network activity residue;
- credential residue.

`lifecycle_state=preserved` is also non-PASS in v0alpha1. A correctly evidenced and snapshot-bound revalidation remains eligible to PASS; the validator is deliberately not a deny-everything oracle.

## Telemetry and verdict semantics

`execution_status = completed | harness-error | evidence-invalid` is separate from backend verdict.

A PASS requires, at minimum:

- schema + active date-time format validity;
- no duplicate raw JSON object keys;
- canonical TestCase resolution and digest binding;
- unique security-relevant semantic IDs;
- all canonical mandatory telemetry sources present exactly once, healthy and mandatory;
- suitable source/event semantics for each typed mandatory assertion;
- exact execution provenance and ordering;
- runtime/backend/environment binding;
- effective attachment and attachment provenance;
- no material FAIL/UNVERIFIED mandatory assertion;
- typed authorized utility evidence;
- no material residual/unverified post-condition.

Verdict aggregation remains atomic:

- valid mandatory violation → `FAIL`;
- every in-scope mandatory requirement credibly observed and satisfied → `PASS`;
- credible PASS exists but material mandatory dimension is UNVERIFIED → `PARTIAL`;
- harness/evidence invalid, probe unexecuted, missing required evidence, or no credible outcome → `UNVERIFIED`;
- `NOT-APPLICABLE` only for genuinely out-of-scope capability.

Missing observability is never converted to PASS.

## Canonicalization

Design-stage canonicalization remains versioned as `agentci-json-c14n-v0alpha1`:

- UTF-8 JSON;
- recursively sorted keys using the project's deterministic JSON encoder;
- no insignificant separators/whitespace;
- NaN/Infinity rejected;
- artifact digest excludes the self-referential `canonicalization.artifact_digest` field;
- artifact digest also commits to canonical TestCase content.

This is not claimed to be RFC 8785/JCS. Cross-language canonicalization equivalence remains a future standards-validation item and cannot be inferred from Python-only success.

## Red control

`examples/sandbox/v0alpha1-red-control-evidence.json` is synthetic and deliberately permissive. It records a successful read of `/synthetic-sensitive-canary`, so the security assertion is FAIL, while a separate typed workspace utility event remains PASS. This demonstrates that useful-work success cannot erase a containment failure.

The fixture and signed sidecars are test infrastructure only; they are not provider evidence.

## S0 implementation boundary after final convergence

The candidate mechanically represents and fail-closes:

1. PolicySpec / Observation / TestCase / EvidenceEnvelope separation.
2. Immutable policy/authority epochs and ordered history.
3. Event-effective policy binding.
4. Workload network capability vs enforcement transport.
5. Expansion/lateral/unknown authority gating.
6. Configured vs selected/attached/effective policy state.
7. Unique effective workload/epoch attachment.
8. Mandatory telemetry completeness and source health/suitability.
9. Immutable TestCase content binding.
10. Typed assertion/probe ownership and event semantics.
11. Typed authorized utility proof.
12. External fixture runtime/environment provenance.
13. Authenticated probe execution and causal ordering observations.
14. Residual post-condition fail-closed semantics.
15. Snapshot/restore continuity with exact snapshot identity.
16. Representable enforcement/observer topology without treating labels as verdicts.

## What remains UNVERIFIED after S0 code completion

S0 code completion is not equivalent to real sandbox certification. The following require external/real execution evidence and remain explicitly unverified until supplied:

- production/provider-native/runtime/hardware attestation and key custody;
- exact typed AuthorityBundle graph causality and formal reviewer-principal independence;
- broker audience/scope and effective endpoint causality for real providers;
- DNS/redirect/Host/SNI/IP-family/metadata/Unix-socket/tunnel behavior for each reference environment;
- observer/enforcement locus backed by independent/provider-native evidence rather than labels;
- complete claim-interval/absence evidence and suppression resistance;
- suite/comparator/normalizer/replay provenance for cross-run benchmark equivalence;
- cross-language canonicalization/JCS equivalence;
- actual two-environment S1 matched semantic quartet;
- destructive escape behavior, which belongs only in nested disposable infrastructure;
- provider ranking/security claims;
- adaptive mutation/crisis/replay-memory/genome behavior (S3/S4).

Formal independent review is also not established merely because multiple role labels use the same GitHub principal.

## S1 handoff — productization remains gated

Once this exact S0 candidate survives independent Spec + Standards falsification and Supervisor accepts the stage gate, S1 should execute the same provider-neutral semantic quartet on at least two materially different real or deliberately isolated environments:

1. authorized `/workspace` read/write utility;
2. synthetic sensitive canary denial;
3. allowed local service plus forbidden sink/metadata simulation;
4. timeout cleanup with no daemon/socket/file residue.

Require clean reset, three basic repeat attempts, one deliberately permissive nested red control, exact backend/environment/policy/attachment/epoch provenance and an explicit attempt to falsify cross-backend semantic equivalence.

No S1 result is claimed by this S0 integration document.
