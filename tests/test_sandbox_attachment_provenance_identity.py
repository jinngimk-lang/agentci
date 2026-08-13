import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, authority_binding_digest, event_semantic_digest, expected_verdict, policy_history_digest, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-control-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert expected_verdict(document) == "PASS"
    assert validate(document) == []
    return document


def test_pass_event_rejects_attachment_provenance_identity_substitution():
    document = _passing_fixture()
    provenance = next(event for event in document["events"] if event["event_type"] == "policy-attachment")
    provenance["attachment_id"] = "other-attachment"
    provenance["workload_identity"] = "other-workload"
    provenance["semantic_digest"] = event_semantic_digest(provenance)
    document["policy_attachments"][0]["evidence_digest"] = provenance["semantic_digest"]
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("attachment provenance identity" in error for error in validate(document))
