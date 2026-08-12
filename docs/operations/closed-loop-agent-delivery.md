# Closed-Loop Agent Delivery

Status: active Owner-authorized operating workflow for AgentCI. This document defines how A–E, Supervisor, External Verifier, and external contributors keep work moving without collapsing review independence.

## Core model

Specialization is persistent; per-change execution identity is flexible.

Agents A–E keep specialist home domains, but for any single change they may rotate through these work identities:

1. **External User** — uses AgentCI as an unknown external agent/developer would, with no hidden project memory.
2. **Finder** — turns an observed defect, contradiction, false-PASS, usability failure, or external contribution into one falsifiable problem.
3. **Planner** — records the smallest reproducible correction plan, evidence required, owner role, and next handoff.
4. **Fixer** — owns one isolated branch/PR and the smallest RED→GREEN correction.
5. **Challenger** — independently attacks the exact head/claim without editing the fix under review.
6. **Merge Decider** — chooses `MERGE | RETURN | NARROW | BLOCK`; when `MERGE`, may merge the exact expected head to `main` under standing Owner authority.

**Hard separation:** `Fixer != Merge Decider` for the same change.

For security-, S0-, authority-, evidence-, runtime-, or release-critical changes, prefer three-role separation:

```text
Fixer
  ↓ exact immutable head
Challenger
  ↓ independent attack/verdict
Merge Decider
  ↓ expected-head merge
main
  ↓ post-merge verification
```

For bounded low-risk docs/routing/maintenance, Fixer + independent Merge Decider is sufficient when scope, RED/contract evidence, CI, and public-claim boundaries are clean.

## Default specialist homes

These are routing defaults, not permanent approval identities:

- **Agent A** — canonical product/schema/probe integration.
- **Agent B** — adversarial falsification, Spec + Standards review.
- **Agent C** — isolation/runtime/process/resource/device/IPC/lifecycle semantics.
- **Agent D** — authority/identity/credentials/network-policy semantics.
- **Agent E** — evidence/telemetry/replay/cleanup semantics.
- **Supervisor** — WIP, conflicts, stage gates, role assignment and audit.
- **External Verifier** — clean public-only perspective; never an approval authority.

Any A–E role may temporarily become Finder, Planner, Fixer, Challenger, or Merge Decider if separation of duties remains intact.

## The no-wait closed loop

Actionable work must not become idle merely because one role is waiting.

```text
External User / contributor
        ↓
      Finder
        ↓
      Planner
        ↓
      Fixer
        ↓
 exact head + evidence
        ↓
    Challenger
        ↓
 Merge Decider
   ↙          ↘
RETURN        MERGE
  ↓             ↓
re-route       main
  ↓             ↓
next Fixer   post-merge verify
                ↓
           next highest-value claim
```

### No-wait rules

- If a role is blocked on another role's output, it takes the next non-conflicting useful task in its specialist queue or temporary assigned role.
- If a PR head/base drifts, the Merge Decider returns it immediately to a different Fixer/reconciliation role; stale green evidence is never a waiting reason or merge authorization.
- If a Challenger finds a valid counterexample, route the smallest correction immediately; do not keep reviewing unchanged heads.
- If there is no new evidence, do not generate status noise. Work should move to another falsifiable claim, external reproduction, or bounded research input.
- One problem has one active Fixer. Avoid duplicate repair PRs unless Supervisor explicitly requests independent variants.
- Preserve one immutable review batch per exact head; a changed head requires fresh review evidence.

## Workflow selection by task

Use the smallest workflow that preserves evidence quality.

### 1. Behavioral bug / false-PASS

Use test-driven RED→GREEN:

```text
reproduce exact failure
→ write failing regression
→ confirm RED for the intended reason
→ smallest implementation correction
→ targeted + full GREEN
→ Challenger attack
→ Merge Decider
```

Do not write the fix before proving the regression catches the defect when a deterministic test is feasible.

### 2. Hard debugging / unexpected failure

Use systematic debugging:

```text
observe
→ isolate root cause
→ distinguish product vs environment failure
→ create smallest reproduction
→ only then patch
```

Do not patch symptoms or classify DNS/runtime/provider limitations as AgentCI defects without evidence.

### 3. Sandbox research / architecture uncertainty

Use claim-driven convergence:

```text
falsifiable semantic claim
→ primary-source/domain evidence
→ portable vs backend-specific boundary
→ canonical contract delta or explicit UNRESOLVED
→ B/Challenger falsification
→ ACCEPT | RETURN | NARROW | BLOCK
```

Research must terminate in a falsifiable contract, test, probe, decision, or explicit unresolved limitation; avoid endless landscape reporting.

### 4. Security-critical change

Require independent challenge before main:

```text
Fixer
→ exact head + threat/counterexample coverage
→ independent Challenger
→ Merge Decider
→ main
→ post-merge verification
```

A green CI run is necessary but not sufficient. A valid unresolved counterexample blocks merge.

### 5. Public docs / agent-facing contract

Treat README, `llms.txt`, `AGENTS.md`, Skills, CLI help, and evidence links as public APIs. For important drift, add a repository-contract RED test, then make the smallest synchronized correction.

Do not make design-stage sandbox commands or certification claims look released.

### 6. External contribution

Every external contribution — issue, PR, patch, benchmark suggestion, semantic objection, or external-agent finding — enters the same evidence loop.

```text
external contribution
→ acknowledge + classify domain
→ reproduce or mark UNVERIFIED
→ de-duplicate existing work
→ extract one falsifiable claim
→ assign one Fixer if a correction is needed
→ independent challenge/review
→ Merge Decider
→ main verification
→ credit contributor / preserve provenance
```

Do not merge because an external contribution is popular, confident, or CI-green. Do not discard it because it conflicts with internal assumptions; reproduce first.

### 7. Base drift / merge conflict

Base drift is a routing event, not a waiting state.

The Merge Decider must `RETURN`, not silently edit the branch. Assign a different Fixer/reconciliation role, preserve the semantic change and already accepted main work, create a new exact head, rerun CI, and hand it back to a decider.

## Merge decision contract

Before `MERGE`, the Merge Decider must inspect live state rather than memory:

- exact PR head and current base;
- scope versus stated claim;
- RED evidence when behavior/contract regression is involved;
- exact-head CI / required Regression evidence;
- unresolved review threads or valid counterexamples;
- public/released claim truthfulness;
- whether the decider authored any part of the fix;
- mergeability of the live head/base.

Use expected head protection for the merge. If the head moved, do not merge.

After merge, verify the exact resulting `main` commit and required main CI. A branch being green does not prove the merged main state is healthy.

## External User / External Agent loop

A–E may deliberately rotate into an External User identity to use AgentCI from public surfaces only:

```text
README / llms.txt
→ AGENTS / Skill
→ install / CLI help
→ first useful invocation
→ evidence / limitations
→ contribution path
```

Do not use private conversation memory to repair missing public instructions mentally. If a clean agent must guess, that is a product/discoverability finding.

The role that finds the issue should normally stop after reproduction + plan when another available role can fix it. This preserves diversity and increases throughput.

## Mainline continuity

The primary Sandbox Program continues while repair loops run.

- Keep S0/S1 stage gates and provider-neutral direction intact.
- Specialists can continue non-conflicting research/probes while another role fixes a bounded defect.
- Supervisor should continuously select the highest-value unblocked claim rather than letting the team wait on one PR.
- Do not start duplicate work merely to look busy.
- P0/P1 or valid security counterexamples preempt lower-value work when they block a current claim/stage.

## Learning and workflow improvement

The team should continuously adopt better engineering workflows when they materially improve evidence, safety, or throughput. Examples include test-driven development, systematic debugging, immutable exact-head review, parallel specialist research, claim-driven convergence, external-user verification, and post-merge verification.

New workflow patterns are experiments, not doctrine by popularity. Keep them when they reduce false confidence, duplicate work, or waiting while preserving independent review. Remove or narrow them when evidence shows extra ceremony without value.

Record durable workflow improvements here or in a directly linked canonical operation document so every agent can discover them from the repository.

## Invariants that never rotate

Role flexibility does not change these project invariants:

- observation is not authority;
- Fixer != Merge Decider;
- missing material observability cannot become PASS;
- backend name is not a security verdict;
- configured/present is not verified/effective;
- no unilateral privilege expansion;
- no fabricated evidence, users, benchmarks, provider claims, or adoption;
- no destructive sandbox escape work on the host or ordinary CI;
- no secrets in fixtures/issues/logs;
- no premature actionable third-party vulnerability disclosure;
- no merge from stale/moved head evidence.
