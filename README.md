# AgentCI V0

AgentCI V0 is a GitHub-first prototype for testing AI-agent behavior and turning **verified engineering evidence** into draft growth assets. It proves a narrow loop:

```text
Issue → Agent A → PR → Agent B review → CI/evidence gate → merge/release → Growth Pack draft → human publish
```

V0 is deliberately deterministic. It does **not** call external LLM providers; eval files contain fixture-style `actual` results so scoring, reporting, governance, and growth policy can be tested reliably.

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

A passing suite exits `0`; an eval regression exits `1`; malformed input/usage exits `2`.

Try the intentionally failing fixture:

```bash
agentci test examples/evals-failing.yaml
```

## Eval format

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
src/agentci/                 deterministic eval CLI
scripts/                     growth validation/generation
.agents/                     Agent A / Agent B system contracts
.company/                    strategy, metrics, decisions, evidence, growth policy
.github/                     issue/PR contracts and CI
examples/                    passing + failing eval suites
tests/                       unit, policy, repository-contract, and E2E tests
```

## GitHub safety boundary

GitHub **branch protection** is authoritative. Use separate least-privilege identities for Agent A and Agent B, require passing CI plus independent review, and keep repository administration, production secrets, and publishing credentials human-controlled.

See [`docs/operations/github-agent-setup.md`](docs/operations/github-agent-setup.md) for the setup checklist and [`docs/operations/labels.md`](docs/operations/labels.md) for the issue state machine.

## Contributing

AgentCI is open source and welcomes contributors. Useful contributions include reproducible bug reports, regression tests, realistic eval cases, target/harness compatibility work, benchmark methodology, security/reliability review, documentation, and first-run improvements.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md). If you want to help but do not know where to begin, look for bounded community-sized work or open an issue describing the exact environment/problem you can reproduce.

The long-term community loop is documented in [`docs/community-growth.md`](docs/community-growth.md): verified results should attract real users and contributors, whose issues, benchmarks, and PRs then become product evidence for the next Agent A/B cycle.

## Open-source distribution

When a real Growth Artifact exists, AgentCI should use GitHub itself as the first distribution surface—README, Releases, Discussions when enabled, reproducible benchmark/research artifacts, and concrete contribution invitations—then expand to platform-native posts on developer/professional channels that fit the artifact.

We optimize for:

```text
repository visit → install → first successful run → issue/question → contribution → verified PR → repeat contributor
```

Stars and impressions help discovery, but they are not treated as proof of adoption.

## What V0 intentionally does not do

No real provider adapters, no hosted dashboard, no MCP firewall, no production secrets, no billing, no automated community replies, and no external social-posting API. Those are V1 candidates only after adoption evidence justifies them.
