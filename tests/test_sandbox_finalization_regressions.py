import copy
import json
from pathlib import Path

import pytest

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
TEST_CASE = ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _canonical_case():
    return json.loads(TEST_CASE.read_text(encoding="utf-8"))


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def _passing_fixture():
    document = _fixture()
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    assert validator.expected_verdict(document) == "PASS"
    return document


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("network_activity", "residual"),
        ("credential_state", "residual"),
        ("lifecycle_state", "preserved"),
    ],
)
def test_material_postcondition_residuals_cannot_certify_pass(field, value):
    document = _passing_fixture()
    document["post_conditions"][field] = value
    _rebind_all(document)
    assert validator.expected_verdict(document) != "PASS"


def test_lifecycle_revalidated_requires_observed_continuity():
    document = _passing_fixture()
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = [
        {
            "snapshot_id": "snapshot-1",
            "capture_epoch": 10,
            "restore_epoch": 11,
            "process_state": "revalidated",
            "socket_fd_state": "revalidated",
            "credential_session_state": "revalidated",
            "policy_attachment_state": "revalidated",
        }
    ]
    _rebind_all(document)
    assert validator.expected_verdict(document) != "PASS"


def test_authorized_utility_cannot_be_proved_by_relabeling_unrelated_event():
    document = _passing_fixture()
    security_event = document["events"][0]
    security_event["event_type"] = "utility"
    utility_assertion = next(
        item for item in document["assertions"] if item["assertion_id"] == "workspace-read-write-available"
    )
    utility_assertion["evidence_event_ids"] = [security_event["event_id"]]
    document["events"] = [
        event
        for event in document["events"]
        if not event["event_id"].endswith(":event-workspace-utility")
    ]
    _rebind_all(document)
    assert validator.expected_verdict(document) != "PASS"


def test_network_probe_requires_typed_exact_channel_evidence(monkeypatch):
    document = _passing_fixture()
    network_case = _canonical_case()
    network_case["capability_domain"] = "network"
    network_case["claim"] = "HTTPS egress boundary and workspace utility are both preserved"
    network_case["probe"]["network_channel"] = "https"
    monkeypatch.setattr(validator, "_load_test_case", lambda case_id: copy.deepcopy(network_case))
    monkeypatch.setattr(validator, "_execution_binding_errors", lambda *args, **kwargs: [])

    document["telemetry"][0]["layer"] = "network"
    security_event = document["events"][0]
    security_event["event_type"] = "network"
    security_event["channel"] = "udp"
    security_event["endpoint"] = "198.51.100.7:443"
    document["events"][1]["event_type"] = "utility"
    _rebind_all(document)

    assert validator.expected_verdict(document) != "PASS"
