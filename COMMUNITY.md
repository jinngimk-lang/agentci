# AgentCI Community: Builders, Breakers, and Verifiers

AgentCI is built around a simple idea: **a counterexample is a contribution**.

If you can make AgentCI claim something stronger than its evidence supports, find a runtime edge case, expose a false PASS, reproduce a cleanup leak, or tighten a verification rule without creating a second source of truth, we want that work visible and credited.

## What gets recognized

### Breaker Hall of Fame

For the first person or external agent to submit a **new, reproducible, material counterexample** that survives triage and causes a test, contract, implementation, or documentation change.

Recognition includes:

- permanent public credit in the Hall of Fame section below;
- link to the reproducer / issue / PR;
- a short write-up of what the counterexample changed;
- priority technical review for the follow-up fix;
- optional contributor spotlight in a release or launch update.

### Verifier Hall of Fame

For external developers or agents who independently reproduce a release claim or verify a fix from a clean environment.

Recognition includes:

- permanent public credit with the exact version/head verified;
- link to the evidence or report;
- priority review for future verification reports.

### Builder Spotlight

For contributors who close a falsifiable gap with tests and evidence while preserving AgentCI's truth boundaries.

Recognition includes public credit and a link to the delivered change.

## What counts as a valid challenge

A strong submission contains:

1. **Exact target** — version, commit, platform/runtime, and relevant configuration.
2. **Falsifiable claim** — what AgentCI appears to claim and what you think is wrong or incomplete.
3. **Safe reproduction** — no destructive host tests, credential exfiltration, or unrelated production impact.
4. **Observed evidence** — commands, logs, fixtures, or machine-readable output sufficient for another person/agent to reproduce.
5. **Expected boundary** — what should become `FAIL`, `PARTIAL`, `UNVERIFIED`, or otherwise change.

A backend name, configuration screenshot, or "it feels unsafe" report is useful context but is not enough by itself for Hall of Fame recognition.

## Good targets to break

- `agentci sandbox doctor` reporting readiness too strongly;
- evidence that incorrectly reaches PASS with missing or mismatched telemetry;
- authority decisions that can be replayed, widened, cross-tenant, or detached from enforcement;
- cleanup where descendants, sockets, files, credentials, or lifecycle state survive unexpectedly;
- restore/recovery paths that silently inherit stale authority;
- packaging/install paths where the shipped verifier differs from the canonical repository contract;
- provider/runtime facts that AgentCI accidentally promotes into a security verdict.

## For agents

External agents are welcome. If an agent finds the issue, credit can name the agent plus its operator/project, provided the report is reproducible and the attribution is not misleading.

Suggested report header:

```text
Reporter: <human / agent / human+agent>
Target: <commit/version>
Claim under test: <one sentence>
Reproduction: <commands or fixture>
Observed result: <what happened>
Expected result: <what should happen>
Safety boundary: <why the repro is non-destructive>
```

## Hall of Fame

No entries are pre-populated. Credit is added only after a real external contribution is independently reproducible and accepted.

| Role | Contributor | Target | Contribution | Evidence |
|---|---|---|---|---|
| — | — | — | Waiting for the first qualifying external breaker/verifier | — |

## Start here

- Launch / public challenge: https://github.com/jinngimk-lang/agentci/issues/118
- Contributor call: https://github.com/jinngimk-lang/agentci/issues/42
- Real-host tester call: https://github.com/jinngimk-lang/agentci/issues/41

**Important:** recognition is not a cash bounty and does not imply employment, certification authority, or a security guarantee. We do not invent rewards or claim independent verification that did not happen.
