# S1 Execution Route Binding Implementation Plan

Goal: implement and challenge `S1-EXEC-ROUTE-001` without introducing provider-specific logic or a backend verdict.

Base: `main@389c30bab30e2db230574eba9b8e5e23e32c09b3`

## Task 1 — Establish semantic RED

Files:

- add `tests/test_sandbox_execution_route_binding_red.py`
- add a deliberately permissive importable skeleton at `src/agentci/sandbox/route_binding.py`

Write exact-match and adversarial tests for missing, ambiguous, stale, fallback, degraded, unauthenticated, subject-mismatched, attempt/context-mismatched, and route-field mutation cases. Run the targeted file and preserve a semantic failure against the permissive evaluator; an import error is not sufficient RED evidence.

## Task 2 — Implement the fail-closed gate

Files:

- modify `src/agentci/sandbox/route_binding.py`
- modify `src/agentci/sandbox/__init__.py`

Implement immutable route, contract, attempt, observation, authentication, and result types; canonical contract/observation digest binding; exact route comparison; UTC/monotonic window, execution, fallback/degraded, and context checks; deterministic reason ordering; and `ELIGIBLE`/`UNVERIFIED` only. Keep readiness diagnostic and provider names out of control flow.

Run the targeted tests until GREEN. Do not weaken a red case to obtain success.

## Task 3 — Prove public and packaging boundaries

Files:

- add focused repository/package tests if required
- update architecture/operation context only where the shipped status changes

Assert that the public result has no PASS, certification, security, or backend-verdict field; package imports work from a built wheel; existing doctor/verify behavior is unchanged.

Run the full isolated suite, compileall, `git diff --check`, build an exact-head wheel, install it in a fresh environment outside the checkout, and run the route-binding smoke plus the existing sandbox doctor/verify smoke.

## Task 4 — Exact-head challenge and merge

Push one canonical PR. Bind every verdict to the immutable head and current base. A non-Fixer Challenger must reproduce the red-control mutations and return separate Spec and Standards verdicts. A different Merge Decider may merge only with expected-head protection, followed by post-merge main replay.

## Task 5 — Advance to real execution evidence

Do not present the schema-only gate as S1 completion. Open the next bounded change for one provider-neutral `ExecutionContract` exercised on at least two materially different real backends. Preferred zero-license-cost candidates are bubblewrap/rootless Podman where the host permits them; gVisor or another materially different backend may substitute when independently observable. Unsupported mappings remain `UNVERIFIED` rather than silently falling back.
