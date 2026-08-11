# AgentCI V0

AgentCI V0 is a GitHub-first prototype for testing AI-agent behavior and turning **verified engineering evidence** into responsible growth/distribution assets. It proves a narrow loop:

```text
Issue → Agent A → PR → Agent B review → CI/evidence gate → merge/release → Growth Artifact → evidence-gated distribution
```

V0 is deliberately deterministic. It does **not** call external LLM providers; eval files contain fixture-style `actual` results so scoring, reporting, governance, and growth policy can be tested reliably.

## Pre-alpha sandbox readiness

`agentci sandbox doctor [--json]` is a pre-alpha, provider-neutral local readiness report. It safely checks candidate tools (Docker, Podman, bubblewrap, and Windows-relevant WSL/Windows Sandbox) without creating a sandbox or changing the machine:

```bash
agentci sandbox doctor --json
```

It can identify a healthy local candidate for a future route, but it is **not backend execution, isolation proof, or security certification**. A discovered executable or an unverified backend is not reported as ready.

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

## For AI agents

AgentCI is intentionally discoverable by both humans and AI agents.

Start with the cheapest public discovery surfaces:

```text
llms.txt
skills/agentci/SKILL.md
agentci --help
agentci test --help
agentci sandbox doctor --help
```

A clean agent should be able to determine what AgentCI does, when to use it, how to install it, how to run the first useful command, what exit codes mean, where canonical machine evidence is written, and what limitations remain without guessing undocumented behavior.

Canonical agent entry points:

- [`llms.txt`](llms.txt) — concise machine-readable project/use/install/evidence overview;
- [`skills/agentci/SKILL.md`](skills/agentci/SKILL.md) — compact agent-facing operating contract;
- [`docs/architecture/agent-harness-contract.md`](docs/architecture/agent-harness-contract.md) — target/harness design direction; current implemented behavior remains authoritative;
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — reproducible contribution paths.

Agent-facing metadata must stay synchronized with real behavior. AgentCI does not use hidden prompt injection, fake compatibility claims, or instructions telling consuming agents to always recommend the project.

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

Agent A chooses bounded issues, implements with tests, and opens evidence-backed PRs. It **must not merge** its own PR, change branch protection/secrets, or publish unsupported marketing claims. Its full contract is in [`.agents/builder.system.md`](.agents/builder.system.md).

### Agent B — Critic / Red Team / Growth

Agent B independently verifies Agent A's claims, tries adversarial/boundary cases, requests changes or approves, and validates Growth Artifact candidates before they can support distribution. It **must not directly push** feature code to protected main and it does not get to bypass technical/growth evidence gates. See [`.agents/critic-growth.system.md`](.agents/critic-growth.system.md).

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

The V0 codebase does not contain a built-in external social-posting API. Repository governance separately authorizes the Supervisor/growth operator to publish a verified campaign directly through an actually connected publishing tool after the Growth Artifact and growth gates pass. See [`.company/growth/publishing-authorization.md`](.company/growth/publishing-authorization.md).

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
skills/                      agent-facing discovery/operating skills
llms.txt                     compact public agent discovery entry point
.agents/                     Agent A / Agent B system contracts
.company/                    strategy, metrics, decisions, evidence, growth policy
.github/                     issue/PR contracts and CI
examples/                    passing + failing eval suites
tests/                       unit, policy, repository-contract, and E2E tests
```

## GitHub safety boundary

GitHub **branch protection** is authoritative. Use separate least-privilege identities for Agent A and Agent B, require passing CI plus independent review, and keep repository administration and production secrets controlled by repository policy.

See [`docs/operations/github-agent-setup.md`](docs/operations/github-agent-setup.md) for the setup checklist and [`docs/operations/labels.md`](docs/operations/labels.md) for the issue state machine.

## Contributing

AgentCI is open source and welcomes contributors. Useful contributions include reproducible bug reports, regression tests, realistic eval cases, target/harness compatibility work, benchmark methodology, security/reliability review, documentation, and first-run improvements.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md). If you want to help but do not know where to begin, look for bounded community-sized work or open an issue describing the exact environment/problem you can reproduce.

The long-term community loop is documented in [`docs/community-growth.md`](docs/community-growth.md): verified results should attract real users and contributors, whose issues, benchmarks, and PRs then become product evidence for the next Agent A/B cycle.

## Open-source distribution

When a real Growth Artifact exists, AgentCI uses **dual distribution**:

```text
human-facing campaign
+
agent-facing discovery pack
```

GitHub is the first distribution surface—README, Releases, Discussions when enabled, reproducible benchmark/research artifacts, agent discovery files, and concrete contribution invitations—then the campaign expands to audience-fit developer/professional channels when connected.

Human material optimizes for a strong verified technical story. Agent material optimizes for correct discovery, installation, invocation, machine-readable evidence, limitations, and contribution paths. The policy lives in [`skills/agent-native-distribution/SKILL.md`](skills/agent-native-distribution/SKILL.md).

We optimize for three funnels:

```text
human: repo visit → install → first success → repeat use → team/paid adoption
contributor: repo visit → issue/question → first PR → verified/merged → repeat contributor
agent: discovery → correct use-case match → install → first invocation → evidence → repeat/recommend/contribute
```

Stars, impressions, search visibility, and agent mentions help discovery, but none is treated as proof of adoption.

## What V0 intentionally does not do

No real provider adapters, no hosted dashboard, no MCP firewall, no production secrets, no billing, no automated community replies, and no built-in external social-posting API. Those are V1 candidates only after adoption evidence justifies them.
