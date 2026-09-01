# 50-Touchpoint Campaign Checkpoint — 2026-09-01

## Governing decision

This campaign is attribution-first. Comment volume is not a success metric by itself.

A placement counts only when a public external write exists and its URL is recorded under `agentci.outreach.v2`. Own-repository issues/PRs are product/contributor handoff surfaces and never count as external promotion. Failed, blocked, duplicate, skipped or permission-denied writes remain attempts.

Hidden traffic remains unknown because the current GitHub App does not expose trustworthy Traffic Insights for this workflow. Do not infer views, clicks, visits or causal conversion from timing.

## Proven acquisition path

The strongest observed contributor-conversion path remains:

```text
high-signal LangGraph upstream issue
-> problem-specific AgentCI evidence/fixture invitation
-> upstream author reply
-> bounded AgentCI intake issue
-> external fork / PR
-> verified merge
```

LangGraph #8582 -> AgentCI #123 -> external PR #124 is the canonical prior example. That historical conversion justifies testing additional LangGraph upstream issues; it does not prove that every LangGraph comment will convert.

## Cohort 001

Canonical batch:

`.company/growth/outreach-2026-09-01-50-touchpoint-batch-001.json`

Current public funnel:

```text
confirmed placements: 5
posted: 5
replied: 0
repo_action: 0
contribution: 0
merged: 0
repeat_contributor: 0
blocked attempts: 1
```

The five placements are deliberately within the proven upstream ecosystem but cover distinct semantic failures:

1. LangGraph #8693 — resume identity authority.
2. LangGraph #8653 — persistence authority / state hydration.
3. LangGraph #8686 — migration replay seed semantics.
4. LangGraph #8184 — checkpoint round-trip semantic fidelity.
5. LangGraph #8759 — cross-backend query semantic divergence.

Blocked attempt: `ringier-data/nannos#182` returned HTTP 403 and is not counted.

## Distribution decision

**HOLD additional publication volume after cohort 001 until public downstream state is re-checked.**

Research and candidate scoring may continue, but another five-write cohort should not be published merely to advance the 50-touchpoint counter. Resume external publishing when one of these is true:

- a current placement produces a public reply, repo action or contribution signal;
- a new candidate is materially stronger than the current cohort and supplies a distinct acquisition hypothesis worth testing;
- evidence shows a current channel is saturated or blocked and a bounded alternative-channel experiment is justified.

When publishing resumes, dedupe first and keep every new write problem-specific.

## Product-feedback loop

Distribution is not separate from product work. External failures must improve AgentCI when they reveal a reusable invariant.

Current example: LangGraph #8764 produced AgentCI intake #143 and the `langgraph-8764-accepted-not-durable` provider-neutral fixture candidate. Its invariant separates runtime evidence absence from authoritative external admission and keeps the AgentCI verdict `UNVERIFIED` until independent reproduction.

This product conversion is valuable even though #8764 is not counted as a new campaign placement here.

## Next exact actions

1. Re-check cohort 001 threads for public downstream evidence before cohort 002 publication.
2. Upgrade `downstream_state` only when a public URL proves the event.
3. Complete review/integration of the cohort ledger PR.
4. Complete current-main merge-result verification and independent challenge for the #8764 fixture candidate.
5. Feed repeated semantic clusters into reusable fixtures/checklists/searchable technical assets instead of producing generic promotional copy.

## Claim boundary

This checkpoint proves only public writes, recorded failures and current repository-visible downstream events. It does not prove traffic, adoption, compatibility, backend certification, partnership, endorsement or causal conversion.
