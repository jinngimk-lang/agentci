import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, authority_binding_digest, event_semantic_digest, expected_verdict, policy_history_digest, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-control-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []): event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert expected_verdict(document) == "PASS" and validate(document) == []
    return document


def test_pass_rejects_workload_self_sourced_privilege_expansion_without_external_authority():
    document = _passing_fixture(); policy = document["policy_history"][0]
    policy["delta_class"] = "expansion"; policy["source_principal_id"] = "fixture-workload"; _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("expansion" in e.lower() and "authority" in e.lower() for e in validate(document))


def test_pass_rejects_expansion_without_decision_and_receipt_binding():
    document = _passing_fixture(); policy = document["policy_history"][0]
    policy["delta_class"] = "expansion"; policy["source_principal_id"] = "external-authority-fixture"; _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("expansion" in e.lower() and "authority" in e.lower() for e in validate(document))


def test_pass_rejects_string_only_decision_and_receipt_as_external_authority_proof():
    document = _passing_fixture(); policy = document["policy_history"][0]
    policy["delta_class"] = "expansion"; policy["source_principal_id"] = "external-authority-fixture"
    event = next(x for x in document["events"] if x["event_id"] == "event-policy-attachment-baseline")
    event["decision_id"] = "decision-external-expansion-1"; event["receipt_id"] = "receipt-external-expansion-1"; _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("expansion" in e.lower() and "authority" in e.lower() for e in validate(document))
