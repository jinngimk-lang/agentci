# AgentCI V0

AgentCI V0 is a GitHub-first prototype for testing AI-agent behavior and turning **verified engineering evidence** into draft growth assets. It proves a narrow loop:

```text
Issue → Agent A → PR → Agent B review → CI/evidence gate → merge/release → Growth Pack draft → human publish
```

V0 keeps deterministic fixture evals for stable regression checks and now also supports one bounded **local-command** target for evaluating a real local process. It still does **not** call external LLM providers, HTTP services, or MCP endpoints.

## 5-minute quickstart

Requirements: Python 3.11+.

```bash
python -m pip install -e '.[dev]'
agentci test examples/evals.yaml
```

The command writes:

```text
artifacts/agentci-results.json
artifacts/agentci-report.md
```

A passing suite exits `0`; an eval regression or target execution failure exits `1`; malformed suite input/CLI usage exits `2`.

Try the intentionally failing fixture:

```bash
agentci test examples/evals-failing.yaml
```

## Run a local agent/process

A suite can declare one argv-based local command target:

```bash
agentci test examples/evals-local-command.yaml
```

Example target configuration:

```yaml
target:
  type: local-command
  command: [python, examples/local_target.py]
  timeout_seconds: 2
```

AgentCI launches the argv list directly with no shell interpolation. Shell command strings are rejected. The process inherits the directory where `agentci` was invoked.

**Security boundary:** `local-command` executes the program and argv declared by the suite. Only run local-command suites from trusted repositories/branches. Avoiding implicit shell interpolation reduces injection risk, but it does not make untrusted command configuration safe to execute.

For each case, AgentCI writes one JSON object plus a newline to the target's **stdin**:

```json
{"id":"refund-confirmation","input":"Refund order #123"}
```

The target must write one JSON object to stdout containing at least a boolean `success`:

```json
{"success":true}
```

It may also return a non-negative finite `cost_usd`. AgentCI ignores target-supplied latency and measures elapsed latency itself. `timeout_seconds` defaults to 10 seconds when omitted, must be positive and finite, and is enforced separately for every case.

AgentCI limits **stdout and stderr independently to 1 MiB per case**. Exceeding either limit terminates the target process tree and is reported as a normal failed case; stderr is drained only for bounding and is not retained in the result. This bounds AgentCI's capture memory for verbose or malfunctioning targets while keeping stdout available for the JSON result contract.

Timeouts, output-limit breaches, missing executables, non-zero exits, malformed/non-UTF-8 output, missing/invalid `success`, or invalid `cost_usd` are reported as normal failed cases rather than uncaught crashes. On POSIX, AgentCI starts each target in a separate session and terminates the whole process group on timeout or output-limit breach; descendant-cleanup behavior is regression-tested on Linux. On Windows, AgentCI creates a new process group and attempts tree termination with `taskkill /T /F`, with direct-process kill as a fallback if that OS command cannot run. These execution bounds are not a CPU, total-memory, filesystem, network, or syscall sandbox. When a `target` is configured, case-level fixture `actual` values are rejected so runtime evidence cannot be mixed ambiguously with fixtures.

## Eval format

Fixture mode remains supported unchanged:

```yaml
suite: demo
cases:
  - id: refund-confirmation
    input: "Refund order #123"
    actual:
      success: true
      latency_ms: 850
      cost_usd: 0.02
    expected:
      success: true
      max_latency_ms: 1500
      max_cost_usd: 0.05
```

Local-command mode omits `actual` because AgentCI produces it by executing the target:

```yaml
suite: local-command-demo
target:
  type: local-command
  command: [python, examples/local_target.py]
  timeout_seconds: 2
cases:
  - id: refund-confirmation
    input: "Refund order #123"
    expected:
      success: true
      max_latency_ms: 2000
```

AgentCI checks expected success plus optional maximum latency/cost and writes per-case failure reasons.

## The two-agent operating loop

### Agent A — Builder / Researcher

Agent A chooses bounded issues, implements with tests, and opens evidence-backed PRs. It **must not merge** its own PR, change branch protection/secrets, or publish marketing claims. Its full contract is in [`.agents/builder.system.md`](.agents/builder.system.md).

### Agent B — Critic / Red Team / Growth

Agent B independently verifies Agent A's claims, tries adversarial/boundary cases, requests changes or approves, and can create draft growth assets only after policy validation. It **must not directly push** feature code to protected main and never receives external publishing authority in V0. See [`.agents/critic-growth.system.md`](.agents/critic-growth.system.md).

## Growth Pack: evidence first

Canonical research artifacts live under:

```text
.company/research/findings/<artifact-id>/
├── facts.json
├── evidence.md
└── sources.json
```

Validate one:

```bash
python scripts/validate_growth_artifact.py .company/research/findings/demo-benchmark
```

Generate a draft pack:

```bash
python scripts/generate_growth_pack.py \
  .company/research/findings/demo-benchmark \
  --output-root growth
```

The Growth Pack contains `x.md`, `reddit.md`, `hackernews.md`, `blog.md`, copied facts/evidence, and a publish checklist. Numeric claims in public drafts must match structured numeric facts. Threshold failures, unsupported claims, and non-disclosure-ready security findings are rejected.

**There is no auto-publish in V0.** A human repository owner reviews and publishes anything external.

## Growth thresholds

Owner-editable defaults in [`.company/growth/rules.yaml`](.company/growth/rules.yaml):

- benchmark: at least 300 reproducible runs;
- performance: at least 20% improvement with at least 100 samples;
- security: high/critical, reproducible, disclosure-ready;
- integration: demo + tests + docs;
- release: at least three meaningful changes or one major capability;
- dataset: at least 100 examples plus reproducible notes.

These are operating-policy defaults, not claims about market truth.

## Repository architecture

```text
src/agentci/                 deterministic eval CLI + local-command adapter
scripts/                     growth validation/generation
.agents/                     Agent A / Agent B system contracts
.company/                    strategy, metrics, decisions, evidence, growth policy
.github/                     issue/PR contracts and CI
examples/                    fixture suites + runnable local-command example
tests/                       unit, policy, repository-contract, and E2E tests
```

## GitHub safety boundary

GitHub **branch protection** is authoritative. Use separate least-privilege identities for Agent A and Agent B, require passing CI plus independent review, and keep repository administration, production secrets, and publishing credentials human-controlled.

See [`docs/operations/github-agent-setup.md`](docs/operations/github-agent-setup.md) for the setup checklist and [`docs/operations/labels.md`](docs/operations/labels.md) for the issue state machine.

## What V0 intentionally does not do

No HTTP/provider/MCP adapters, no hosted dashboard, no production secrets, no billing, no automated community replies, and no external social-posting API. Those are V1 candidates only after adoption evidence justifies them.
