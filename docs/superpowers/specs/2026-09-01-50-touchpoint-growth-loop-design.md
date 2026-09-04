# AgentCI 50-Touchpoint Growth Loop Design

Date: 2026-09-01
Status: owner-approved design; implementation pending plan/review
Repository: `jinngimk-lang/agentci`

## Goal

Create 50 real, searchable acquisition touchpoints that can plausibly convert qualified AI-agent, sandbox, MCP, workflow, and evaluation users into AgentCI repository actions, while continuing to improve the product so arriving users reach a useful deterministic result quickly.

The target is not 50 comments. The target is 50 public acquisition surfaces with observable downstream evidence.

## Core Funnel

```text
qualified public problem/search surface
→ AgentCI-specific technical value
→ public AgentCI link / reusable artifact
→ repository action proxy
→ contribution
→ merge / repeat contributor
```

Observable downstream states remain:

```text
posted
→ replied
→ repo_action
→ contribution
→ merged
→ repeat_contributor
```

Hidden referral traffic, views, clicks, or conversions are never inferred when the available tooling cannot observe them.

PR #141 (`agentci.outreach.v2`) is the intended placement-level evidence layer for new distribution batches. The 50-touchpoint campaign should consume that format once its contract is complete rather than inventing a competing attribution format.

## Distribution Portfolio

The 50-touchpoint target is allocated across four surfaces. Quotas are defaults, not hard ceilings: capacity moves toward channels that produce observable downstream evidence.

### A. High-intent upstream technical threads — target 20

Public GitHub issues/PR discussions where users are already searching for or debugging a failure AgentCI can represent.

Priority semantic classes:

- replay / restore fidelity;
- duplicate non-idempotent effects;
- accepted-but-not-durable execution;
- checkpoint/state immutability;
- cleanup / terminality;
- lost acknowledgement / exactly-once ambiguity;
- tool-result false success / telemetry disagreement;
- execution identity / route drift;
- policy / authority binding;
- sandbox lifecycle/resource residue;
- stale CI / reviewed-head / merge-result evidence;
- cross-provider metadata or capability truth loss.

A placement is eligible only when the comment contributes a concrete fixture shape, invariant, validation method, or claim boundary before mentioning AgentCI.

Do not duplicate an existing AgentCI comment in the same thread. Avoid adjacent-thread flooding in one repository when a prior placement is still awaiting response.

### B. AgentCI-owned searchable conversion surfaces — target 10

Public repository assets designed to answer queries after discovery and to shorten first success.

Examples:

- `QUICKSTART.md` / first-minute flow;
- truth-checked showcase cases;
- failure taxonomy pages;
- fixture contribution guide;
- replay/terminality/authority FAQ pages;
- benchmark/evidence format reference;
- issue templates that accept upstream provenance;
- `llms.txt` and agent-readable routing surfaces;
- search-friendly GitHub issues for specific evidence classes;
- comparison/adoption research pages that clearly distinguish AgentCI from runners.

Each surface must have a real user question/search phrase it answers and a direct next action.

### C. Ecosystem discovery / directory / discussion surfaces — target 10

Places where users deliberately browse tools, benchmarks, eval infrastructure, sandbox infrastructure, MCP tooling, or agent reliability resources.

Candidate surface types:

- relevant Awesome lists;
- ecosystem resource lists;
- benchmark/evaluation catalogs;
- sandbox/runtime tooling indexes;
- agent framework discussions that explicitly invite related tools or evidence methods;
- project showcases / community resource threads;
- integration directories where AgentCI can truthfully register as an independent evidence-verification layer.

No compatibility, certification, endorsement, or integration claim is made unless actually verified.

### D. Reusable technical assets that earn citations — target 10

Assets whose primary purpose is to be useful enough that maintainers/users can link to them independently.

Examples:

- provider-neutral minimal fixtures from real upstream bugs;
- false-PASS taxonomy with deterministic examples;
- replay/restore evidence checklist;
- sandbox lifecycle evidence checklist;
- exact-head / merge-result CI evidence model;
- authority-vs-observation decision table;
- portable terminality receipt shape;
- execution-result binding example;
- cross-runtime evidence comparison matrix;
- small offline validator examples.

These are distribution assets only when they are public, searchable, and contain a direct reproduction or verification path.

## Selection Scoring

External thread candidates are scored before posting:

| Signal | Points |
| --- | ---: |
| self-contained or reproducible failure | 2 |
| silent semantic divergence / false success / false absence | 2 |
| clear provider-neutral AgentCI fixture or verifier fit | 2 |
| active author/maintainer contribution or debugging intent | 1 |
| ecosystem historically produced downstream AgentCI action | 2 |
| recent/open/actively discussed | 1 |

Default publication threshold: 7/10.

A lower-scoring placement may still be used as a bounded experiment when it opens a genuinely new distribution channel. Experimental channels are capped until they produce observable downstream evidence.

## Comment Shape

External comments should be problem-specific and approximately follow this sequence:

1. name the precise invariant or ambiguity;
2. offer a portable evidence/fixture structure;
3. explain the negative control / false-PASS case;
4. state the claim boundary;
5. disclose AgentCI affiliation and link the repository;
6. preserve the upstream thread as canonical provenance;
7. use a contribution-oriented CTA, not a star/follow request.

Do not paste one generic template unchanged across many threads.

## Batch Execution

The campaign runs in small adaptive cohorts rather than one unreviewed blast.

Recommended cadence:

```text
search 12–20 candidates
→ score + dedupe
→ publish 5–8 placements
→ persist placement evidence
→ re-check prior cohorts
→ promote channels with replies/repo actions
→ reduce or pause channels with no downstream evidence
```

The campaign may still reach 50 placements quickly when high-quality supply is available. The cohort boundary exists to protect conversion quality, not to impose an arbitrary low volume ceiling.

## Attribution and Evidence

Once PR #141's `agentci.outreach.v2` contract is complete, every new external placement should record at minimum:

- placement ID;
- repository/surface;
- issue/PR/discussion identifier;
- successful public URL;
- semantic class;
- user intent/problem path;
- CTA type;
- publication result;
- downstream state;
- downstream evidence URLs;
- claim boundary;
- timestamp/date.

403/permission failures, duplicates, closed/saturated threads, and deliberate skips belong in `attempts`, never `placements`.

Owned assets and ecosystem listings should use equivalent placement records with a surface-type field once the v2 schema is deliberately extended. Do not silently overload GitHub-comment-only fields.

## Product Conversion Loop

Distribution and product work are coupled.

When repeated upstream problems cluster into one semantic class:

```text
external evidence cluster
→ choose one falsifiable invariant
→ create provider-neutral fixture / validator / showcase entry
→ RED → GREEN implementation
→ clean-wheel / exact-head verification
→ searchable docs / quickstart
→ use that artifact in the next relevant outreach cohort
```

Product priorities remain:

1. first-minute activation (`init → test`);
2. searchable truth-checked showcase;
3. portable upstream-provenance fixtures;
4. external execution-result binding rather than building another generic agent runner;
5. real backend evidence experiments only when evidence and environment access justify them.

## External Intelligence Loop

Every campaign cycle scans adjacent projects for changes that can alter AgentCI direction.

Primary categories:

- agent eval/evaluation frameworks;
- sandbox/runtime managers;
- MCP inspectors/security tooling;
- agent workflow/CI systems;
- tracing/observability frameworks;
- benchmark/attack suites;
- execution runners.

For each relevant project, record one of:

- `ADOPT_NOW` — pattern can improve AgentCI without breaking positioning;
- `EXPERIMENT` — needs a falsifiable fixture or user case first;
- `WATCH` — valuable but not current bottleneck;
- `NOT_CORE` — useful elsewhere, but duplicating it would dilute AgentCI differentiation.

Any durable conclusion goes under `.company/research/external/` or a project checkpoint so future sessions can recover the reasoning without relying on chat context.

## Searchability Strategy

The campaign should deliberately cover phrases qualified users actually type or encounter, including combinations of:

- AI agent evaluation;
- agent reliability testing;
- agent sandbox verification;
- sandbox evidence;
- agent replay / checkpoint bugs;
- duplicate tool calls;
- MCP authorization / tool approval;
- agent false success;
- agent terminality / cleanup;
- stale CI evidence;
- agent workflow reproducibility;
- agent observability provenance;
- provider-neutral agent testing.

Repository metadata, README headings, quickstart/docs titles, issue titles, and showcase descriptions should use accurate natural-language terms from these paths where they truthfully describe the content. Do not keyword-stuff unrelated terms.

## Success Criteria

Campaign completion requires all of the following:

- 50 confirmed public/searchable touchpoints, not failed write attempts;
- no duplicate AgentCI placement in a thread unless there is new material downstream;
- placement-level evidence persisted for new external comments;
- at least four distribution surface types represented;
- every upstream comment contains concrete technical value before the project link;
- owned assets contain direct next actions;
- downstream states are updated only from observable evidence;
- at least one product improvement or fixture is derived from campaign intelligence;
- campaign checkpoint records which channels should scale, pause, or be retried.

The campaign may finish with zero proven conversions; if so, that is a valid measured result and should trigger channel/product correction rather than fabricated attribution.

## Safety and Reputation Boundaries

Volume is allowed. Irrelevance is not.

The following remain disallowed campaign behavior:

- unrelated promotional comments;
- repeated identical comments across adjacent issues;
- false affiliation/compatibility/certification claims;
- asking for stars as the main CTA;
- counting failed writes or hidden traffic as success;
- reviving clearly dead/solved threads only to advertise;
- posting security-sensitive exploit detail beyond what the upstream thread already safely exposes.

These are conversion/reputation constraints, not low-volume rules.

## Recovery / Context-Length Contract

If session context becomes too long, resume in this order:

1. `docs/superpowers/specs/2026-09-01-50-touchpoint-growth-loop-design.md`;
2. PR #141 / its implementation plan and current attribution schema;
3. latest `.company/checkpoints/*outreach*` or attribution checkpoint;
4. latest `.company/research/external/` adoption assessments;
5. open P1 product PRs for quickstart/showcase;
6. re-check downstream evidence on the most recent outreach cohorts before publishing the next cohort.

Do not reconstruct campaign truth from memory when durable placement evidence exists.
