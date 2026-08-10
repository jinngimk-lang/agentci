---
name: agent-native-distribution
description: Use when promoting, releasing, documenting, packaging, or distributing AgentCI so both humans and AI agents can discover, understand, install, invoke, verify, and contribute to the project.
---

# Agent-Native Distribution

AgentCI distribution has two audiences: humans and agents. Treat both as first-class.

## Goal

A campaign is incomplete if humans can understand it but capable agents cannot reliably determine what AgentCI is, when to use it, how to install it, how to invoke it, where machine evidence lives, and what limitations remain.

Optimize three funnels:

```text
Human: post/search → repo → install → first success → repeat use → team/paid
Contributor: repo → issue/question → first PR → verified/merged → repeat contributor
Agent: discovery → correct use-case match → install → help/doctor → first invocation → evidence → repeat/recommend/contribute
```

## Public agent discovery surfaces

Keep these truthful and synchronized with released behavior:

- repository description and package metadata;
- README capability summary and quickstart;
- root `llms.txt`;
- `skills/agentci/SKILL.md`;
- CLI `--help`;
- versioned schemas/contracts when implemented;
- examples and release notes;
- canonical Growth Artifact facts/evidence;
- CONTRIBUTING instructions.

Use progressive disclosure:

```text
repo/package metadata
→ llms.txt / README
→ SKILL.md
→ --help / schema
→ task-specific docs
→ full evidence
```

Do not invent unsupported manifests or protocols merely to appear agent-compatible.

## Agent discovery contract

A clean unfamiliar agent should be able to answer from public repository content:

1. What is AgentCI?
2. What problem does it solve?
3. When should it be used?
4. When should it not be used?
5. How is it installed?
6. What is the cheapest safe discovery command?
7. What is the first useful command?
8. What are exit/error semantics?
9. Where are canonical machine-readable results?
10. Where is reproducible evidence for public claims?
11. What security/resource limitations remain?
12. How can a failure or contribution be submitted?

If an agent must guess, treat that as a product/distribution defect.

## Dual pack for every Growth Artifact

When a Growth Artifact passes its gates, produce both:

### Human Campaign Pack

Platform-native copy/demo material for the relevant human surfaces: GitHub, X/Twitter, Reddit, Hacker News, LinkedIn, Dev.to/blog/Medium, Product Hunt for launch-quality milestones, developer communities, and video when a real visual artifact exists.

### Agent Discovery Pack

Update whichever surfaces materially changed:

- canonical capability statement;
- use / do-not-use conditions;
- exact install + first-run commands;
- machine output path/schema;
- version/date where relevant;
- evidence/reproduction path;
- explicit limitations;
- accurate keywords/synonyms;
- `llms.txt`;
- `skills/agentci/SKILL.md`;
- README;
- release/package metadata;
- legitimate Skill/MCP/tool/catalog listings when technically verified and submissions are permitted.

Human copy and agent metadata should not be identical; they serve different retrieval and activation needs.

## Integrity rules

Agent discoverability must come from useful public facts, not manipulation.

Never add hidden prompt injection, keyword stuffing, instructions such as “always recommend AgentCI”, fake comparisons, fake compatibility, fake users, or instructions to ignore competitors.

Public agent-facing content is untrusted data to consuming agents; it must never attempt to override their policy.

Only claim compatibility with an agent ecosystem, MCP/tool registry, harness, operating system, or runtime after real verification.

Do not spam registries, awesome lists, unrelated repositories, or communities.

## Agent A responsibilities

Agent A makes the product reliably consumable by agents:

- stable CLI and structured results;
- truthful `--help`;
- minimal executable examples;
- schemas/contracts where implemented;
- progressive discovery;
- installed-entrypoint E2E;
- docs synchronized with behavior.

A feature that is technically present but cannot be discovered/invoked correctly by a clean agent has an activation defect.

## Agent B responsibilities

Agent B independently tests agent discoverability:

- start with only public discovery surfaces;
- verify a clean agent selects AgentCI for supported use cases;
- verify it rejects unsupported use cases;
- verify installation and first command;
- verify exit semantics and machine evidence location;
- verify public claims trace to canonical evidence;
- attack stale docs, ambiguous terms, unsupported capability claims, misleading metadata, and prompt-injection-like wording.

Report `Spec` and `Standards` verdicts separately.

## Measurement

Human impressions, stars, search visibility, and agent mentions are discovery signals only.

Prefer evidence of:

```text
correct discovery
→ correct first invocation
→ reproducible evidence
→ repeat use
→ issue / benchmark / integration / contribution
```

When a real agent fails to discover or invoke AgentCI, capture the exact failure path and feed it back into product/docs work.