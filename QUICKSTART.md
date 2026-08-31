# AgentCI Quickstart

This page describes the current `0.3.0.dev0` development line. The released `v0.2.0` CLI does **not** include `agentci init` or `agentci showcase` yet.

## First deterministic result

Requirements: Python 3.11+.

From a source checkout:

```bash
python -m pip install -e '.[dev]'
agentci init
agentci test agentci.yaml
```

`agentci init` creates `agentci.yaml` only when the target does not already exist. It refuses to overwrite an existing file.

The generated starter suite is deliberately deterministic and provider-free. A successful first run prints `1/1 passed` and writes:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

This first PASS proves only that the generated eval suite ran through AgentCI's deterministic eval engine. It is not a model-quality, agent-security, sandbox-isolation, or backend-certification claim.

To choose another path:

```bash
agentci init path/to/my-evals.yaml
agentci test path/to/my-evals.yaml
```

## Discover current evidence cases

On the same `0.3.0.dev0` development line:

```bash
agentci showcase list
agentci showcase show sandbox-sensitive-read-red-control
```

The showcase catalog is discovery metadata. It reports evidence maturity, represented commands, repository paths where applicable, and claim boundaries. Catalog presence does not mean a sandbox ran or passed.

## Inspect sandbox readiness

```bash
agentci sandbox doctor --json
```

Readiness is not backend execution, isolation proof, or security certification.

## Validate canonical sandbox evidence

```bash
agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest
```

The canonical red-control fixture is intentionally valid evidence with a `FAIL` verdict. Exit code `0` from `sandbox verify` means the evidence envelope is valid under the contract; it does **not** mean the sandbox passed.

## If you arrived from an upstream agent/runtime bug

AgentCI is most useful when a failure can be reduced to a portable invariant such as:

- replay/restore fidelity;
- duplicate non-idempotent effects;
- cleanup/terminality;
- residual process/socket/resource state;
- execution identity drift;
- policy/authority binding;
- checkpoint/state immutability;
- false-success or misleading telemetry.

Preserve the upstream issue as canonical provenance. A good first contribution is usually a bounded fixture + validation test, not a provider integration or certification claim.
