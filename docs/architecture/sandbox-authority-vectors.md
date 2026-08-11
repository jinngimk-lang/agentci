# Sandbox Authority Deterministic Vectors (Agent D)

Status: bounded Agent D S0 test artifact. This is **not** a second canonical Policy IR/schema and does not certify any backend.

Lease/base integration head: `896787aff272c69b87e3fbd48d9fe51c8319a490`. Immutable D artifact commit: `f48ec2aa063217542236cff155a3d22738f4e39e`.

The machine-readable source of truth is `tests/fixtures/sandbox/authority/vectors.json`. Each fixture has exactly one expected authority/evidence outcome and is intentionally narrow enough for Agent B to falsify independently.

Coverage: D-01..D-12 plus split D-13 variants for self-grant, replay/epoch TOCTOU, multi-principal union/atomic tuple widening, alternate-channel bypass, broker audience/scope/credential-epoch confusion, effective endpoint evidence, stale restore state, lateral/unknown delta gating, delegation actor loss, unknown enforcement provenance, explicit DENY precedence, stale policy attachment, behavioral-only authority-causation UNVERIFIED, and matched native decision-bound receipt provenance.

These vectors may expose fields the canonical A schema cannot yet express losslessly. That is intentional deterministic evidence for A/B, not a competing schema. D-authored tests cannot sign Spec/Standards PASS; after A integrates equivalent semantics, D performs field-level fidelity only and B remains the independent gate.
