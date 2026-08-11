# Sandbox Authority Deterministic Vectors (Agent D)

Status: bounded Agent D S0 test artifact. This is **not** a second canonical Policy IR/schema and does not certify any backend.

Lease/base integration head: `896787aff272c69b87e3fbd48d9fe51c8319a490`. Immutable D artifact commit: `f48ec2aa063217542236cff155a3d22738f4e39e`.

The machine-readable source of truth is `tests/fixtures/sandbox/authority/vectors.json`. Each fixture has exactly one expected authority/evidence outcome and is intentionally narrow enough for Agent B to falsify independently.

Coverage: D-01..D-12 plus split D-13 variants, D-14, and D-15 review-principal variants. The pack covers self-grant, replay/epoch TOCTOU, multi-principal union/atomic tuple widening, alternate-channel bypass, broker audience/scope/credential-epoch confusion, effective endpoint evidence, stale restore state, lateral/unknown delta gating, delegation actor loss, unknown enforcement provenance, explicit DENY precedence, stale policy attachment, behavioral-only authority-causation UNVERIFIED, matched native decision-bound receipt provenance, fail-closed typed-ID uniqueness, and formal reviewer-independence identity binding.

D-15 does not create a new reviewer identity system. It reuses the same principal semantics as the authority model: a reviewer reference must resolve through trusted/attested principal evidence, the reviewer principal must be distinct from the author principal for a formal independence gate, and the review must bind the exact immutable head/artifact it evaluated. A different agent role under the same principal remains useful role-separated reproduction evidence but is **not** formal identity-independent review. Missing/ambiguous reviewer identity or stale-head binding remains `UNVERIFIED`.

These vectors may expose fields the canonical A schema cannot yet express losslessly. That is intentional deterministic evidence for A/B, not a competing schema. D-authored tests cannot sign Spec/Standards PASS; after A integrates equivalent semantics, D performs field-level fidelity only and B remains the independent gate.
