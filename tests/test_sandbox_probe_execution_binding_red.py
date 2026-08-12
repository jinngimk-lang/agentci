import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
TEST_CASE = ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"


def _rebind(document):
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_pass_must_bind_evidence_to_the_canonical_probe_that_actually_ran(monkeypatch):
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical_case = json.loads(TEST_CASE.read_text(encoding="utf-8"))
    changed_case = copy.deepcopy(canonical_case)

    # Keep the case ID, assertions, telemetry obligations, and oracle unchanged,
    # but replace the actual probe command with a materially different safe
    # synthetic command. The existing evidence events still describe the old
    # sensitive-canary attempt; no event or receipt records which argv ran.
    changed_case["probe"]["argv"] = ["synthetic-probe-v2", "--different-target"]
    monkeypatch.setattr(
        validator,
        "_load_test_case",
        lambda case_id: copy.deepcopy(changed_case) if case_id == changed_case["case_id"] else None,
    )

    # Convert the deliberately permissive red control into a nominal PASS and
    # rebind all envelope-level digests to the newly selected canonical case.
    # If probe execution is not independently bound, the old event evidence can
    # be reinterpreted as proof that the new probe ran.
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert validator.expected_verdict(document) != "PASS"
    errors = validator.validate(document)
    assert any("probe" in error.lower() or "execution" in error.lower() for error in errors)
