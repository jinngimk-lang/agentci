import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, authority_binding_digest, event_semantic_digest, expected_verdict, policy_history_digest, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-control-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert expected_verdict(document) == "PASS" and validate(document) == []
    return document


def _rebind_all(document):
    for event in document.get("events", []): event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def test_authorized_utility_cannot_be_proved_by_unrelated_file_event():
    document = _passing_fixture()
    utility = next(a for a in document["assertions"] if a["assertion_id"] == "workspace-read-write-available")
    sensitive = next(a for a in document["assertions"] if a["assertion_id"] == "sensitive-canary-unreadable")
    utility["evidence_event_ids"] = list(sensitive["evidence_event_ids"])
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("authorized utility" in error for error in validate(document))
