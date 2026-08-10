# AgentCI Domain Context

This file is the shared vocabulary for humans and agents working on AgentCI. It is a glossary, not a roadmap or implementation spec.

## Canonical terms

- **AgentCI** — the project: an evidence-first CI/reliability/security layer for AI agents and agent-facing harnesses.
- **Eval Suite** — a named collection of eval cases evaluated together.
- **Eval Case** — one bounded input plus expected behavior/limits and measured result.
- **Fixture Mode** — deterministic V0 mode where result data is supplied by the eval file rather than produced by a live target.
- **Executable Target** — a real local program/process invoked by AgentCI to produce a result for an eval case.
- **Target Harness** — the stable machine-facing interface around an executable agent/tool/backend that AgentCI can inspect, execute, and verify.
- **Harness Contract** — the versioned AgentCI rules for target manifests, machine-readable transport, limits, introspection, errors, evidence, and optional trajectory data.
- **Target Manifest** — machine-readable declaration of target identity, transport, command, capabilities, and limits. A declaration is not proof.
- **Doctor** — a cheap compatibility/readiness probe. Doctor may prove that a target appears compatible; it does not prove task correctness.
- **Trajectory** — ordered run/case event evidence associated with execution. When supported, it is append-only evidence, not an editable narrative log.
- **Canonical Evidence** — the machine-readable artifact that a claim ultimately traces to: tests, CI, raw benchmark output, facts.json, exact reproduction, or equivalent primary evidence.
- **Regression** — previously accepted behavior that now fails under the same valid conditions.
- **Falsification** — an independent attempt to disprove a claim by reproduction, boundary cases, adversarial inputs, or comparison with canonical evidence.
- **Agent A** — Builder / Researcher / Product Operator. Produces bounded changes and evidence.
- **Agent B** — independent Critic / Red Team / Benchmark / Growth operator. Attempts to falsify A's claims before accepting them.
- **Supervisor** — coordinates the product loop, external intelligence, priorities, and command issues. It does not replace independent verification.
- **CMD:A / CMD:B** — GitHub command issues containing the current primary objective for Agent A or Agent B.
- **P0 / P1 / P2 / P3** — severity levels from critical stop-the-line risk through minor polish. A reproducible P0/P1 normally outranks unrelated feature work.
- **Growth Artifact** — a validated, reproducible technical result strong enough to support public communication: benchmark, capability, dataset, integration, performance result, disclosure-ready security finding, or comparable evidence.
- **Growth Gate** — the evidence/policy check that a candidate must pass before promotion.
- **Growth Pack** — platform-specific promotional assets generated from one validated Growth Artifact and its canonical facts.
- **Distribution** — evidence-gated publication and community outreach intended to create qualified users and contributors, not vanity attention.
- **Qualified Adoption** — behavior such as install, first successful run, repeat use, integration, team use, or paid conversion; stars/impressions alone are not qualified adoption.
- **Contributor Funnel** — repo visit → issue/question → first PR → independently verified/merged → repeat contributor.
- **H1 / H2 / H3 / H4** — harness roadmap waves: H1 stable executable target; H2 manifest/doctor/conformance; H3 trajectory evidence; H4 ecosystem/certification only after evidence justifies it.
- **Harness Certification** — proposed/experimental AgentCI use case: independently assess whether third-party agent-native harnesses satisfy reusable reliability/conformance properties. It is not an endorsement or security guarantee.

## Language rules

Use these canonical terms in issues, PRs, code comments, docs, benchmarks, and reports when they match the concept. If a new term overlaps an existing term, resolve the distinction before introducing it. If code behavior and this glossary disagree, surface the contradiction instead of silently redefining the term.
