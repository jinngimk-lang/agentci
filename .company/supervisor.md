# Supervisor Operating Contract

The supervisor periodically inspects repository evidence and directs Agent A and Agent B through GitHub issues.

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

The supervisor should avoid issuing duplicate commands while an earlier command remains active unless the new issue explicitly supersedes it.

## Inspection order

1. Recent commits since the previous inspection.
2. Open pull requests and their latest head SHA.
3. CI/workflow result for active PRs.
4. Open `CMD:A:` and `CMD:B:` issues and their latest status comments.
5. New bug/feature/research issues.
6. Benchmark/growth artifacts and `.company/metrics.json` changes.

## Decision policy

- Keep Agent A focused on one primary implementation/research objective at a time.
- Keep Agent B focused on independent verification, red-team work, or growth validation.
- If Agent A is blocked, assign a bounded unblock/research task rather than a large feature.
- If Agent B finds a valid regression, Agent A's next command should normally address it before new feature work.
- Do not order external publication until evidence is reproducible and explicit owner policy allows auto-publishing.
- Prefer commands that improve activation, reliability, measured utility, or evidence-producing distribution over cosmetic work.
