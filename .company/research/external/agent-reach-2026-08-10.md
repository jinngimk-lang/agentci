# External review: Agent Reach (2026-08-10)

Source: `Panniantong/Agent-Reach`

## Decision

Adopt selected capability-routing and health-check patterns. Do **not** add Agent Reach as an AgentCI core runtime dependency and do not import its authenticated social-platform/cookie workflows into AgentCI.

## Why it matters to AgentCI

Agent Reach v1.5.0 reframes platform integrations as a capability layer with ordered backend candidates, real lightweight health probes, an explicit `active_backend`, and fallback behavior. That maps directly to AgentCI H2 target introspection/doctor and future adapter certification.

The strongest transferable patterns are:

1. **Ordered backend candidates** — a capability can have a preferred backend plus fallbacks instead of one hard-coded implementation.
2. **Real health probes** — executable presence is not health. A stale shim/venv may resolve on PATH but fail to execute.
3. **Explicit active backend** — machine-readable diagnostics should report which backend is actually serving a capability now.
4. **Truthful state separation** — declared, installed, configured, probed, active, and unverified are different states.
5. **Failure isolation** — one broken backend/channel must not crash the entire doctor report.
6. **Side-effect-free probing** — doctor probes should use cheap version/status/help/handshake operations and must not mutate state merely to prove readiness.
7. **Backend override without hiding fallbacks** — a user override may reorder candidates, but an unknown/stale override should not conceal a healthy fallback.
8. **Honest deprecation** — when an upstream path is no longer reliable, remove/demote it rather than preserving a misleading capability claim.
9. **Installed-package verification** — Agent Reach added real wheel build/install smoke gates after editable installs failed to expose packaging defects; this reinforces AgentCI's unrelated-working-directory installed-entrypoint E2E requirement.
10. **Capability-oriented skill routing** — agents should discover the capability/intent first, then load only the backend-specific instructions needed for the current path.

## AgentCI adoption

Immediate design/policy adoption:
- add `skills/capability-routing-reach/SKILL.md`;
- add a capability-routing/doctor design note;
- teach Agent A/B/Supervisor to distinguish installed/configured/probed/active states;
- require real side-effect-free probes where a doctor claim depends on an external executable;
- require independent tests for preferred-backend failure + healthy fallback, probe timeout, stale executable, per-backend exception isolation, and false-positive doctor states.

Future experiment after H1 is independently accepted:
- evaluate Agent Reach itself as a real third-party multi-backend harness/capability target for AgentCI certification;
- do not use authenticated social accounts/cookies in CI;
- focus on local CLI health/routing semantics and public zero-config paths only.

## Non-goals

- AgentCI does not become a social-media scraping product.
- No automatic browser-cookie extraction or login automation is introduced.
- No core dependency on Agent Reach/OpenCLI.
- No H2/H3 feature expansion is added to the already-large PR #9.
- No claims of partnership or endorsement by Agent Reach maintainers.

## Security notes

Treat backend discovery as a declaration until a bounded probe confirms it. Probe commands must be argv-based, timeout-bounded, output-bounded where applicable, secret-redacted, and side-effect-free. A `doctor` success proves readiness/compatibility only; it does not prove task correctness.

## Source references

- Repository: https://github.com/Panniantong/Agent-Reach
- v1.5.0 release: https://github.com/Panniantong/Agent-Reach/releases/tag/v1.5.0
- Upstream skill: `agent_reach/skill/SKILL.md`
- Routing contract: `agent_reach/channels/base.py`
- Probe implementation: `agent_reach/probe.py`
- Doctor aggregation: `agent_reach/doctor.py`

Agent Reach is MIT licensed. This note summarizes/adapts patterns and does not copy its implementation code.