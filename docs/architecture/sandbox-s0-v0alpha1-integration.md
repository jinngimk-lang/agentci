# AgentCI Sandbox S0 v0alpha1 Integration

Status: **design-stage integration head for independent Agent B review**. This is not released `agentci sandbox` behavior and is not a certification claim.

## Purpose

This document is Agent A's canonical S0 integration surface for Supervisor #24 / CMD:A #25. It integrates accepted program invariants and the current bounded inputs from B/C/D/E without inventing provider guarantees.

Canonical schema package:

- `schemas/sandbox-certification-v0alpha1.schema.json`
- `schemas/sandbox-authority-v0alpha1.schema.json`

The package is one Agent A-owned contract. C/D/E provide domain packets; they do not maintain competing IRs.

## Four object separation

The contract keeps these objects distinct:

1. `PolicySpec` — desired capabilities plus trusted authority references. It is intent, not evidence.
2. `Observation` — declared/configured/probed/verified/failed/unverified/not-applicable facts bound to collector health and the effective policy/authority epoch.
3. `TestCase` — falsifiable semantic claim, threat model, preconditions, probe, oracle, cleanup, backend assumptions, mandatory assertions, mandatory telemetry and authorized utility.
4. `EvidenceEnvelope` — exact run evidence, policy history, attachment state, backend/environment provenance, telemetry, trajectory events, post-conditions, limitations, execution status and verdict.

No object may be used as a substitute for another. In particular, configuration cannot become an Observation of effective containment and a desired `DENY` cannot become evidence that access was denied.

## Temporal policy binding

A final `policy_digest` is insufficient for a mutable sandbox. Every immutable policy snapshot is identified by:

- `policy_epoch`;
- `policy_digest`;
- `authority_epoch`;
- UTC and monotonic effective time;
- source principal;
- `delta_class = contraction | expansion | lateral | no-op | unknown`.

Every trajectory event and policy attachment references the policy epoch that was effective for that event. Policy history is ordered: duplicate epochs or time regression are invalid evidence. An event cannot precede the effective wall/monotonic time of the policy epoch it claims, and its authority epoch must match that policy-history entry. If the effective epoch cannot be established, the affected assertion is `UNVERIFIED`; it cannot contribute to PASS.

The EvidenceEnvelope binds an ordered `policy_history` plus `policy_history_digest` rather than only one final policy digest.

## Authority model

The canonical authority module defines five immutable object classes:

- `TrustRoot`;
- `PrincipalAttestation`;
- `CapabilityGrant`;
- `Decision`;
- `EnforcementReceipt`.

A grant and decision are bound to principal, action, resource, context, policy/authority epoch and validity information. An enforcement receipt binds a decision to the actual backend/environment and, when applicable, actual endpoint, credential epoch and restore epoch.

Unknown/error authorization is intended to fail closed. The LLM, workload, repository, MCP/tool output and other observations cannot be the only grant issuer/approver for privilege expansion.

### Privilege delta classification

`PrivilegeDelta.classification` is one of:

- `contraction` — new effective authority is a strict subset and obligations are not weaker;
- `expansion` — new authority is a strict superset;
- `lateral` — old/new authority sets are incomparable;
- `no-op` — normalized authority is equal;
- `unknown` — normalization/enforcement equivalence is not established.

Only proved contraction may later be eligible for automatic application. `lateral`, `expansion` and `unknown` remain behind an external authority gate. `classify_delta` alone never proves snapshot/restore safety because stale live sessions can survive while the normalized authority set appears unchanged.

## Network semantics: capability != enforcement transport

The contract does not contain a generic boolean `network denied` claim.

Workload-facing channels are separate semantic dimensions:

- HTTP;
- HTTPS;
- proxied generic TCP;
- direct TCP;
- UDP;
- ICMP;
- DNS;
- Unix-domain sockets;
- ingress;
- tunnels.

Each channel is independently `blocked | mediated | direct | unverified | not-applicable`.

Enforcement transport is a separate object, for example an application proxy, stream proxy, packet filter, namespace boundary, service mesh or host broker. A Unix socket can therefore be an intended enforcement transport without implying arbitrary workload Unix-socket authority. No channel verdict is inferred from another channel.

## Configured -> selected/attached -> effective

A policy existing in a control plane does not prove that it applies to the tested workload. `PolicyAttachment.state` distinguishes:

```text
configured -> selected -> attached -> effective
                      \-> failed / unverified
```

Claims that depend on policy selection require attachment evidence linking workload identity/selector, policy digest/epoch and enforcer. For this S0 envelope, an `effective` attachment's `evidence_digest` must content-address the `semantic_digest` of a valid `event_type=policy-attachment` event in the same envelope. That event remains behavioral/control-plane evidence; it does not by itself prove D-style grant/decision causation. Missing or dangling attachment evidence yields `UNVERIFIED`, not PASS.

## Snapshot / restore continuity

Restore is not modeled as an implicit clean reset. `LifecycleContinuity` records:

- `snapshot_id`;
- `capture_epoch`;
- `restore_epoch`;
- process state;
- socket/file-descriptor state;
- credential/session state;
- policy-attachment state.

Each continuity state is `preserved | revalidated | revoked | replaced | unverified`.

A preserved socket/session after restore must be re-bound to the current authority/policy/credential evidence or the affected claim remains failed/unverified. Same-policy equality before/after restore does not by itself prove fresh authority.

## Evidence and verdict semantics

`execution_status = completed | harness-error | evidence-invalid` is separate from the backend verdict.

The S0 validator executes the Draft 2020-12 JSON Schema with date-time format checking before accepting PASS. Unknown fields, invalid event classes and invalid date-time values therefore fail closed rather than bypassing semantic checks.

Atomic verdict rule used by the S0 helper:

- any valid mandatory assertion or explicit residual cleanup violation -> `FAIL`;
- every in-scope mandatory assertion observed and satisfied -> `PASS`;
- at least one mandatory PASS, no FAIL, but a material mandatory UNVERIFIED -> `PARTIAL`;
- unexecuted probe, harness error, invalid evidence, missing credible mandatory evidence -> `UNVERIFIED`;
- `NOT-APPLICABLE` is only for a capability genuinely outside claim scope.

A PASS requires unique event/assertion/telemetry identities, valid event-to-collector references, and at least one observed event from every envelope-local source marked `mandatory`. This last rule proves only that the declared mandatory collector participated; it does **not** prove TestCase event-class or claim-interval completeness. That stronger coverage remains `UNVERIFIED` until an immutable TestCase digest/bundle is bound into evaluation.

A PASS cannot silently contain unverified or residual material post-conditions. Deny-everything behavior is not sufficient because each `TestCase` also carries `authorized_utility` requirements.

## Canonicalization and digest rule

Design-stage canonicalization is `agentci-json-c14n-v0alpha1`:

- UTF-8 JSON;
- keys sorted recursively by Python's deterministic JSON encoder;
- separators `,` and `:` with no insignificant whitespace;
- `NaN`/`Infinity` rejected;
- the EvidenceEnvelope artifact digest is SHA-256 over the canonical document with `canonicalization.artifact_digest` omitted, avoiding a self-referential digest.

This is intentionally versioned and is **not** claimed to implement RFC 8785/JCS. It may be replaced before S0 freeze if B finds cross-language/numeric ambiguities.

## Deliberately permissive red control

`examples/sandbox/v0alpha1-red-control-evidence.json` is a synthetic red control, not provider evidence. The desired claim is that a synthetic sensitive canary is unreadable; the deliberately permissive fixture records an actual read event and a mandatory assertion FAIL. It also contains a separate policy-attachment event so attachment provenance has a real content-addressed target rather than an arbitrary placeholder digest.

Validation command:

```bash
python scripts/validate_sandbox_evidence.py examples/sandbox/v0alpha1-red-control-evidence.json
pytest -q tests/test_sandbox_evidence_contract.py tests/test_sandbox_authority_contract.py
```

The validator is an S0 semantic checker, not a sandbox runtime/certifier.

## Current resolved S0 mechanics in this draft

1. `PolicySpec`, `Observation`, `TestCase`, `EvidenceEnvelope` are formally separated.
2. policy epoch/history and per-event binding are represented.
3. authority references and the five D authority objects are represented.
4. network capability and enforcement transport are separate, channel-specific semantics.
5. attachment/selection evidence is separate from configured/effective behavior and has an envelope-local content-addressed evidence target.
6. restore continuity is explicit and not assumed clean.
7. execution status, schema/evidence validity, mandatory assertion coverage and cleanup post-conditions are separate from backend verdict.
8. a deliberately permissive red control is present and expected to fail the containment claim.

These are implementation claims awaiting C/D/E fidelity checks and independent B exact-head review; they are not S0 acceptance.

## Explicit unresolved items — do not infer consensus

The following remain unresolved or intentionally narrowed:

- exact minimum representation for D's trusted AuthorityBundle graph, broker audience/scope, endpoint causality and restore/session freshness;
- receipt provenance strength and observer locus: behavioral evidence must not be upgraded into proof that a specific grant/Decision caused enforcement;
- true TestCase event-class and claim-interval telemetry completeness, including absence-as-negative-evidence semantics;
- exact distinction between enforceable-but-not-observable and observable-but-not-enforceable per S1 reference target;
- ordinary-CI-safe versus nested-disposable-only attack classes;
- whether the current project-specific canonicalization is sufficiently cross-language stable;
- formal independent-review identity provenance; same GitHub principal with different role labels is not independent verification;
- exact S1 reference targets and execution readiness.

These unresolved items must not be hidden in free-form metadata or silently treated as PASS.

## Planned S1 matched semantic quartet — HOLD for productization

After B gives Spec PASS + Standards PASS and Supervisor accepts S0, the first S1 experiment should use one provider-neutral case definition per semantic claim, with setup/collector adapters only:

1. authorized `/workspace` read/write utility canary;
2. external synthetic sensitive canary exists and is unreadable;
3. allowed local service is reachable while forbidden sink/metadata simulation is unreachable;
4. timed-out parent leaves no daemonized descendant/socket/file residue.

Each case requires clean reset, three basic repeat attempts, a deliberately permissive nested red control and exact provenance. Three attempts only establish basic reproducibility; they are not a public benchmark.

## Non-goals for this head

- no sandbox runtime or hypervisor implementation;
- no provider adapter;
- no `agentci sandbox certify` released behavior;
- no adaptive policy mutation;
- no crisis/incident memory/genome implementation;
- no provider ranking or opaque security score;
- no self-certification by Agent A.
