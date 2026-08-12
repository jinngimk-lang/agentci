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


def test_pass_must_bind_evidence_to_the_canonical_probe_that_actually_ran_on_current_a_head(monkeypatch):
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical_case = json.loads(TEST_CASE.read_text(encoding="utf-8"))
    changed_case = copy.deepcopy(canonical_case)

    changed_case["probe"]["argv"] = ["synthetic-probe-v2", "--different-target"]
    monkeypatch.setattr(
        validator,
        "_load_test_case",
        lambda case_id: copy.deepcopy(changed_case) if case_id == changed_case["case_id"] else None,
    )

    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert validator.expected_verdict(document) != "PASS"
    errors = validator.validate(document)
    assert any("probe execution" in error.lower() or "execution provenance" in error.lower() for error in errors)


def test_missing_execution_provenance_event_is_unverified():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    execution_id = validator.execution_binding_id(
        document,
        validator._load_test_case(document["case_id"]),
        next(event for event in document["events"] if event["event_type"] == "file"),
    )
    document["events"] = [event for event in document["events"] if event["event_id"] != execution_id]
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert validator.expected_verdict(document) == "UNVERIFIED"
    assert any("execution provenance event" in error.lower() for error in validator.validate(document))


def test_execution_provenance_is_distinct_from_authority_receipts():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    execution_event = next(event for event in document["events"] if event["event_type"] == "process")
    execution_event["decision_id"] = "opaque-decision-string"
    execution_event["receipt_id"] = "opaque-enforcement-receipt-string"
    execution_event["semantic_digest"] = validator.event_semantic_digest(execution_event)
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert validator.expected_verdict(document) == "PASS"
