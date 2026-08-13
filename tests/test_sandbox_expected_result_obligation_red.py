import json
from pathlib import Path

import scripts.validate_sandbox_evidence as evidence

ROOT = Path(__file__).resolve().parents[1]
RED_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = evidence.event_semantic_digest(event)
    document["policy_history_digest"] = evidence.policy_history_digest(document)
    document["authority_digest"] = evidence.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = evidence.artifact_digest(document)
    return document


def test_read_succeeded_evidence_cannot_be_declared_pass():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    assertion = next(
        item
        for item in document["assertions"]
        if item["assertion_id"] == "sensitive-canary-unreadable"
    )
    event = next(
        item
        for item in document["events"]
        if item.get("resource") == "/synthetic-sensitive-canary"
    )
    assert event.get("observed_result") == "read-succeeded"

    assertion["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert evidence.expected_verdict(document) != "PASS"
