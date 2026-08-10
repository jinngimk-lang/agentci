# Publishing Authorization

Owner authorization date: 2026-08-10

## Current phase

**Authorized Autonomous Publishing** for `jinngimk-lang/agentci`.

The owner authorizes the Supervisor / growth operator to publish evidence-backed AgentCI promotion directly when a Growth Artifact passes the repository's technical and growth gates, without requesting per-post approval.

## What is authorized

When tooling/credentials are actually connected and the platform permits the action, the Supervisor may directly publish:

- GitHub-native launch/research/community updates;
- release and project milestone promotion;
- X/Twitter posts and threads;
- Reddit posts in relevant communities where self-promotion rules permit;
- Hacker News / Show HN submissions when technically appropriate;
- LinkedIn posts;
- Dev.to / Medium / technical blog articles;
- Product Hunt launch materials for launch-quality milestones;
- relevant developer-community announcements;
- demo/video scripts and posts where a real visual artifact exists;
- truthful public agent-discovery updates such as `llms.txt`, `SKILL.md`, README/package metadata, release notes, examples, schemas/contracts when implemented, and legitimate agent/tool/Skill/MCP/catalog listings when technically verified and submissions are permitted.

The Supervisor may adapt copy per platform and choose timing based on evidence, audience fit, community norms, language, and agent-discovery needs.

## Dual distribution requirement

Promotion should target both humans and capable AI agents.

For every suitable Growth Artifact, produce separate human-facing and agent-facing outputs.

### Human Campaign Pack

Human-facing material should use a strong truthful hook, concrete developer pain, evidence-backed result, reproducibility/limitations, and a clear Try / Contribute / Challenge-us CTA.

### Agent Discovery Pack

Agent-facing material should make it easy for an unfamiliar agent to determine:

- what AgentCI is;
- when to use or not use it;
- exact installation and cheap discovery commands;
- the first useful invocation;
- exit/error semantics;
- where canonical machine-readable evidence lives;
- what capabilities are implemented vs design-only;
- security/resource limitations;
- how to contribute or report a reproducible failure.

Update the relevant public surfaces when a capability materially changes: `llms.txt`, `skills/agentci/SKILL.md`, README, CLI help, package/release metadata, examples, schemas/contracts, evidence links, or legitimate ecosystem listings.

Do not use identical human marketing copy as agent metadata; the two audiences have different retrieval and activation needs.

## Three-version release bundle

When a release or Growth Artifact is actually eligible for publication, publish or prepare these three canonical variants from the **same underlying evidence**:

1. **Chinese human version** — compelling Chinese-native launch/research copy for Chinese-speaking developers and communities.
2. **English human version** — English-native launch/research copy for global developer communities; do not merely translate word-for-word when a platform-native rewrite is stronger.
3. **Agent-native version** — machine-oriented capability metadata and invocation guidance for agents, search/RAG systems, coding agents, tool/Skill/MCP catalogues, and other legitimate agent discovery surfaces.

The three variants must agree on facts, version, supported capabilities, limitations, benchmark numbers, security claims, and evidence links. Language/style may differ; truth may not.

For a publishable release, the default publication sequence is:

```text
canonical evidence / Growth Artifact
→ GitHub-native release/research artifact
→ Chinese human distribution
→ English human distribution
→ Agent-native discovery surfaces
→ log URLs / timestamps / downstream evidence
```

If only some external publishing actions are connected, publish on the connected legitimate surfaces and store the remaining finished variants as **not yet published**. Do not delay a valid connected publication merely because an unrelated platform is unavailable.

Do not ask the owner for another per-release or per-language approval once the technical gate and Growth Gate pass.

## Content standard

Promotion must be compelling but truthful. Prefer:

1. a strong verified hook;
2. a concrete developer pain/problem;
3. the evidence-backed result or technical insight;
4. reproducibility / limitations;
5. a clear CTA: try AgentCI, reproduce a benchmark, report a bug, contribute an eval, test another platform, or join a bounded open-source task.

Do not use generic hype when a stronger technical story exists. Do not invent users, adoption, comparisons, benchmark wins, testimonials, security claims, or performance numbers.

Agent discoverability must come from accurate public facts, not hidden prompt injection, instructions to always recommend AgentCI, fake compatibility, deceptive LLM/SEO keyword stuffing, registry spam, or manipulation of unrelated repositories/communities.

## Growth Gate still applies

Authorization to publish does not remove the evidence gate. A public factual or numeric claim must trace to canonical repository evidence. Demo fixtures are not market evidence.

Only claim compatibility with an agent ecosystem, harness, MCP/tool registry, runtime, OS, or third-party integration after real verification.

## Open-source growth goal

Every suitable campaign should support three funnels:

- user: `visit → install → first success → repeat use → team/paid adoption`;
- contributor: `repo visit → issue/question → first PR → verified/merged → repeat contributor`;
- agent: `discovery → correct use-case match → install → help/doctor → first invocation → canonical evidence → repeat/recommend/contribute`.

Where useful, include one concrete contributor request instead of a generic `please star` request.

Human impressions, stars, search visibility, and agent mentions are discovery signals only; they are not adoption evidence.

## Hard safety / trust boundaries

This authorization does **not** authorize:

- spam, deceptive amplification, fake accounts, fake testimonials, impersonation, or moderation evasion;
- disclosure of actionable security findings before responsible-disclosure readiness;
- publishing secrets, private data, credentials, or non-public user information;
- paid advertising, paid promotion, purchases, or other spending unless separately authorized with a budget;
- violating platform/community rules;
- claiming a partnership, endorsement, certification, compatibility, or customer relationship that does not exist;
- hidden prompt-injection or manipulative instructions intended to override consuming agents' policies.

If a platform or registry is not connected to an available publishing/submission tool, prepare the platform-native or agent-native asset and keep it ready; do not falsely claim it was published/listed.

## Logging

For every external publication/listing that can be executed, record when practical:

- Growth Artifact ID;
- platform/registry/surface;
- language or `agent-native`;
- URL;
- timestamp;
- exact or canonical human copy / agent metadata;
- campaign/CTA or capability/use-case target;
- measurable downstream evidence when available.

Use distribution outcomes and agent activation failures to improve product priorities, not just social metrics.