# Capability Routing / True Doctor Design Note

Status: design guidance for future H2 work. It does not expand the current V0 local-command implementation or claim that multi-backend routing already ships.

## Goal

A target capability should remain truthful when its underlying implementation changes, breaks, or is replaced. AgentCI should diagnose the capability surface rather than equating one executable with the capability itself.

## Capability model

A capability can declare an ordered list of backend candidates:

```yaml
capability: example
backends:
  - id: preferred-cli
  - id: fallback-mcp
  - id: legacy-cli
```

The first candidate is preferred by policy, not automatically healthy.

A user override may reorder a known candidate. An unknown/stale override must not erase healthy fallbacks from diagnosis.

## Readiness state model

Keep these concepts distinct:

- `declared`: target/adapter metadata says the capability exists;
- `installed`: the backend can be resolved locally;
- `configured`: required local configuration appears present;
- `probed`: a bounded readiness probe was actually attempted;
- `active`: this backend is currently verified as the route AgentCI should use;
- `unverified`: a deeper probe was intentionally skipped because it would be stateful, authenticated, unsafe, expensive, or unavailable.

A future structured doctor result should expose these distinctions instead of reducing everything to a single boolean.

Illustrative shape only:

```json
{
  "capability": "example",
  "state": "ready",
  "candidates": [
    {"id":"preferred-cli","probe":"broken"},
    {"id":"fallback-mcp","probe":"healthy"}
  ],
  "active_backend": "fallback-mcp",
  "reason": "preferred backend resolved on PATH but failed to execute"
}
```

## Probe contract

Executable presence is discovery, not health.

Where safe, use a cheap side-effect-free probe such as `--version`, `--help`, local `status`/`doctor`, or a read-only protocol handshake.

Probe requirements:

- argv execution; no implicit shell interpolation;
- timeout bounded;
- output bounded/redacted where needed;
- no external mutation;
- no secret values in diagnostic output;
- explicit error category.

At minimum distinguish:

```text
missing
broken
probe-timeout
probe-error
healthy
unverified
```

A stale shim/venv that resolves but cannot execute is `broken`.

## Failure isolation and fallback

One backend failure must not crash the whole doctor report. Probe candidates independently, record the failure, and continue to the next allowed candidate.

Required future contract tests:

1. preferred healthy;
2. preferred missing + fallback healthy;
3. preferred installed but broken + fallback healthy;
4. preferred probe timeout + fallback healthy;
5. one probe raises unexpectedly and full report survives;
6. all backends unavailable;
7. stale/unknown user override does not hide healthy fallback;
8. `active_backend` changes correctly when the preferred backend recovers;
9. doctor success followed by real installed E2E failure is treated as a doctor false positive and fixed.

## Doctor truth boundary

Doctor answers: **is the declared harness/capability compatible and ready enough to attempt?**

Doctor does not prove task correctness, output quality, semantic behavior, production reliability, or security. Those require real eval/E2E evidence.

For stateful/authenticated backends, `unverified` is preferable to a probe that reads credentials, mutates remote state, or performs a user action merely to improve a readiness score.

## Honest upstream lifecycle

Backends decay. When real evidence shows an upstream route no longer works reliably:

```text
demote / disable / remove
→ preserve healthy fallback if available
→ narrow documentation/claims
→ record the evidence
→ rerun the route matrix
```

Support tables are product claims and must remain evidence-backed.

## Packaging reality

Adapter/CLI acceptance includes the installed command surface:

1. build/install in a clean environment;
2. change to unrelated cwd;
3. resolve the public command from PATH;
4. run doctor/readiness path;
5. execute a real bounded target path;
6. verify structured evidence, not only exit 0.

Editable-import tests cannot prove packaging or entrypoint readiness.

## External inspiration

This design note adapts general capability-layer ideas observed in `Panniantong/Agent-Reach` v1.5.0: ordered fallback backends, real executable probes, explicit `active_backend`, failure-isolated health reporting, and removal/demotion of unreliable upstream routes. Agent Reach is MIT licensed; no implementation code is copied and no affiliation is claimed.