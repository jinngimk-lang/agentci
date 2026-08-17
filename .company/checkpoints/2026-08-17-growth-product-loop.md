# AgentCI Growth + Product Loop Checkpoint

Date: 2026-08-17
Owner mode: autonomous, evidence-first, long-running loop

## Recovery source

- Latest checked `main`: `b177e5cfb477a365818bccc700b95e948b0317aa`
- Latest main commit message: `growth: record confirmed outreach batch 002`
- Latest observed main CI: run `31987776126`, conclusion `success`
- Existing screenshot/visual artifact gate: not applicable to the current CLI/evidence-verifier product surface; no current UI screenshot artifact was found in the repository tree. If a visual UI is introduced, add screenshot/playtest evidence before release claims.

## Growth state

Two counts must remain distinct:

1. **Repository-audited outreach:** 77 confirmed public writes are persisted in `.company/growth/outreach-2026-08-17-batch-001.json` and `batch-002.json`.
2. **Session-confirmed outreach:** 124 successful external public writes have been observed in the active execution session. Failed/403/skipped attempts were excluded. The 47-write delta above the repository-audited count still needs URL reconciliation into a later audit manifest before it should be treated as repository-audited.

Do not collapse these counts. Future recovery should start from repository evidence, then reconcile any session-confirmed delta.

## Current growth bottleneck

The repository is public but GitHub metadata remains weak for conversion/discovery: description is empty, topics are empty, homepage is empty, releases are empty, and license metadata is absent. Stars/watchers/forks were still 0 at the latest check. Traffic Insights is not readable through the current GitHub App (403), so do not invent view counts.

Outreach alone is not a release/growth gate. The conversion surface must make the value obvious within seconds and provide a direct `doctor` / `verify` / Breaker Challenge path.

## Promotion rule

External promotion means external repositories/discussions/communities. Comments/posts inside `jinngimk-lang/agentci` are landing-page/support assets and do not count as external outreach.

Successful outreach should be:
- highly relevant to the external thread;
- human-sounding and context-specific;
- framed as pain point -> falsifiable breaker/solution -> concrete AgentCI participation path;
- transparent about affiliation with AgentCI;
- linked to real, non-cash rewards only: durable public credit, accepted breaker provenance, Hall-of-Fame/spotlight, priority conversion help;
- never counted if the write failed, was skipped, or was only drafted.

Respect platform rate limits and repository permissions. Do not turn the campaign into duplicate unsolicited spam.

## Pain-point synthesis queue

Repeated external pain points already observed and worth productizing after sufficient corpus:

- configured / advertised / healthy != effective capability;
- requested provider/backend/policy != effective runtime selection;
- approval/decision not uniquely bound to the effect that executes;
- replay/retry duplicates a non-idempotent side effect;
- cancel/cleanup reports terminal success while descendants/state/resources remain;
- resume/restore reuses stale provider, authority, stream, or lifecycle identity;
- resource limits are configured but enforced too late or on the wrong execution path;
- tool catalog/cache mutation causes effective capability drift;
- telemetry/observer health is mistaken for proof of the claimed enforcement event;
- durable history persists data but not the exact effective execution semantics;
- run-level terminal success can coexist with missing utility/output evidence;
- cross-agent/sibling identity substitution weakens authorization or isolation.

## Next loop order

1. Read latest `main` and this checkpoint.
2. Read latest open PR/CI state.
3. Reconcile the 47 session-confirmed but not-yet-repository-audited outreach writes into the next manifest when URLs can be verified.
4. Continue external high-relevance outreach in bounded batches; successful writes only increment the count.
5. In parallel, fix the highest-value conversion gap that is writable through available GitHub APIs/repository files.
6. Once the outreach corpus is large enough, cluster pain points by frequency, severity, cross-framework recurrence, and AgentCI differentiation; convert the top cluster into RED -> GREEN product work.
7. Do not claim completion until release gates are met. Do not claim provider/security certification without matching real evidence.

## Stop conditions

Stop only for a real release gate completion, explicit owner pause/change, legal/paid/credential/irreversible-high-risk boundary requiring owner action, or a genuine external platform/permission block. Otherwise continue from this checkpoint rather than relying on chat memory.
