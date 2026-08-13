import copy
import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, authority_binding_digest, event_semantic_digest, expected_verdict, policy_history_digest, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-control-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert expected_verdict(document) == "PASS"
    assert validate(document) == []
    return document


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)


def test_pass_attachment_provenance_requires_healthy_mandatory_source():
    document = _passing_fixture()
    provenance = next(event for event in document["events"] if event["event_type"] == "policy-attachment")
    optional_source = copy.deepcopy(document["telemetry"][0])
    optional_source["source_id"] = "optional-degraded-attachment-provenance"
    optional_source["coverage"] = "optional"
    optional_source["health"] = "degraded"
    document["telemetry"].append(optional_source)
    provenance["source_id"] = optional_source["source_id"]
    provenance["semantic_digest"] = event_semantic_digest(provenance)
    document["policy_attachments"][0]["evidence_digest"] = provenance["semantic_digest"]
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("attachment effectiveness provenance" in error and "healthy mandatory telemetry source" in error for error in validate(document))
