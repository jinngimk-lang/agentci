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


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def test_pass_cannot_omit_a_canonical_mandatory_nonutility_assertion():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    # The canonical TestCase requires both sensitive-canary-unreadable and
    # workspace-read-write-available. Keep only the authorized-utility PASS and
    # remove the failed containment assertion plus its event. A PASS must not be
    # constructible by shrinking the EvidenceEnvelope's assertion set.
    document["assertions"] = [
        assertion
        for assertion in document["assertions"]
        if assertion["assertion_id"] == "workspace-read-write-available"
    ]
    document["events"] = [
        event
        for event in document["events"]
        if event["event_id"] != "event-sensitive-read"
    ]
    document["verdict"] = "PASS"
    _rebind_all(document)

    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert any("mandatory assertion" in error.lower() for error in errors)
