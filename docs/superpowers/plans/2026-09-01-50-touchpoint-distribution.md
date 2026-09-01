# 50-Touchpoint Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete placement-level attribution and publish 20 new high-intent upstream technical placements as the external-comment portion of the owner-approved 50-touchpoint campaign.

**Architecture:** Finish the existing `agentci.outreach.v2` validator on PR #141 instead of creating a competing format. Campaign execution runs in four adaptive cohorts of five confirmed writes; every candidate is scored and deduplicated before posting, successful writes are persisted as placements, failed/blocked/duplicate/skipped attempts are persisted separately, and downstream state is updated only from public evidence.

**Tech Stack:** GitHub Issues/PRs, Python 3.11, JSON, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-01-50-touchpoint-growth-loop-design.md`

## Global Constraints

- Campaign counter starts after owner approval of the 50-touchpoint design; earlier outreach remains baseline evidence and does not reduce the 50-touchpoint target.
- External-comment target for this plan is 20 **successful public writes**, not 20 attempts.
- Default candidate threshold is 7/10 using the design scoring table.
- No duplicate AgentCI comment in a thread unless new downstream material requires a direct response.
- A comment must provide a concrete invariant, fixture/evidence shape, negative control or claim boundary before the AgentCI link.
- Failed/403/duplicate/skipped attempts never count as placements.
- Hidden referral traffic, views and clicks remain unknown.
- No compatibility, certification, partnership or endorsement claim without direct evidence.
- Preserve upstream issue/PR as canonical provenance.
- Do not publish actionable security detail beyond what is already safely public upstream.
- `Fixer != Merge Decider` for code/schema changes; distribution writes themselves do not create merge authority.

---

### Task 1: Finish the current `comment_url` RED on PR #141

**Files:**
- Modify: `scripts/validate_outreach_batch.py`
- Test: `tests/test_outreach_attribution.py`
- Reference: `docs/superpowers/plans/2026-09-01-outreach-placement-attribution.md`

**Interfaces:**
- Consumes: one `agentci.outreach.v2` JSON file.
- Produces: validator exit `0` only when every counted placement contains a confirmed public GitHub issue/PR comment URL.

- [ ] **Step 1: Reconfirm the existing RED**

Run the exact current PR #141 head through GitHub Actions or the focused test:

```bash
python -m pytest -q tests/test_outreach_attribution.py::test_counted_placement_requires_confirmed_public_comment_url
```

Expected: FAIL because a placement without `comment_url` is currently accepted.

- [ ] **Step 2: Add the smallest URL contract**

In `scripts/validate_outreach_batch.py`, validate every placement before counting it:

```python
comment_url = placement.get('comment_url')
if not isinstance(comment_url, str) or not comment_url.startswith('https://github.com/'):
    raise ValueError('placement comment_url must be a confirmed public GitHub comment URL')
if '#issuecomment-' not in comment_url:
    raise ValueError('placement comment_url must identify a GitHub issue/PR comment')
```

Do not add network lookup in this task.

- [ ] **Step 3: Run focused GREEN**

```bash
python -m pytest -q tests/test_outreach_attribution.py
```

Expected: PASS for the valid fixture and missing-URL rejection.

- [ ] **Step 4: Commit on PR #141 branch**

Commit message:

```text
fix(growth): require confirmed outreach comment URLs
```

### Task 2: Close placement inflation paths

**Files:**
- Modify: `tests/test_outreach_attribution.py`
- Modify: `scripts/validate_outreach_batch.py`

**Interfaces:**
- Consumes: placement records with `id`, `comment_url`, `publication_result`.
- Produces: deterministic rejection of non-posted or duplicate counted placements.

- [ ] **Step 1: RED — non-posted placement must not count**

Add a test mutating the valid fixture:

```python
payload['placements'][0]['publication_result'] = 'blocked'
result = _run_validator(tmp_path, payload)
assert result.returncode == 1
assert 'publication_result' in result.stderr
```

Run it and confirm failure for the intended reason.

- [ ] **Step 2: GREEN — require `publication_result == posted`**

Add:

```python
if placement.get('publication_result') != 'posted':
    raise ValueError('counted placement publication_result must be posted')
```

Run the focused suite and confirm GREEN.

- [ ] **Step 3: RED — duplicate IDs and comment URLs**

Create two placements with the same `id`, then two with distinct IDs but the same `comment_url`; each must return `1`.

- [ ] **Step 4: GREEN — deterministic uniqueness**

Track `seen_ids` and `seen_urls`; reject reuse before incrementing summary counters.

- [ ] **Step 5: Commit**

```text
fix(growth): reject inflated outreach placements
```

### Task 3: Make downstream state evidence explicit

**Files:**
- Modify: `tests/test_outreach_attribution.py`
- Modify: `scripts/validate_outreach_batch.py`

**Interfaces:**
- Allowed states: `posted | replied | repo_action | contribution | merged | repeat_contributor`.
- Advanced states require at least one public `downstream_urls` entry.

- [ ] **Step 1: RED — reject invented traffic/referral state**

Mutate `downstream_state` to `visited` and assert validator exit `1` with `downstream_state` in stderr.

- [ ] **Step 2: GREEN — closed state enum**

Define:

```python
ALLOWED_DOWNSTREAM_STATES = {
    'posted', 'replied', 'repo_action', 'contribution', 'merged', 'repeat_contributor'
}
```

Reject all others.

- [ ] **Step 3: RED — advanced state needs public evidence URL**

Set state to `replied` with `downstream_urls=[]`; assert failure.

- [ ] **Step 4: GREEN — require public evidence for advanced states**

For every state except `posted`, require a non-empty list of `https://github.com/` URLs.

- [ ] **Step 5: Full validator verification**

```bash
python -m pytest -q tests/test_outreach_attribution.py
python -m pytest -q
python -m compileall src scripts
```

Expected: all GREEN.

- [ ] **Step 6: Exact-head CI handoff**

Update PR #141 body with RED→GREEN evidence, exact head SHA, full test count and remaining limitations. Do not merge as the Fixer.

### Task 4: Establish the campaign ledger for new placements

**Files:**
- Create after #141 contract is GREEN: `.company/growth/outreach-2026-09-01-50-touchpoint-batch-001.json`
- Create: `.company/growth/outreach-2026-09-01-50-touchpoint-batch-002.json`
- Create: `.company/growth/outreach-2026-09-01-50-touchpoint-batch-003.json`
- Create: `.company/growth/outreach-2026-09-01-50-touchpoint-batch-004.json`
- Create/update campaign checkpoint: `.company/checkpoints/2026-09-01-50-touchpoint-campaign.md`

**Interfaces:**
- One batch = five confirmed successful external comment placements plus any attempts encountered while finding them.
- Batch IDs: `2026-09-01-50tp-001` through `004`.

- [ ] **Step 1: Create each batch file only after its five successful writes exist**

Use this exact top-level shape, substituting the matching batch ID:

```json
{
  "schema_version": "agentci.outreach.v2",
  "batch_id": "2026-09-01-50tp-001",
  "date": "2026-09-01",
  "placements": [],
  "attempts": []
}
```

Do not pre-fill planned targets as successful placements.

- [ ] **Step 2: Validate every persisted batch offline**

```bash
python scripts/validate_outreach_batch.py .company/growth/outreach-2026-09-01-50-touchpoint-batch-001.json --json
python scripts/validate_outreach_batch.py .company/growth/outreach-2026-09-01-50-touchpoint-batch-002.json --json
python scripts/validate_outreach_batch.py .company/growth/outreach-2026-09-01-50-touchpoint-batch-003.json --json
python scripts/validate_outreach_batch.py .company/growth/outreach-2026-09-01-50-touchpoint-batch-004.json --json
```

Expected for every completed batch: `successful_placements == 5`.

- [ ] **Step 3: Campaign checkpoint counters**

Record exact totals by surface and downstream state. Baseline outreach before design approval is listed separately and does not count toward the campaign 50.

### Task 5: Execute upstream cohort 1 — replay/durability/exactly-once

**Files:**
- External GitHub issue/PR comments.
- Persist results in batch 001 JSON.

**Interfaces:**
- Search pool target: 12–20 open/recent issues.
- Required successful writes: 5.

- [ ] **Step 1: Search candidates**

Use focused GitHub searches such as:

```text
checkpoint replay resume duplicate tool call agent
accepted run no checkpoint durable state agent
commit ack retry duplicate agent session
```

Prioritize LangGraph, OpenAI Agents SDK, Google ADK, E2B, Pydantic AI, Mastra and adjacent active projects, but allow new ecosystems.

- [ ] **Step 2: Dedupe**

Fetch comments for every candidate. Exclude a thread if AgentCI already has a comment unless a new maintainer/user reply creates a legitimate response path.

- [ ] **Step 3: Score**

For every candidate considered for publication, record the six design score components and total in the campaign checkpoint before posting. Publish by default only when score >= 7.

- [ ] **Step 4: Write five problem-specific comments**

Each comment must contain:

```text
precise invariant
portable evidence/fixture fields
negative control or ambiguity
claim boundary
AgentCI affiliation + repo link
upstream provenance preservation
bounded contribution CTA
```

Do not reuse identical prose.

- [ ] **Step 5: Persist only successful writes**

403/permission failures go to `attempts`. Continue replacing failed targets until five successful writes exist.

### Task 6: Execute upstream cohort 2 — terminality/lifecycle/resource residue

Repeat Task 5 with semantic focus:

```text
cleanup terminality cancelled process remains agent
sandbox pause resume orphan process resource leak
stream ended without terminal event agent
```

Produce exactly five additional confirmed placements in batch 002.

### Task 7: Execute upstream cohort 3 — authority/identity/route evidence

Repeat the same search→dedupe→score→publish→persist loop with:

```text
MCP authorization tool approval mismatch
agent route identity drift stale authority
reviewed head merge result stale CI agent
```

Produce five confirmed placements in batch 003.

### Task 8: Execute upstream cohort 4 — telemetry/provenance/false success

Repeat the loop with:

```text
agent trace success but error telemetry
tool failed marked success agent
observability provenance environment wrong agent
```

Produce five confirmed placements in batch 004.

### Task 9: Re-check all four cohorts for downstream evidence

**Files:**
- Modify the four batch JSON files only when public evidence changes.
- Modify `.company/checkpoints/2026-09-01-50-touchpoint-campaign.md`.

- [ ] **Step 1: Fetch comments/threads for every placement**

Look only for evidence after the AgentCI placement timestamp.

- [ ] **Step 2: Upgrade state conservatively**

Examples:

```text
maintainer/user replies to AgentCI comment → replied
new AgentCI issue/fork attributable from public evidence → repo_action
external PR/fixture → contribution
merged external PR → merged
second later contribution from same external contributor → repeat_contributor
```

Do not infer repo visits from timing alone.

- [ ] **Step 3: Channel decision**

Checkpoint must name:

```text
scale: semantic/ecosystem combinations with downstream evidence
hold: posted but no downstream signal yet
pause: repeated no-response or saturated channels
blocked: permission/moderation constraints
```

### Task 10: Final verification for this plan

- [ ] Confirm campaign ledger contains exactly 20 successful external-comment placements after design approval.
- [ ] Confirm no failed attempt appears in `placements`.
- [ ] Confirm all four batch files pass `validate_outreach_batch.py`.
- [ ] Confirm no duplicate comment URL across campaign batches.
- [ ] Confirm at least four ecosystems are represented unless downstream evidence justifies concentration in a smaller proven set; document any concentration explicitly.
- [ ] Run full repository CI for any code/schema changes.
- [ ] Hand code/schema PRs to a non-Fixer Merge Decider; public outreach itself remains logged evidence, not merge evidence.
