# External Fixture Product Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn repeated external failure signals into 10 reusable public technical assets, including one concrete provider-neutral replay/durability fixture derived from LangGraph #8764 and built through RED→GREEN evidence.

**Architecture:** External GitHub/runtime issues are untrusted provenance inputs, not AgentCI truth. The first executable artifact extends AgentCI's existing provider-neutral replay fixture pattern (`tests/fixtures/replay/langgraph-8582-send-untracked`) rather than adding a provider SDK or second verdict engine. LangGraph #8764 is reduced to the caller-admission vs runtime-durability boundary: an external caller may record a background run as accepted while the runtime has no first durable checkpoint after process death. AgentCI preserves that upstream claim as `UNVERIFIED` and makes the missing durability evidence explicit.

**Tech Stack:** Python 3.11, JSON/JSONL fixtures, pytest, Markdown, AgentCI showcase catalog, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-01-50-touchpoint-growth-loop-design.md`

## Global Constraints

- Target: 10 new reusable public technical assets after campaign approval.
- At least one asset must include executable/reproducible machine-readable evidence rather than prose only.
- LangGraph #8764 remains upstream provenance; AgentCI does not claim independent LangGraph reproduction in the reduced fixture unless that is separately executed later.
- Do not say LangGraph itself durably accepted a run when the public issue only establishes that an external caller/system may have recorded acceptance.
- No LangGraph core/runtime dependency is added.
- Preserve upstream issue URL and reporter credit.
- Fixture presence does not certify LangGraph or any backend.
- Missing runtime material remains `UNVERIFIED`; absence of a checkpoint does not prove “nothing happened” or “the run never existed”.
- `configured/present != verified/effective`; `observation != authority`.
- Security-sensitive external cases must not be expanded into public exploit instructions.
- Behavior/schema changes use TDD; `Fixer != Merge Decider`.

---

### Task 1: Build the campaign semantic-cluster ledger

**Files:**
- Create: `.company/research/external/50-touchpoint-signal-clusters-2026-09-01.md`

**Interfaces:**
- Consumes: successful campaign placements and high-signal external research issues.
- Produces: ranked semantic clusters with provenance URLs, count, evidence quality and proposed AgentCI artifact.

- [ ] **Step 1: Classify every successful upstream placement**

Use one primary class per placement:

```text
replay-restore-fidelity
exactly-once-lost-ack
accepted-not-durable
terminality-cleanup
resource-residue
identity-route-drift
authority-binding
stale-ci-evidence
telemetry-false-success
metadata-provenance
configured-vs-effective-capability
```

- [ ] **Step 2: Rank cluster strength**

For each cluster record:

```text
number of independent upstream repositories
number of self-contained reproductions
observable downstream AgentCI response
existing AgentCI fixture overlap
smallest new invariant
```

- [ ] **Step 3: Record the first executable choice**

Select `accepted-not-durable` / LangGraph #8764 for the first new fixture because it is a recent open issue with a self-contained process-death reproduction and cleanly extends the existing replay fixture corpus without a new runtime dependency.

### Task 2: Asset 1 — machine-readable external provenance index

**Files:**
- Create: `.company/research/external/50-touchpoint-provenance-index.json`
- Test: `tests/test_external_provenance_index.py`

**Interfaces:**
- Each record: `id`, `source_url`, `source_repository`, `semantic_class`, `status`, `agentci_artifact`, `claim_boundary`.
- Allowed `status`: `observed-upstream | reduced-fixture | independently-reproduced | merged-contribution`.

- [ ] **Step 1: Write RED for duplicate source URLs**

Create `tests/test_external_provenance_index.py` with a helper that validates a list of records and one test containing the same `source_url` twice. The test must fail until canonical validation exists.

- [ ] **Step 2: Add the canonical index and validation assertions**

The initial LangGraph #8764 record is:

```json
{
  "id": "langgraph-8764-accepted-not-durable",
  "source_url": "https://github.com/langchain-ai/langgraph/issues/8764",
  "source_repository": "langchain-ai/langgraph",
  "semantic_class": "accepted-not-durable",
  "status": "observed-upstream",
  "agentci_artifact": "tests/fixtures/replay/langgraph-8764-accepted-not-durable",
  "claim_boundary": "Upstream reproduction observed; AgentCI runtime reproduction remains UNVERIFIED."
}
```

Make the test enforce unique non-empty HTTPS source URLs and allowed status values.

- [ ] **Step 3: Add secret/material scan**

Serialize the canonical index in the test and assert it does not contain keys or values named `token`, `password`, `secret_value`, `api_key`, or `authorization`.

- [ ] **Step 4: Run focused GREEN**

```bash
python -m pytest -q tests/test_external_provenance_index.py
```

### Task 3: Asset 2 — RED for LangGraph #8764 reduced fixture

**Files:**
- Create test first: `tests/test_langgraph_8764_accepted_not_durable_fixture.py`
- Fixture directory to be created only in GREEN: `tests/fixtures/replay/langgraph-8764-accepted-not-durable/`

**Interfaces:**
- Reuses the file pattern of `tests/fixtures/replay/langgraph-8582-send-untracked`:
  - `provenance.json`
  - `case.json`
  - `trajectory.jsonl`
  - `README.md`
- No production validator API is added in this slice; the fixture itself is the canonical reduced evidence artifact and the pytest contract makes its claims deterministic.

- [ ] **Step 1: Write the failing provenance/boundary test**

Create the new test file with:

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'replay' / 'langgraph-8764-accepted-not-durable'


def _load_json(name: str):
    return json.loads((FIXTURE / name).read_text(encoding='utf-8'))


def test_langgraph_8764_preserves_upstream_and_unverified_boundary():
    provenance = _load_json('provenance.json')
    case = _load_json('case.json')
    assert provenance['source']['url'] == 'https://github.com/langchain-ai/langgraph/issues/8764'
    assert provenance['source']['reporter'] == 'mstevens843'
    assert provenance['agentci_reproduction_status'] == 'UNVERIFIED'
    assert case['semantic_class'] == 'accepted-not-durable'
    assert case['agentci_result'] == 'UNVERIFIED'
```

Run:

```bash
python -m pytest -q tests/test_langgraph_8764_accepted_not_durable_fixture.py
```

Expected: FAIL with missing fixture files/directories, while the existing LangGraph #8582 test remains green.

- [ ] **Step 2: Add RED for admission/durability distinction**

In the same test file add:

```python
def test_external_acceptance_is_not_promoted_to_runtime_durability():
    case = _load_json('case.json')
    assert case['external_acceptance']['status'] == 'asserted-by-upstream-caller'
    assert case['runtime_admission_record']['status'] == 'unavailable'
    assert case['first_durable_checkpoint']['presence'] == 'absent-in-upstream-reproduction'
    assert case['user_effect']['observed_count'] == 0
    assert case['recovery']['outcome'] == 'no-resumable-state'
    assert case['classification'] == 'ADMISSION_DURABILITY_GAP'
    assert case['agentci_result'] == 'UNVERIFIED'
```

This test intentionally forbids collapsing caller acceptance into a LangGraph runtime acceptance claim.

- [ ] **Step 3: Add RED for trajectory shape**

Load `trajectory.jsonl` and assert event types exactly equal:

```python
[
    'external-run-accepted',
    'process-terminated',
    'durable-checkpoint-observed',
    'recovery-attempted',
    'admission-durability-result',
]
```

Final event must contain:

```python
assert final['classification'] == 'ADMISSION_DURABILITY_GAP'
assert final['verdict'] == 'UNVERIFIED'
assert final['missing_material_evidence'] == ['runtime_admission_record', 'first_durable_checkpoint']
```

### Task 4: Asset 2 — GREEN fixture files

**Files:**
- Create: `tests/fixtures/replay/langgraph-8764-accepted-not-durable/provenance.json`
- Create: `tests/fixtures/replay/langgraph-8764-accepted-not-durable/case.json`
- Create: `tests/fixtures/replay/langgraph-8764-accepted-not-durable/trajectory.jsonl`
- Create: `tests/fixtures/replay/langgraph-8764-accepted-not-durable/README.md`

**Interfaces:**
- `provenance.json` records upstream issue metadata and `agentci_reproduction_status: UNVERIFIED`.
- `case.json` records the reduced semantic boundary, not raw LangGraph code.
- `trajectory.jsonl` is a case-local semantic reduction, not a claim that AgentCI captured native runtime telemetry.

- [ ] **Step 1: Write `provenance.json`**

Use:

```json
{
  "source": {
    "url": "https://github.com/langchain-ai/langgraph/issues/8764",
    "repository": "langchain-ai/langgraph",
    "issue_number": 8764,
    "reporter": "mstevens843",
    "reported_at": "2026-08-30"
  },
  "capture": {
    "source_kind": "public-upstream-issue",
    "reproduction_kind": "self-contained-process-death-reproduction",
    "upstream_contract": "UNCONFIRMED"
  },
  "agentci_reproduction_status": "UNVERIFIED"
}
```

- [ ] **Step 2: Write `case.json`**

Use a provider-neutral object containing exactly these semantic fields:

```json
{
  "case_id": "langgraph-8764-accepted-not-durable",
  "semantic_class": "accepted-not-durable",
  "external_acceptance": {"status": "asserted-by-upstream-caller"},
  "runtime_admission_record": {"status": "unavailable"},
  "first_durable_checkpoint": {"presence": "absent-in-upstream-reproduction"},
  "process_termination": {"kind": "abrupt-process-death"},
  "user_effect": {"observed_count": 0},
  "recovery": {"outcome": "no-resumable-state"},
  "classification": "ADMISSION_DURABILITY_GAP",
  "acceptable_outcomes": ["durable-admission-record", "explicit-durable-failure-record", "caller-owned-acceptance-ledger", "UNVERIFIED"],
  "agentci_result": "UNVERIFIED",
  "claim_boundary": "This fixture preserves an upstream admission/durability ambiguity; it does not prove LangGraph runtime acceptance or certify recovery behavior."
}
```

- [ ] **Step 3: Write five JSONL trajectory events**

Use monotonic `sequence` 1–5 and one case-local `logical_run_ref`. Event 3 records checkpoint presence as false/absent in the upstream reproduction; event 5 records the missing material list and `UNVERIFIED` verdict.

- [ ] **Step 4: Write fixture README**

README must state:

```text
upstream provenance
what the upstream reproduction observed
what AgentCI reduced into a provider-neutral invariant
why caller acceptance != runtime durability
how to run the fixture test
why the result remains UNVERIFIED
no LangGraph dependency / no backend certification
```

Exact command:

```bash
python -m pytest -q tests/test_langgraph_8764_accepted_not_durable_fixture.py
```

- [ ] **Step 5: Focused GREEN**

Run the new test plus existing #8582 fixture test:

```bash
python -m pytest -q tests/test_langgraph_8764_accepted_not_durable_fixture.py tests/test_langgraph_8582_replay_fixture.py
```

Expected: all PASS.

### Task 5: Asset 2 — no-dependency/secret boundary

**Files:**
- Modify: `tests/test_langgraph_8764_accepted_not_durable_fixture.py`

- [ ] Add a test concatenating all new fixture text and assert it contains no `secret_value`, `api_key`, `authorization`, or copied private runtime value.
- [ ] Parse `pyproject.toml` and assert no dependency begins with `langgraph`.
- [ ] Scan `src/agentci/**/*.py` and assert the new fixture work did not add `import langgraph` / `from langgraph`.
- [ ] Run focused GREEN again.

### Task 6: Asset 2 — full verification and challenge

- [ ] Run:

```bash
python -m pytest -q
python -m compileall src scripts
```

- [ ] Open a dedicated fixture PR from current main; do not mix it into the campaign-design PR.
- [ ] Challenger attacks the exact head for: caller acceptance mislabeled as runtime acceptance, nonzero effect count incorrectly tolerated, checkpoint presence incorrectly marked durable, and copied `UNVERIFIED` labels without underlying missing-material fields.
- [ ] Record Spec and Standards verdicts separately.
- [ ] Eligible non-Fixer Merge Decider acts only on exact head + green CI + clean challenge.

### Task 7: Asset 3 — showcase entry for LangGraph #8764 fixture

**Files:**
- Modify `showcase/catalog-v1.json` only after #130 or its successor is on the relevant integration base.
- Modify existing showcase truth-contract tests.

**Interfaces:**
- ID: `replay-accepted-not-durable-langgraph-8764`.
- `evidence_maturity: fixture`.
- `certification_claim: false`.
- `repository_path: tests/fixtures/replay/langgraph-8764-accepted-not-durable/case.json`.

- [ ] RED: canonical catalog test expects this fixture ID and currently fails because the entry is absent.
- [ ] GREEN: add one catalog entry pointing to the existing fixture path and a parseable pytest/reproduction command supported by the documented development line.
- [ ] Run catalog validator and clean-wheel/source discovery tests; do not package the entire test fixture corpus into the wheel unless a separate product decision requires that.

### Task 8: Asset 4 — external execution-result binding checklist

**Files:**
- Create: `docs/testing/execution-result-binding.md`

Document the minimum evidence tuple:

```text
run/attempt identity
starting tree/workspace digest
post-run tree/workspace digest
exact verifier argv + timeout
environment/policy digest
route/sandbox identity
exit code + bounded output digest
actor/verifier shared-authority relationship
claim boundary
```

End with a contribution CTA for runners that can export this evidence. Cite external projects only as provenance/pattern inputs, not compatibility claims.

### Task 9: Asset 5 — cross-runtime evidence comparison matrix

**Files:**
- Create: `.company/research/external/cross-runtime-evidence-matrix-2026-09-01.md`

Compare only documented/public evidence surfaces for projects already researched: SWE-ReX, Kubernetes Agent Sandbox, Docker Sandboxes, E2B, OpenHands, and agent-belt where relevant.

Columns:

```text
runtime/project
execution identity available?
lifecycle/cleanup evidence?
network/policy evidence?
workspace/tree identity?
external verifier hook?
provider-neutral export?
AgentCI classification
source/version/date
```

Use `unknown` rather than inference. Record license and source pin for every row.

### Task 10: Asset 6 — configured-vs-effective capability matrix

**Files:**
- Create: `docs/testing/configured-vs-effective-capability.md`

Explain why declared support cannot prove feature combinations or runtime usability. Include this deterministic matrix:

```text
configured=true, discovered=true, effective=unknown -> non-PASS
configured=true, bounded probe fails -> not-ready
configured=true, bounded real probe succeeds -> evidence limited to the probed capability
```

Use Google ADK #6954 only as an upstream example of why combination-level capability truth matters; do not claim AgentCI has reproduced or supports Google ADK.

### Task 11: Asset 7 — terminal evidence absence pattern

**Files:**
- Create: `docs/testing/negative-terminal-evidence.md`

Define how to record “no terminal event observed” without turning absence into “sandbox died” or “command succeeded”. Require:

```text
last observed event identity
observation source
bounded observation window
resource/lifecycle health source if available
negative evidence statement
allowed classifications
```

### Task 12: Asset 8 — exactly-once / lost-ack checklist

**Files:**
- Create: `docs/testing/exactly-once-lost-ack.md`

Separate durable commit truth from caller acknowledgement. Require durable state reconciliation before replaying a guarded input/effect. Use OpenAI Agents SDK #4775 only as public provenance for the failure shape unless independently reproduced.

### Task 13: Asset 9 — upstream fixture contribution template

**Files:**
- Inspect first: `.github/ISSUE_TEMPLATE/backend_evidence.yml`
- Extend that template if it can remain the single intake surface; create `.github/ISSUE_TEMPLATE/upstream_fixture.yml` only if the existing form cannot express replay/terminality/false-success provenance without confusing backend evidence.

Required fields after the change:

```text
upstream URL
minimal reproduction
semantic class
observed vs inferred facts
portable invariant
negative control
secret/redaction confirmation
proposed fixture path
```

Add YAML parse validation to repository tests or CI if current templates are not already parsed.

### Task 14: Asset 10 — campaign-derived technical index

**Files:**
- Create: `docs/testing/agent-evidence-patterns.md`

Create a search-oriented router linking Assets 2–9 plus existing AgentCI evidence docs. Each row contains:

```text
problem phrase | AgentCI evidence pattern | exact next action/command | claim boundary
```

Include phrases such as:

```text
agent says success but tool failed
checkpoint resume duplicated an effect
background run disappeared after acceptance
cancelled sandbox still has a process/socket
reviewed commit is green but merge result changed
tool reviewer allowed action but policy should deny
```

Do not duplicate full guides; this page is routing/indexing.

### Task 15: Reuse technical assets in later distribution cohorts

- [ ] For every new external placement after an applicable asset exists, prefer linking the exact technical asset over only the repository root when it materially helps the upstream user.
- [ ] Record CTA as `reproduce`, `fixture`, `challenge`, or `contribute` according to the asset.
- [ ] Compare downstream public evidence for root-link placements vs asset-link placements; do not claim causality without enough evidence.

### Task 16: Final verification for this plan

- [ ] 10 new public reusable technical assets are live after campaign approval: provenance index, LangGraph #8764 fixture, showcase entry, execution-result binding checklist, cross-runtime matrix, configured-vs-effective guide, terminal absence guide, lost-ack guide, intake template, evidence-pattern index.
- [ ] LangGraph #8764 fixture is backed by machine-readable fixture files, a focused test, exact-head full CI and explicit `UNVERIFIED` boundary.
- [ ] No LangGraph dependency was added.
- [ ] Research matrix marks unknowns as unknown and includes source/license pins.
- [ ] Agent-facing index gives direct next actions.
- [ ] Campaign checkpoint records which repeated external failure classes changed AgentCI product priorities.
