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
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
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


def test_healthy_mandatory_source_cannot_self_declare_policy_attachment_suitability():
    """B/#26: source health is not TestCase-bound observer suitability."""
    document = _passing_fixture()
    document["telemetry"].append(
        {
            "source_id": "synthetic-filesystem-only-observer",
            "layer": "filesystem",
            "version": "v1",
            "health": "healthy",
            "coverage": "mandatory",
        }
    )
    provenance = next(event for event in document["events"] if event["event_type"] == "policy-attachment")
    provenance["source_id"] = "synthetic-filesystem-only-observer"
    document["policy_attachments"][0]["evidence_digest"] = event_semantic_digest(provenance)
    _rebind_all(document)

    assert expected_verdict(document) != "PASS"
    assert any("source suitability" in error for error in validate(document))
