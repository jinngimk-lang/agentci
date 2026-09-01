# Outreach Placement Attribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned, deterministic placement-level outreach record and validator so new public distribution can be measured by semantic class and observable downstream state without inflating success from failed writes or hidden-traffic inference.

**Architecture:** Keep historical URL-only outreach JSON untouched. New `agentci.outreach.v2` files contain `placements` for confirmed successful public comments and `attempts` for blocked/duplicate/skipped work. A standalone offline validator owns schema and evidence rules; tests invoke it as a CLI so the format remains useful outside Python internals.

**Tech Stack:** Python 3.11, JSON, pytest, subprocess CLI tests.

**Spec:** GitHub issue #135.

## Global Constraints

- Do not migrate the historical 550 URL-only placements in this slice.
- No network lookup is required to validate or summarize a v2 batch.
- A failed, blocked, duplicate, or skipped attempt never counts as a placement.
- Hidden referral/traffic inference is not an observable downstream fact.
- Public comments must contribute concrete technical value before the AgentCI CTA.

---

### Task 1: Valid v2 batch contract

**Files:**
- Create: `tests/test_outreach_attribution.py`
- Create later in GREEN: `scripts/validate_outreach_batch.py`

**Interfaces:**
- Consumes: one JSON file path and optional `--json` flag.
- Produces: exit code `0` for valid input and JSON summary containing `schema_version`, `successful_placements`, `by_semantic_class`, and `by_downstream_state`.

- [ ] **Step 1: Write the failing test**

Create one valid batch with exactly one placement and assert the validator returns `0` plus `successful_placements == 1`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_outreach_attribution.py::test_valid_v2_batch_reports_one_successful_placement`
Expected: FAIL because `scripts/validate_outreach_batch.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

Implement only enough parsing/schema checking and summary generation for the valid fixture.

- [ ] **Step 4: Run test to verify it passes**

Run the focused test. Expected: PASS.

### Task 2: Fail-closed placement evidence

**Files:**
- Modify: `tests/test_outreach_attribution.py`
- Modify: `scripts/validate_outreach_batch.py`

- [ ] **Step 1: RED — reject placement without confirmed public GitHub comment URL**
- [ ] **Step 2: GREEN — require a GitHub issue/PR comment URL for every counted placement**
- [ ] **Step 3: RED — reject blocked/failed/skipped/duplicate result inside `placements`**
- [ ] **Step 4: GREEN — allow only `publication_result=posted` inside `placements`**
- [ ] **Step 5: RED — reject duplicate placement IDs or comment URLs**
- [ ] **Step 6: GREEN — enforce uniqueness deterministically**

### Task 3: Observable downstream-state contract

**Files:**
- Modify: `tests/test_outreach_attribution.py`
- Modify: `scripts/validate_outreach_batch.py`

- [ ] **Step 1: RED — reject hidden traffic/referral claims as downstream evidence**
- [ ] **Step 2: GREEN — allow only observable state enum: `posted | replied | repo_action | contribution | merged | repeat_contributor`**
- [ ] **Step 3: RED — require public downstream URLs once state advances beyond `posted`**
- [ ] **Step 4: GREEN — enforce evidence URL requirement**

### Task 4: Current batch and documentation

**Files:**
- Create: `.company/growth/outreach-2026-09-01-placement-batch.json`
- Create or modify: `.company/growth/README.md` only if a canonical growth-format document does not already exist.

- [ ] Record only confirmed successful public comments as placements.
- [ ] Put 403, duplicates, and skipped saturated targets in `attempts`.
- [ ] Document that reactions/replies/forks/issues/PRs/merges are observable signals, not proof of hidden referral traffic.

### Task 5: Verification

- [ ] Run focused attribution tests.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m compileall src scripts`.
- [ ] Run existing growth validation and generation smoke.
- [ ] Add CI invocation only if full tests would otherwise not exercise the validator.
