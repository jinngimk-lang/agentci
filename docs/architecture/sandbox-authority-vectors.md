# Sandbox Authority Deterministic Vectors (Agent D)

Status: bounded Agent D S0 test artifact. This is **not** a second canonical Policy IR/schema and does not certify any backend.

Base integration head: `896787aff272c69b87e3fbd48d9fe51c8319a490`.

The machine-readable source of truth for this vector pack is `tests/fixtures/sandbox/authority/vectors.json`. Each fixture has exactly one expected authority/evidence outcome and is intentionally narrow enough for Agent B to falsify independently.

The pack covers D-01..D-12 plus the Supervisor-required split D-13 variants:

- untrusted self-grant;
- approval replay / epoch TOCTOU;
- multi-principal union and atomic tuple widening;
- alternate-channel bypass;
- broker audience/scope/credential-epoch confusion;
- effective-endpoint evidence gaps across DNS/redirect/Host-SNI/proxy/final socket;
- stale authority and credential state after restore;
- lateral/unknown privilege delta expansion-gating;
- delegation actor loss;
- unknown enforcement provenance;
- explicit DENY precedence;
- stale restored policy attachment;
- behavioral-only observation that must remain authority-causation `UNVERIFIED`;
- matched native decision-bound receipt provenance whose causal dimension follows the receipt result.

The vectors deliberately expose fields that the current A schema may not yet represent losslessly. Their purpose is to make that gap deterministic for integration and red-team review, not to create a competing schema.

## Oracle boundary

`tests/test_sandbox_authority_vectors.py` contains the bounded deterministic oracle used only to validate the vector pack. D-authored code cannot sign Spec/Standards PASS for A. Once A integrates equivalent canonical semantics, Agent D performs field-level fidelity review and Agent B remains the independent falsification gate.

Unknown or unobservable enforcement stays `UNVERIFIED`; known stale/invalid authority stays `DENY`; unknown/un-normalizable privilege delta goes through `EXPANSION_GATE`. Policy equality or contraction never proves runtime/session freshness after restore.
