# S1 Execution Route Binding

Status: candidate first S1 falsifiable slice under exact-head review. This document specifies a route-binding eligibility gate; it does not certify a backend or claim real backend execution is already implemented.

## Claim under test

`S1-EXEC-ROUTE-001`:

> A requested execution target, route, version, build, mode, and adapter must exactly match one independently authenticated external observation of the completed execution. Missing, ambiguous, stale, fallback, degraded, or mismatched observations remain `UNVERIFIED`. An exact match is only `ELIGIBLE` for later semantic evidence evaluation; it is never PASS, secure, certified, or proof of containment.

This slice deletes provider-specific selection syntax from the common path while retaining the facts required to detect silent provider fallback.

## Trust and state boundaries

The route gate keeps six states separate:

1. `ExecutionContract` records the frozen authorized route request.
2. `ExecutionAttemptBinding` binds one run, case, attempt nonce, environment, policy, and observation window to that contract.
3. `ExecutionRouteObservation` records what an external observer says executed.
4. `ObservationAuthentication` carries an external authority's signature over the exact observation digest, key/epoch identity, and validity interval. The evaluator verifies it against verifier-pinned trust policy; the object cannot declare its own trust.
5. `RouteBindingState` records whether the requested and observed route facts match.
6. `RouteGateState` is only `ELIGIBLE` or `UNVERIFIED`.

Readiness remains diagnostic input. It is reported but cannot upgrade missing execution evidence. Observation is not authority: route fields inside an observation cannot authenticate themselves, and keys or authority claims embedded in workload output are not accepted by this gate. The shipped trust policy is empty; callers must explicitly supply pinned authority id, algorithm, key id, trust epoch, and public key material before a signature can be accepted.

## Canonical route identity

Both requested and observed routes carry opaque, provider-neutral identifiers:

- `target_id`
- `route_id`
- `route_version`
- `route_build_digest`
- `mode_id`
- `mode_digest`
- `adapter_id`
- `adapter_version`

The common evaluator performs exact, case-sensitive equality. It has no provider-name branches, aliases, wildcards, version ranges, normalization, or fallback preference. Provider adapters may collect these facts later, but cannot weaken the generic equality rule.

## Eligibility rule

The result is `ELIGIBLE` only when all of the following hold at the evaluation time:

- exactly one route was externally observed;
- the observation binds the exact contract digest, run, case, attempt number, attempt nonce, environment fingerprint, and policy digest;
- the observation falls inside both the UTC and monotonic windows of the attempt;
- execution state is `COMPLETED`;
- route resolution is `EXACT`, not fallback or degraded;
- all eight route identity fields exactly match the contract;
- external authentication is present and its signature verifies against verifier-pinned trust policy;
- authentication binds the canonical digest of this observation;
- authentication is inside its validity interval and matches the pinned authority, key, algorithm, and trust epoch.

Every other state returns `UNVERIFIED` with deterministic reason codes. Multiple defects may be reported together. Unknown values fail closed.

## Result boundary

`RouteGateResult` exposes:

- gate status;
- route-binding state;
- execution state;
- diagnostic readiness state;
- deterministic reason codes;
- requested route and the single observed route when one exists;
- authenticated authority metadata only after successful binding.

It deliberately exposes no `PASS`, backend verdict, `certified`, `secure`, isolation, or containment field. Consumers must run later semantic tests and evidence verification before any broader conclusion.

## Required adversarial cases

- readiness alone with no observation;
- missing authentication;
- a correctly signed authentication evaluated without pinned verifier trust;
- a caller-asserted authority or signature not present in verifier trust policy;
- authentication for a different observation digest;
- unauthenticated or expired authentication;
- not-yet-valid authentication;
- missing or multiple observed routes;
- incomplete, failed, or unknown execution state;
- contract, run, case, attempt, nonce, environment, or policy mismatch;
- observation outside the UTC or monotonic attempt window;
- fallback or degraded resolution even when route fields match;
- one-field mutations for target, route, version, build digest, mode id/digest, and adapter id/version;
- case and whitespace changes, which must not be normalized into a match;
- exact route/authentication match proving only `ELIGIBLE` and exposing no PASS/certification claim.

## Non-goals for this slice

- no real bubblewrap, Podman, gVisor, or provider adapter;
- no execution CLI;
- no real authority key custody, rotation service, or shipped S1 trust roots;
- no S0 evidence-schema rewrite;
- no containment, network, credential, resource, cleanup, or lifecycle verdict;
- no backend selection or automatic fallback.

After this semantic gate is closed, the next S1 milestone must feed it independently collected observations from at least two materially different real backends and run the same authorized-utility, sensitive-canary, network-deny, timeout, resource, and cleanup semantics. Until then S1 remains `UNVERIFIED`.
