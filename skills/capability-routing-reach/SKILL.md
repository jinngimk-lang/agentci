---
name: capability-routing-reach
description: Use when AgentCI work involves target discovery, external executable readiness, multiple adapter backends, doctor/health semantics, capability fallback, or certifying whether an installed tool is actually usable.
---

# Capability Routing and True Doctor

Use this skill for H2 target introspection, adapter discovery, external CLI/MCP/tool readiness, and multi-backend capability work.

## 1. Model a capability separately from its backend

A user-visible capability may have an ordered list of backend candidates:

```text
capability
→ preferred backend
→ fallback backend
→ last-resort backend
```

Do not hard-code product semantics to one upstream implementation when the capability can survive backend replacement.

A user override may move a known backend to the front. A stale/unknown override must not hide healthy candidates.

## 2. Keep readiness states distinct

Never collapse these into one `available=true` flag:

- `declared` — manifest/config says the capability exists;
- `installed` — executable/package can be resolved;
- `configured` — required local configuration is present;
- `probed` — a bounded real readiness probe was attempted;
- `active` — this backend is the currently verified route;
- `unverified` — deeper checking would require unsafe, stateful, authenticated, expensive, or unavailable operations.

A doctor report should expose enough structured state to explain its verdict.

## 3. PATH resolution is not health

`which`/PATH/package metadata only proves discoverability. It does not prove execution.

When safe, run a **side-effect-free bounded probe** such as:

- `--version`;
- `--help`;
- local `status`/`doctor`/handshake;
- a read-only protocol negotiation.

The probe must be argv-based, timeout-bounded, secret-redacted, and not mutate external state.

Distinguish at least:

```text
missing
broken
probe-timeout
probe-error
healthy
unverified
```

A stale shim whose interpreter disappeared is `broken`, not `installed-and-ready`.

## 4. Report the active backend

For a multi-backend capability, machine-readable diagnostics should include:

```json
{
  "capability": "example",
  "candidates": ["preferred", "fallback"],
  "active_backend": "fallback",
  "state": "ready"
}
```

The exact schema may differ, but the user/agent must be able to determine which route is actually serving the capability now.

`active_backend: null` must not be interpreted as proof that no backend exists when deeper verification was intentionally skipped; use an explicit `unverified`/reason field.

## 5. Failure isolation

One bad backend must not crash the full doctor/capability report.

Probe candidates independently. Capture a bounded error category and continue when policy allows fallback.

Test at minimum:

1. preferred backend healthy;
2. preferred backend missing, fallback healthy;
3. preferred backend resolves but cannot execute, fallback healthy;
4. preferred probe times out, fallback healthy;
5. one backend throws an unexpected error, report survives;
6. all candidates fail;
7. stale override points to a dead/unknown backend;
8. doctor says ready but real installed-entrypoint E2E fails — this must be caught as a false positive.

## 6. Doctor is readiness, not correctness

A successful doctor establishes bounded compatibility/readiness only.

It does **not** prove:

- task correctness;
- output quality;
- application semantics;
- security of the target;
- production reliability.

Those need real E2E eval/certification evidence.

## 7. Honest capability maintenance

Upstream integrations decay. Treat that as normal.

When evidence shows a route is no longer reliable:

```text
demote / disable / remove the route
→ preserve a healthy fallback if one exists
→ narrow docs and claims
→ record why
→ re-test the remaining route matrix
```

Do not keep a capability in docs merely because it used to work.

## 8. Installed-package reality check

Acceptance for CLI/adapters must include the real installed surface, not only editable/import-based tests:

```text
build/install package
→ unrelated working directory
→ resolve public command from PATH
→ run doctor/target path
→ verify structured output and artifacts
```

Packaging/discovery is part of product reliability.

## 9. External capability discovery

Before building a new adapter, inspect whether a mature CLI/MCP/OpenCLI-style backend already exposes the needed capability.

Discovery only proves a candidate exists. Run a bounded probe and real non-empty read-only task before claiming support.

Prefer integrating/certifying a stable upstream contract over reimplementing application behavior.

## 10. Agent A / Agent B split

### Agent A
- define the capability contract before backend-specific code;
- implement the smallest bounded route/probe;
- preserve legacy behavior;
- include failure/fallback tests;
- document unverified states honestly.

### Agent B
Independently attack:
- installed-but-broken executables;
- stale venv/shebangs;
- PATH shadowing;
- preferred-backend failure;
- timeout/error fallback;
- capability lies;
- doctor false positives;
- secret leakage in probe output;
- stateful probes mislabeled as read-only;
- backend-order ambiguity;
- installed-entrypoint behavior from arbitrary cwd.

Report `Spec` and `Standards` verdicts separately.

## Attribution

This skill adapts capability-layer patterns observed in `Panniantong/Agent-Reach` v1.5.0, including ordered backend routing, real command probing, `active_backend`, and failure-isolated doctor reporting. Agent Reach is MIT licensed. See `NOTICE.md` and `.company/research/external/agent-reach-2026-08-10.md`.
