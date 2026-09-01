# External Fixture Product Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn repeated external failure signals into 10 reusable public technical assets, with at least one new provider-neutral AgentCI fixture/showcase improvement built through RED→GREEN evidence.

**Architecture:** External GitHub/runtime issues are untrusted provenance inputs, not AgentCI truth. Cluster them by semantic invariant, choose the strongest evidence-backed class, create a small provider-neutral fixture or checklist/validator asset, validate it independently, then use the resulting artifact as a higher-conversion distribution destination in later cohorts. External projects remain upstream provenance and pattern sources; AgentCI does not import their runtime dependencies unless a separate experiment proves that necessary.

**Tech Stack:** Python 3.11, JSON fixtures, pytest, Markdown, AgentCI showcase catalog, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-01-50-touchpoint-growth-loop-design.md`

## Global Constraints

- Target: 10 new reusable public technical assets after campaign approval.
- At least one asset must include executable/reproducible machine-readable evidence rather than prose only.
- External issue claims stay `UNVERIFIED` until independently reproduced or represented as a bounded upstream-provenance fixture with an explicit claim boundary.
- Do not add provider SDK dependencies merely to reproduce an evidence shape.
- Preserve upstream issue URLs and contributor credit.
- Fixture presence does not certify a backend.
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

- [ ] **Step 3: Select one executable-fixture candidate**

Default choice is the highest cluster with at least two independent upstream cases and no existing equivalent canonical fixture. A single exceptionally strong case may win if it has deterministic reproduction and contributor intent.

### Task 2: Asset 1 — machine-readable external provenance index

**Files:**
- Create: `.company/research/external/50-touchpoint-provenance-index.json`
- Test: `tests/test_external_provenance_index.py`

**Interfaces:**
- Each record: `id`, `source_url`, `source_repository`, `semantic_class`, `status`, `agentci_artifact`, `claim_boundary`.
- `status`: `observed-upstream | reduced-fixture | independently-reproduced | merged-contribution`.

- [ ] **Step 1: RED — duplicate or missing source URLs fail**

Write a test loading a temporary index with duplicate `source_url` and require failure from a small validation helper or test-local validator.

- [ ] **Step 2: GREEN — add canonical index with uniqueness test**

Do not invent reproduction status. Initial entries may remain `observed-upstream`.

- [ ] **Step 3: Add secret/material scan assertions**

Reject obvious credential/token fields in persisted provenance records.

### Task 3: Select and specify the new executable fixture

**Files:**
- Create issue in AgentCI with exact upstream provenance and acceptance criteria.
- Later fixture files under `tests/fixtures/` or `examples/` following the existing semantic domain.

**Interfaces:**
- The issue must define:

```text
upstream source(s)
portable invariant
input/state identities
negative control
expected AgentCI verdict/validation state
what remains unverified
no-provider-dependency boundary
```

- [ ] Search existing AgentCI issues/fixtures for semantic duplication.
- [ ] Create one issue only if no equivalent task exists.
- [ ] Name exact future test/fixture paths so an external contributor can start without private context.

### Task 4: RED for the selected external invariant

**Files:**
- Test path chosen in Task 3.
- Fixture source chosen in Task 3.

**Interfaces:**
- Test must fail against current AgentCI for the intended missing representation/validation behavior, or, when product validator already behaves correctly, fail because the new canonical fixture/catalog entry is absent.

- [ ] **Step 1: Write the smallest failing test first**

Example shape for a lost-ack/exactly-once case:

```python
def test_committed_effect_with_lost_ack_is_not_safe_to_blindly_replay():
    case = load_fixture('lost-ack-committed-effect.json')
    result = validate_or_classify(case)
    assert result.state != 'PASS'
```

Use actual existing AgentCI interfaces discovered from the selected domain; do not create a second verdict engine for convenience.

- [ ] **Step 2: Confirm RED reason**

Existing unrelated suite stays green; only the new missing contract/fixture assertion fails.

### Task 5: GREEN for the selected fixture

**Files:**
- Minimal production/schema/catalog changes required by Task 4.
- Canonical fixture + provenance metadata.

- [ ] Add only the structure needed to make the invariant machine-checkable.
- [ ] Preserve `UNVERIFIED` when material evidence is missing.
- [ ] Bind upstream provenance in fixture metadata without depending on upstream package imports.
- [ ] Run targeted GREEN, full pytest, compileall and relevant clean-wheel smoke.
- [ ] Hand exact head to a non-Fixer Challenger.

### Task 6: Challenger attack for the new fixture

**Files:**
- Prefer separate RED-only branch/PR if a material counterexample is found.

Attack at least:

```text
wrong input/work identity
stale/replayed evidence
missing effect identity
same-looking success with different durable state
missing terminal/cleanup state where relevant
copied digest/label without underlying semantic material
```

- [ ] Record Spec verdict and Standards verdict separately.
- [ ] If a counterexample survives, return the exact head immediately; do not approve based on green CI.
- [ ] If clean, hand to eligible Merge Decider.

### Task 7: Asset 2 — provider-neutral fixture README

**Files:**
- Create/update a README adjacent to the new fixture corpus.

**Interfaces:**
- Must answer: what failure this represents, how to run it, what PASS/FAIL/UNVERIFIED means, what it does not prove, upstream provenance.

- [ ] Include one exact reproduction/validation command.
- [ ] Include one negative control description.
- [ ] Include no backend certification wording.

### Task 8: Asset 3 — showcase entry for the new fixture

**Files:**
- Modify `showcase/catalog-v1.json` only after #130 or its successor is on the relevant integration base.
- Modify truth-contract tests as required.

**Interfaces:**
- New entry uses `evidence_maturity: fixture`.
- `certification_claim` must remain `false`.
- `repository_path` must exist.
- `released_command` must be parseable on the documented line/version.

- [ ] RED: test expects the new fixture ID absent/currently undiscoverable.
- [ ] GREEN: add exactly one catalog entry.
- [ ] Run catalog validator and clean-wheel installed fallback smoke.

### Task 9: Asset 4 — external execution-result binding checklist

**Files:**
- Create: `docs/testing/execution-result-binding.md`

**Interfaces:**
- Inspired by adjacent runners such as agent-belt without importing them.

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

End with a contribution CTA for runners that can export this evidence.

### Task 10: Asset 5 — cross-runtime evidence comparison matrix

**Files:**
- Create: `.company/research/external/cross-runtime-evidence-matrix-2026-09-01.md`

**Interfaces:**
- Compare only documented/public evidence surfaces for projects already researched (for example SWE-ReX, Kubernetes Agent Sandbox, Docker Sandboxes, E2B, OpenHands, agent-belt where relevant).

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

Use `unknown` rather than inference.

### Task 11: Asset 6 — configured-vs-effective capability matrix

**Files:**
- Create: `docs/testing/configured-vs-effective-capability.md`

**Interfaces:**
- Explain why declared support cannot prove combinations work (e.g. tool + output-schema combinations, installed backend vs usable backend).

Include one deterministic matrix example:

```text
configured=true, discovered=true, effective=unknown -> non-PASS
configured=true, probe fails -> not-ready
configured=true, bounded real probe succeeds -> evidence limited to probed capability
```

Do not claim Google ADK or other upstream compatibility from the example.

### Task 12: Asset 7 — terminal evidence absence pattern

**Files:**
- Create: `docs/testing/negative-terminal-evidence.md`

**Interfaces:**
- Define how to record “no terminal event observed” without turning absence into “sandbox died” or “command succeeded”.

Include:

```text
last observed event identity
observation source
bounded observation window
resource/lifecycle health source if available
negative evidence statement
allowed classifications
```

### Task 13: Asset 8 — exactly-once / lost-ack checklist

**Files:**
- Create: `docs/testing/exactly-once-lost-ack.md`

**Interfaces:**
- Separate commit truth from caller acknowledgement.
- Require durable reconciliation before blind replay.
- Link only to public upstream provenance where already recorded.

### Task 14: Asset 9 — upstream fixture contribution template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/upstream_fixture.yml` or extend the existing backend evidence template if that is the better single entry point.

**Interfaces:**
- Required fields:

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

- [ ] Inspect existing issue templates first and avoid duplicate intake forms.
- [ ] If extending the existing form, add only missing fields.

### Task 15: Asset 10 — campaign-derived technical index

**Files:**
- Create: `docs/testing/agent-evidence-patterns.md`

**Interfaces:**
- Search-oriented index linking the nine preceding technical assets and existing canonical AgentCI evidence docs.
- Each entry: problem phrase → use this AgentCI asset → exact next command/action → claim boundary.

Example row:

```text
"agent says success but tool failed" -> false-PASS taxonomy -> inspect/reduce fixture -> telemetry truth is not execution truth
```

Do not duplicate full content; this is routing/indexing.

### Task 16: Reuse technical assets in later distribution cohorts

- [ ] For every new external placement after an applicable asset exists, prefer linking the exact technical asset over linking only the repository root when it materially helps the upstream user.
- [ ] Record CTA as `reproduce`, `fixture`, `challenge`, or `contribute` according to the asset.
- [ ] Compare downstream evidence for root-link placements vs asset-link placements; do not claim causality without enough evidence.

### Task 17: Final verification for this plan

- [ ] 10 new public reusable technical assets are live after campaign approval.
- [ ] At least one asset is backed by a machine-readable fixture/test and exact-head CI.
- [ ] New fixture has upstream provenance and explicit non-certification boundary.
- [ ] No copied upstream code/dependency was introduced without license/dependency review.
- [ ] Research matrix marks unknowns as unknown.
- [ ] Agent-facing index gives direct next actions.
- [ ] Campaign checkpoint records which repeated external failure classes changed AgentCI product priorities.
