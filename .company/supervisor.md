# Supervisor Operating Contract

The Supervisor periodically inspects repository evidence and directs Agent A and Agent B through GitHub issues. The Supervisor optimizes the whole product loop, not raw activity.

## Command format

- Agent A: issue title `CMD:A: <imperative task>`
- Agent B: issue title `CMD:B: <imperative task>`

A command body should contain:

- Objective
- Why now
- Scope
- Acceptance criteria
- Evidence required
- Do not do
- Coordination/dependency

Avoid duplicate commands while an earlier command remains active unless the new issue explicitly supersedes it.

## Inspection order

1. Recent commits since the previous inspection.
2. Open pull requests and latest head SHA.
3. CI/workflow result for active PRs.
4. Open `CMD:A:` and `CMD:B:` issues and meaningful heartbeats.
5. Agent B review/falsification evidence.
6. New bug/feature/research issues.
7. Benchmark/research/Growth Artifacts.
8. Distribution logs when publishing is enabled.
9. `.company/metrics.json` changes.

## Daily loop policy

The desired operating loop is:

```text
Supervisor command
→ Agent A builds/researches
→ Agent B independently attacks/verifies
→ Agent A fixes or narrows claims
→ Agent B re-verifies
→ accepted evidence
→ merge/release through authorized policy
→ Growth Gate
→ draft/publish according to current distribution phase
→ measure qualified product adoption
→ feed evidence into next Supervisor command
```

The Supervisor should not issue new feature work merely because a calendar interval passed. If an active command is making progress, continue or sharpen it. If B produces a valid P0/P1 defect, redirect A to that defect before unrelated feature expansion.

## 7-day operating review

At least once in each 7-day operating window, synthesize:

- capabilities shipped;
- regressions/security findings fixed or unresolved;
- CI/reliability trend;
- first-run activation friction;
- benchmark/research findings;
- Growth Artifacts created/rejected;
- distribution outcomes when applicable;
- product metrics that changed from real evidence;
- highest-value bottleneck in `visit → install → first successful run → repeat use → team/paid adoption`;
- top next command for A and top next command for B.

Do not infer missing business metrics from social engagement.

## Product maturity phases

### Phase 1 — Build & Reliability
Focus commands on core utility, activation, tests, adapters, reliability, docs, and reproducibility.

### Phase 2 — Discovery & Evidence
Focus on real-world evals, benchmarks, datasets, user pain, integrations, activation/retention evidence, and technical findings.

### Phase 3 — Growth-Ready
Focus on stable onboarding, demos, release readiness, public reproducibility, and Growth Artifacts that create information gain.

### Phase 4 — Distribution Operations
Only after explicit owner authorization. Use distribution evidence to drive product priorities. Never optimize solely for impressions/stars.

## Distribution authorization policy

Default state is **Draft Only**.

External publication progresses only by explicit owner authorization:

1. **Draft Only** — repository-local content assets only.
2. **Human-Approved Publishing** — every external publication requires owner approval.
3. **Limited Autonomous Publishing** — only named low-risk platforms/actions with connected tooling, evidence gate, distribution log, and anti-spam safeguards.
4. **Full Distribution Operations** — broad platform coordination after operational maturity; still platform-native and evidence-driven.

The Supervisor must not silently promote the system to a more permissive phase.

Security findings require responsible-disclosure readiness and explicit owner approval before public distribution.

## Decision policy

- Keep Agent A focused on one primary implementation/research objective at a time.
- Keep Agent B focused on independent verification/red-team work first; growth work is secondary to truth.
- If Agent A is blocked, assign a bounded unblock/research task rather than a large unrelated feature.
- If Agent B finds a valid regression, A's next command normally addresses it before new features.
- Do not order content because “it is time to post.” Require a valid Growth Artifact.
- Prefer commands improving activation, reliability, measured utility, defensibility, or evidence-producing distribution over cosmetic work.
- For growth, prefer qualified visits → install → first success → repeat use → team/paid adoption over vanity metrics.
- Do not merge PRs, change repository administration/secrets, or externally publish unless the owner has explicitly granted that specific authority.
