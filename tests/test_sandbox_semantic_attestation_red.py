import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator
from scripts.execution_attestation import execution_attestation_valid

ROOT = Path(__file__).resolve().parents[1]
RED_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_red_read_succeeded_evidence_cannot_be_flipped_into_pass():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    sensitive = next(a for a in document["assertions"] if a["assertion_id"] == "sensitive-canary-unreadable")
    event = next(e for e in document["events"] if e.get("resource") == "/synthetic-sensitive-canary")
    assert event["observed_result"] == "read-succeeded"

    sensitive["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)

    assert validator.expected_verdict(document) != "PASS"


def test_execution_attestation_binds_assertion_semantic_digest():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    process_event = next(e for e in document["events"] if e["event_type"] == "process")
    assert execution_attestation_valid(document, process_event["event_id"], process_event["source_id"]) is True

    tampered = copy.deepcopy(document)
    sensitive = next(e for e in tampered["events"] if e.get("resource") == "/synthetic-sensitive-canary")
    sensitive["observed_result"] = "denied"
    sensitive["semantic_digest"] = validator.event_semantic_digest(sensitive)

    # Identity/source/timing stay unchanged. The external execution receipt
    # must still fail because the signed semantic digest changed.
    assert execution_attestation_valid(tampered, process_event["event_id"], process_event["source_id"]) is False
