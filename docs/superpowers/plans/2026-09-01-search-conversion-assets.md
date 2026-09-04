# Searchable Conversion Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 10 AgentCI-owned searchable conversion surfaces and secure 10 legitimate ecosystem discovery placements so qualified users who find AgentCI can understand the use case and reach a first useful action quickly.

**Architecture:** Owned surfaces live in the repository and answer concrete search/user questions with direct next actions. Ecosystem placements are external listings/discussions/resource surfaces that truthfully classify AgentCI as an independent evidence-verification tool; they are persisted only when actually published. Because PR #141 is initially GitHub-comment-oriented, owned/listing surface attribution must be extended deliberately with `surface_type` rather than overloading `comment_url` semantics.

**Tech Stack:** Markdown, GitHub repository metadata/issues/PRs, `llms.txt`, AgentCI CLI documentation, Python 3.11, JSON, pytest.

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
- Modify: `docs/community-growth.md`

**Interfaces:**
- Adds `surface_type` enum while preserving `agentci.outreach.v2` semantics.
- Supported types: `github_comment | owned_asset | ecosystem_listing | technical_asset`.
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

Expected before extension: validator rejects this record because it lacks the GitHub-comment-only URL contract.

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
owned_asset/ecosystem_listing/technical_asset -> public_url required and https:// URL
```

Reject records containing both `comment_url` and `public_url`.

- [ ] **Step 3: RED/GREEN — uniqueness includes public URL**

Two non-comment placements with the same `public_url` must fail exactly like duplicate comment URLs.

- [ ] **Step 4: Document the extension**

Add one short section to `docs/community-growth.md` specifying the four surface types, their URL identity fields, and that only publicly published surfaces count.

- [ ] **Step 5: Full tests + exact-head handoff**

```bash
python -m pytest -q tests/test_outreach_attribution.py
python -m pytest -q
python -m compileall src scripts
```

Then require exact-head GitHub CI and hand the schema change to a non-Fixer Merge Decider.

### Task 2: Owned surface 1 — first-minute quickstart

**Files:**
- Existing implementation branch: PR #132 / `QUICKSTART.md`
- Synchronization surfaces already changed by that stack: `README.md`, `llms.txt`, `skills/agentci/SKILL.md`

**Interfaces:**
- User question: “How do I get one deterministic AgentCI result quickly?”
- Direct next action after the development stack is merged: `agentci init` → `agentci test`.

- [ ] Verify #130 is merged by an eligible non-Fixer decider before #132 is retargeted/merged; do not duplicate the showcase CLI changes on another branch.
- [ ] Re-run #132 exact-head clean-wheel `init → test` flow after any base reconciliation.
- [ ] Preserve explicit v0.2 vs `0.3.0.dev0` boundary until a release actually contains `init`/`showcase`.
- [ ] Record `https://github.com/jinngimk-lang/agentci/blob/main/QUICKSTART.md` as one `owned_asset` placement only after the file is on `main`.

### Task 3: Owned surface 2 — false-PASS taxonomy

**Files:**
- Create: `docs/testing/false-pass-taxonomy.md`
- Modify: `README.md` with one routing link from the evidence/reliability section.

**Interfaces:**
- Search intent: `AI agent false success`, `tool failed but agent says success`, `agent telemetry success mismatch`.
- Produces: taxonomy table + reproduction/fixture next action.

- [ ] Create a table with these classes:

```text
execution truth != telemetry truth
accepted != durable
management state != resource terminality
reviewed head != merge-result tree
configured capability != effective capability
observation/reviewer recommendation != authority
```

- [ ] For each class, link to an existing canonical AgentCI fixture or public upstream provenance. If no canonical AgentCI fixture exists, state exactly `canonical AgentCI fixture: none` and link the public provenance instead; do not create a placeholder link.
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

- [ ] Link to `tests/fixtures/replay/langgraph-8582-send-untracked/` and LangGraph #8764 only with their actual current reproduction boundaries.
- [ ] Include a “not enough evidence” section so absence of checkpoint does not become a fabricated execution claim.

### Task 5: Owned surface 4 — lifecycle/terminality evidence checklist

**Files:**
- Create: `docs/testing/lifecycle-terminality-evidence-checklist.md`

**Interfaces:**
- Search intent: sandbox cleanup, cancelled agent process remains, orphan process/socket.

- [ ] Separate management-plane terminal state from real process/socket/resource terminal state.
- [ ] Define negative evidence and observation-window requirements.
- [ ] Provide a bounded contribution CTA for runtime cases: upstream URL + terminal state + residual resource observation + cleanup attempt + claim boundary.

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
- [ ] Link only to already-public AgentCI authority design/evidence; no claim that every runtime implements it.

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

- [ ] Provide one deterministic counterexample pattern where `reviewed_head` stays unchanged, current base changes in the blast radius, and the prior branch-head PASS cannot certify the new merge-result tree.

### Task 8: Owned surfaces 7–10 — four search-specific GitHub entry issues

**Files:**
- Create or materially upgrade exactly four useful public AgentCI issues.

**Interfaces:**
- Each issue title is a user problem/search phrase, not a marketing title.
- Each issue contains acceptance criteria for a real fixture/docs/reproduction contribution.

Primary topics in order:

```text
INTAKE: agent replay / checkpoint duplicate-effect fixture
INTAKE: agent cleanup / terminality evidence fixture
INTAKE: agent false-success telemetry fixture
INTAKE: stale CI / exact-head evidence fixture
```

Fallback topics, used in order only when a primary topic already has a materially equivalent open AgentCI issue that does not need another public surface:

```text
INTAKE: accepted-but-not-durable agent run fixture
INTAKE: exactly-once / lost-ack agent fixture
INTAKE: configured-vs-effective capability fixture
INTAKE: MCP authority-vs-observation fixture
```

- [ ] Search AgentCI issues for each primary topic before creation.
- [ ] If an equivalent issue exists and can be materially upgraded with current fixture paths/acceptance, update it and count that upgraded public surface; otherwise use the next fallback topic.
- [ ] Preserve provider-neutral scope and require an upstream provenance URL.
- [ ] Name exact expected fixture/test/doc path in each issue.
- [ ] Count only issues that remain useful product/contributor surfaces even if they generate no traffic.

### Task 9: Discover 20 ecosystem-listing candidates

**Files:**
- Create: `.company/research/external/50-touchpoint-ecosystem-discovery-2026-09-01.md`

**Interfaces:**
- Candidate classes: awesome lists, eval catalogs, sandbox/tool indexes, agent reliability resource lists, community showcase threads, discussions inviting related tools.

- [ ] Search repositories/resources with queries:

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
last meaningful activity date
submission mechanism
license/CONTRIBUTING/self-promotion rule
AgentCI-fit statement
connected write capability available now: yes/no
```

- [ ] Reject surfaces that are abandoned, unrelated, pay-to-list, or prohibit the submission.
- [ ] Rank the remaining candidates by audience fit, maintenance activity, submission legitimacy and ability to describe AgentCI without compatibility overclaim.

### Task 10: Publish ecosystem placements 1–5

- [ ] Select the five highest-ranked writable surfaces from Task 9.
- [ ] Use project-native format: PR entry, issue submission, discussion reply or documented catalog submission.
- [ ] Description must classify AgentCI accurately as evidence-first CI/reliability/security verification for AI agents; include Developer Preview / no backend certified where material.
- [ ] Persist each successful public URL as `ecosystem_listing`.
- [ ] Permission failures go to attempts and are replaced until five successful placements exist.

### Task 11: Publish ecosystem placements 6–10

- [ ] Select the next five highest-ranked writable legitimate surfaces after rechecking the first five for moderation/feedback.
- [ ] Prefer different discovery communities rather than ten entries in one list ecosystem.
- [ ] If a proven listing produces public downstream evidence, concentration is allowed only after the checkpoint records that evidence and rationale.
- [ ] Persist only successful public placements.

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
