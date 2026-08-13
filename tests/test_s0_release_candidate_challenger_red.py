import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as evidence
from scripts.execution_attestation import execution_attestation_valid
from scripts.validate_sandbox_authority import validate as validate_authority
from tests.test_sandbox_authority_semantics import _bundle

ROOT = Path(__file__).resolve().parents[1]
RED_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = evidence.event_semantic_digest(event)
    document["policy_history_digest"] = evidence.policy_history_digest(document)
    document["authority_digest"] = evidence.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = evidence.artifact_digest(document)
    return document


def test_read_succeeded_evidence_cannot_be_flipped_to_pass():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    sensitive = next(a for a in document["assertions"] if a["assertion_id"] == "sensitive-canary-unreadable")
    event = next(e for e in document["events"] if e.get("resource") == "/synthetic-sensitive-canary")
    assert event.get("observed_result") == "read-succeeded"
    sensitive["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)
    assert evidence.expected_verdict(document) != "PASS"


def test_external_execution_attestation_authenticates_assertion_semantics():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    process_event = next(event for event in document["events"] if event["event_type"] == "process")
    assert execution_attestation_valid(document, process_event["event_id"], process_event["source_id"])
    tampered = copy.deepcopy(document)
    sensitive = next(event for event in tampered["events"] if event.get("resource") == "/synthetic-sensitive-canary")
    sensitive["observed_result"] = "denied"
    sensitive["semantic_digest"] = evidence.event_semantic_digest(sensitive)
    assert not execution_attestation_valid(tampered, process_event["event_id"], process_event["source_id"])


def test_attested_workload_identity_does_not_create_grant_issuer_authority():
    bundle = _bundle()
    bundle["grants"][0]["issuer_principal_id"] = "workload-1"
    assert validate_authority(copy.deepcopy(bundle)) != []
