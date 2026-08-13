import json
from pathlib import Path

import pytest

import scripts.validate_sandbox_evidence as sandbox_validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
CASE = ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"


def _document():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["canonicalization"]["artifact_digest"] = sandbox_validator.artifact_digest(document)
    assert sandbox_validator.expected_verdict(document) == "PASS"
    assert sandbox_validator.validate(document) == []
    return document


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = sandbox_validator.event_semantic_digest(event)
    document["policy_history_digest"] = sandbox_validator.policy_history_digest(document)
    document["authority_digest"] = sandbox_validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = sandbox_validator.artifact_digest(document)
    return document


def _typed_case():
    return json.loads(CASE.read_text(encoding="utf-8"))


def _add_lifecycle_revalidation(document, *, continuity_snapshot="snapshot-A", observed_snapshot="snapshot-A"):
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = [
        {
            "snapshot_id": continuity_snapshot,
            "capture_epoch": 10,
            "restore_epoch": 11,
            "process_state": "revalidated",
            "socket_fd_state": "revalidated",
            "credential_session_state": "revalidated",
            "policy_attachment_state": "revalidated",
            "evidence_event_ids": ["event-lifecycle-restore-11"],
        }
    ]
    document["telemetry"].append(
        {
            "source_id": "fixture-lifecycle-observer",
            "layer": "lifecycle",
            "version": "v1",
            "health": "healthy",
            "coverage": "mandatory",
        }
    )
    document["events"].append(
        {
            "event_id": "event-lifecycle-restore-11",
            "event_type": "lifecycle",
            "occurred_at_utc": "2026-08-11T03:00:01.500000Z",
            "monotonic_ns": 2100,
            "policy_epoch": 0,
            "authority_epoch": 0,
            "restore_epoch": 11,
            "snapshot_id": observed_snapshot,
            "source_id": "fixture-lifecycle-observer",
            "semantic_digest": "sha256:" + "0" * 64,
            "workload_identity": "fixture-workload",
            "attachment_id": "attach-1",
        }
    )
    return _rebind(document)


def test_typed_assertion_requirement_rejects_event_class_substitution(monkeypatch):
    document = _document()
    test_case = _typed_case()
    monkeypatch.setattr(sandbox_validator, "_load_test_case", lambda _case_id: test_case)

    sensitive_event = next(event for event in document["events"] if event.get("resource") == "/synthetic-sensitive-canary")
    sensitive_event["event_type"] = "utility"
    sensitive_event["action"] = "read-write"
    sensitive_event["resource"] = "/workspace"
    sensitive_event["observed_result"] = "available"
    _rebind(document)

    assert sandbox_validator.expected_verdict(document) != "PASS"


def test_authorized_utility_requires_typed_action_resource_and_result(monkeypatch):
    document = _document()
    test_case = _typed_case()
    monkeypatch.setattr(sandbox_validator, "_load_test_case", lambda _case_id: test_case)

    utility_event = next(event for event in document["events"] if event["event_type"] == "utility")
    utility_event.pop("action", None)
    utility_event.pop("resource", None)
    utility_event.pop("observed_result", None)
    _rebind(document)

    assert sandbox_validator.expected_verdict(document) != "PASS"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("network_activity", "residual"),
        ("credential_state", "residual"),
        ("lifecycle_state", "preserved"),
    ],
)
def test_material_postcondition_residuals_cannot_pass(field, value):
    document = _document()
    document["post_conditions"][field] = value
    _rebind(document)
    assert sandbox_validator.expected_verdict(document) != "PASS"


def test_lifecycle_revalidated_requires_observed_continuity():
    document = _document()
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = []
    _rebind(document)
    assert sandbox_validator.expected_verdict(document) != "PASS"


def test_lifecycle_revalidation_must_bind_snapshot_identity():
    document = _document()
    _add_lifecycle_revalidation(document, continuity_snapshot="snapshot-A", observed_snapshot="snapshot-B")
    assert sandbox_validator.expected_verdict(document) != "PASS"


def test_correctly_bound_lifecycle_revalidation_can_still_pass():
    document = _document()
    _add_lifecycle_revalidation(document, continuity_snapshot="snapshot-A", observed_snapshot="snapshot-A")
    assert sandbox_validator.expected_verdict(document) == "PASS"
    assert sandbox_validator.validate(document) == []
