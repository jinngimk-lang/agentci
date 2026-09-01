# Searchable Conversion Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 10 AgentCI-owned searchable conversion surfaces and secure 10 legitimate ecosystem discovery placements so qualified users who find AgentCI can understand the use case and reach a first useful action quickly.

**Architecture:** Owned surfaces live in the repository and answer concrete search/user questions with direct next actions. Ecosystem placements are external listings/discussions/resource surfaces that truthfully classify AgentCI as an independent evidence-verification tool; they are persisted only when actually published. Because PR #141 is initially GitHub-comment-oriented, owned/listing surface attribution must be extended deliberately with `surface_type` rather than overloading `comment_url` semantics.

**Tech Stack:** Markdown, GitHub repository metadata/issues/PRs, `llms.txt`, AgentCI CLI documentation, Python/JSON only if attribution schema is extended.

**Spec:** `docs/superpowers/specs/2026-09-01-50-touchpoint-growth-loop-design.md`

## Global Constraints

- Target: 10 owned searchable surfaces + 10 ecosystem discovery surfaces = 20 campaign touchpoints.
- A surface counts only when publicly reachable and containing a direct next action or valid discovery path.
- Existing pre-campaign files may be improved, but count only when this campaign materially creates or upgrades a distinct searchable acquisition surface.
- Do not keyword-stuff unrelated terms.
- Do not claim released behavior for main-only `0.3.0.dev0` work.
- No integration/compatibility/certification claim without verified integration evidence.
- External directory/listing submissions must follow the target project's contribution/self-promotion rules.
- If no connected write path exists, prepare the asset but do not count it as published.

---

### Task 1: Define a surface-neutral attribution extension

**Files:**
- Modify after PR #141 base contract is GREEN: `tests/test_outreach_attribution.py`
- Modify: `scripts/validate_outreach_batch.py`
- Modify plan/docs for growth format only if needed.

**Interfaces:**
- Adds `surface_type` enum while preserving `agentci.outreach.v2` semantics.
- Supported types in this plan: `github_comment | owned_asset | ecosystem_listing | technical_asset`.
- `github_comment` requires `comment_url`; other surface types require `public_url`.

- [ ] **Step 1: RED — owned asset must not be forced into comment URL**

Add a valid placement shaped as:

```python
{
    'id': 'owned-false-pass-taxonomy',
    'surface_type': 'owned_asset',
    'public_url': 'https://github.com/jinngimk-lang/agentci/blob/main/docs/testing/false-pass-taxonomy.md',
    'semantic_class': 'false-pass-discovery',
    'intent': 'find examples of agent false success',
    'cta': 'reproduce',
    'publication_result': 'posted',
    'downstream_state': 'posted',
    'downstream_urls': [],
    'claim_boundary': 'Public documentation; no adoption claim.'
}
```

Expected before extension: validator rejects or cannot represent it cleanly.

- [ ] **Step 2: GREEN — type-specific URL contract**

Implement:

```python
ALLOWED_SURFACE_TYPES = {
    'github_comment', 'owned_asset', 'ecosystem_listing', 'technical_asset'
}
```

Validation rule:

```text
github_comment -> comment_url required and #issuecomment- URL
every other type -> public_url required and https:// URL
```

Do not allow both URL fields to create two identities for one placement.

- [ ] **Step 3: RED/GREEN — uniqueness includes public URL**

Two non-comment placements with the same `public_url` must fail exactly like duplicate comment URLs.

- [ ] **Step 4: Full tests + exact-head handoff**

Run focused attribution tests, full pytest, compileall and CI. Hand schema change to a non-Fixer Merge Decider.

### Task 2: Owned surface 1 — first-minute quickstart

**Files:**
- Land or reconcile existing `QUICKSTART.md` from PR #132 after its dependency chain is resolved.
- Synchronize `README.md`, `llms.txt`, `skills/agentci/SKILL.md` only with behavior actually available on the relevant branch/release.

**Interfaces:**
- User question: “How do I get one deterministic AgentCI result quickly?”
- Direct next action on main-only dev line: `agentci init` → `agentci test` once merged.

- [ ] Verify the clean-wheel `init → test` flow remains green on the exact integration head.
- [ ] Preserve explicit v0.2 vs `0.3.0.dev0` boundary until released.
- [ ] Record the public quickstart URL as one `owned_asset` placement only after merged to the publicly indexed branch.

### Task 3: Owned surface 2 — false-PASS taxonomy

**Files:**
- Create: `docs/testing/false-pass-taxonomy.md`
- Add a small link from README evidence/reliability section.

**Interfaces:**
- Search intent: `AI agent false success`, `tool failed but agent says success`, `agent telemetry success mismatch`.
- Produces: taxonomy table + reproduction/fixture next action.

- [ ] Create a table with at least these existing AgentCI-relevant classes:

```text
execution truth != telemetry truth
accepted != durable
management state != resource terminality
reviewed head != merge-result tree
configured capability != effective capability
observation/reviewer recommendation != authority
```

- [ ] For each class, link only to an existing canonical fixture/upstream provenance or mark `example pending`; do not invent case evidence.
- [ ] End with one CTA: contribute a minimal provider-neutral fixture preserving upstream provenance.
- [ ] Review all wording for certification/compatibility overclaim.

### Task 4: Owned surface 3 — replay/restore evidence checklist

**Files:**
- Create: `docs/testing/replay-restore-evidence-checklist.md`

**Interfaces:**
- Search intent: agent replay bug, checkpoint resume duplicate side effect, restore fidelity.

- [ ] Define minimum evidence fields:

```text
input/work identity
checkpoint identity/version
effect identity/count
crash/interrupt boundary
resume/replay decision
pre/post durable state
expected invariant
claim boundary
upstream provenance
```

- [ ] Link to LangGraph-derived AgentCI provenance only where already public and verified.
- [ ] Include a “not enough evidence” section so absence of checkpoint does not become a fabricated execution claim.

### Task 5: Owned surface 4 — lifecycle/terminality evidence checklist

**Files:**
- Create: `docs/testing/lifecycle-terminality-evidence-checklist.md`

**Interfaces:**
- Search intent: sandbox cleanup, cancelled agent process remains, orphan process/socket.

- [ ] Separate management-plane terminal state from real process/socket/resource terminal state.
- [ ] Define negative evidence and observation-window requirements.
- [ ] Provide a bounded contribution CTA for E2B/runtime cases.

### Task 6: Owned surface 5 — authority vs observation guide

**Files:**
- Create: `docs/testing/authority-vs-observation.md`

**Interfaces:**
- Search intent: MCP tool approval, agent permissions, reviewer model authorization.

- [ ] Define with AgentCI canonical terms:

```text
observation
recommendation/reviewer output
authoritative policy decision
enforcement receipt
subject/action/resource/context binding
```

- [ ] State that model confidence or majority vote cannot self-promote to authority.
- [ ] Link only to already-public authority design/evidence; no claim that every runtime implements it.

### Task 7: Owned surface 6 — stale CI / exact-head evidence guide

**Files:**
- Create: `docs/testing/exact-head-merge-result-evidence.md`

**Interfaces:**
- Search intent: stale CI approval, merge result changed, reviewed head drift.

- [ ] Explain distinct immutable identities:

```text
reviewed_head
base_head_at_review
merge_base
merge_result_tree / merge commit
approval evidence identity
```

- [ ] Provide one deterministic counterexample pattern where reviewed head stays unchanged while merge-result evidence becomes stale.

### Task 8: Owned surfaces 7–10 — four search-specific GitHub entry issues

**Files:**
- Create four real GitHub issues only if each offers useful contribution work.

**Interfaces:**
- Each issue title is a search-friendly user problem, not “marketing”.
- Each issue contains acceptance criteria for a real fixture/docs/reproduction contribution.

Use these four bounded topics unless evidence shows a better current cluster:

```text
INTAKE: agent replay / checkpoint duplicate-effect fixture
INTAKE: agent cleanup / terminality evidence fixture
INTAKE: agent false-success telemetry fixture
INTAKE: stale CI / exact-head evidence fixture
```

- [ ] Dedupe against existing AgentCI issues before creating.
- [ ] Preserve provider-neutral scope and upstream provenance field.
- [ ] Add exact expected files/test path when the issue is created.
- [ ] Count only issues that remain useful product/contributor surfaces even if they generate no traffic.

### Task 9: Discover 20 ecosystem-listing candidates

**Files:**
- Research checkpoint under `.company/research/external/` or campaign checkpoint.

**Interfaces:**
- Candidate classes: awesome lists, eval catalogs, sandbox/tool indexes, agent reliability resource lists, community showcase threads, discussions inviting related tools.

- [ ] Search repositories/resources with queries such as:

```text
awesome ai agents evaluation tools
awesome agent security sandbox
LLM eval tools list agent
MCP security tools awesome
AI agent reliability benchmark tools
```

- [ ] For each candidate record:

```text
public URL
maintainer activity
submission mechanism
license/CONTRIBUTING rules
whether self-promotion/tool submissions are invited
AgentCI-fit statement
publish capability available now?
```

- [ ] Reject surfaces that are abandoned, unrelated, pay-to-list, or prohibit the submission.

### Task 10: Publish ecosystem placements 1–5

- [ ] Select five highest-fit writable surfaces from Task 9.
- [ ] Use project-native format: PR entry, issue submission, discussion reply, catalog form, etc.
- [ ] Description must classify AgentCI accurately as evidence-first CI/reliability/security verification for AI agents; include Developer Preview / no backend certified where material.
- [ ] Persist each successful public URL as `ecosystem_listing`.
- [ ] Permission failures go to attempts and are replaced until five successful placements exist.

### Task 11: Publish ecosystem placements 6–10

Repeat Task 10 with preference for different discovery communities rather than ten entries in one list ecosystem. If one proven directory drives downstream action, concentration is allowed but must be documented.

### Task 12: Owned-surface agent discoverability verification

**Files:**
- Public surfaces only; follow `docs/testing/external-agent-verification.md`.

- [ ] Starting without private project memory, answer from public files:

```text
What is AgentCI?
When should it be used?
When should it not be used?
What is the cheapest discovery command?
What is the first useful invocation?
What does PASS/valid evidence mean and not mean?
How do I contribute a real failure?
```

- [ ] Any answer requiring hidden memory becomes a distribution/product defect, not a mental patch.
- [ ] Fix only the smallest missing public routing surface; synchronize README/llms/SKILL when behavior actually changed.

### Task 13: Final verification for this plan

- [ ] 10 distinct campaign-owned public searchable surfaces are live.
- [ ] 10 ecosystem discovery placements are actually published.
- [ ] Every owned surface has a concrete search/user intent and direct next action.
- [ ] Every ecosystem entry follows target contribution rules.
- [ ] No unpublished prepared asset is counted as published.
- [ ] Surface-neutral attribution files validate under the extended contract.
- [ ] Checkpoint records which search phrases/surfaces produced observable downstream signals and which remained unknown.
