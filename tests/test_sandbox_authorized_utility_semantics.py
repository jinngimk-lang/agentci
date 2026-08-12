import json
from pathlib import Path

from scripts.validate_sandbox_evidence import (
    artifact_digest,
    authority_binding_digest,
    event_semantic_digest,
    expected_verdict,
    policy_history_digest,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    assert expected_verdict(document) == "PASS"
    assert validate(document) == []
    return document


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def test_authorized_utility_cannot_be_proved_by_unrelated_file_event():
    """B/#26: workspace utility cannot borrow an unrelated sensitive-read event."""
    document = _passing_fixture()
    utility = next(
        assertion
        for assertion in document["assertions"]
        if assertion["assertion_id"] == "workspace-read-write-available"
    )
    utility["evidence_event_ids"] = ["event-sensitive-read"]
    _rebind_all(document)

    assert expected_verdict(document) != "PASS"
    assert any("authorized utility" in error for error in validate(document))
