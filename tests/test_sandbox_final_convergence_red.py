import copy
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
    test_case = json.loads(CASE.read_text(encoding="utf-8"))
    test_case["assertion_requirements"] = [
        {
            "assertion_id": "sensitive-canary-unreadable",
            "event_type": "file",
            "action": "read",
            "resource": "/synthetic-sensitive-canary",
            "expected_result": "denied",
        },
        {
            "assertion_id": "workspace-read-write-available",
            "event_type": "utility",
            "action": "read-write",
            "resource": "/workspace",
            "expected_result": "available",
        },
    ]
    return test_case


def test_typed_assertion_requirement_rejects_event_class_substitution(monkeypatch):
    document = _document()
    test_case = _typed_case()
    monkeypatch.setattr(sandbox_validator, "_load_test_case", lambda _case_id: test_case)

    sensitive = next(a for a in document["assertions"] if a["assertion_id"] == "sensitive-canary-unreadable")
    utility = next(a for a in document["assertions"] if a["assertion_id"] == "workspace-read-write-available")
    sensitive["evidence_event_ids"] = list(utility["evidence_event_ids"])
    _rebind(document)

    assert sandbox_validator.expected_verdict(document) != "PASS"


def test_authorized_utility_requires_typed_action_resource_and_result(monkeypatch):
    document = _document()
    test_case = _typed_case()
    monkeypatch.setattr(sandbox_validator, "_load_test_case", lambda _case_id: test_case)
    _rebind(document)

    # The current fixture has only event_type=utility.  It has no typed
    # action/resource/result evidence and therefore must not certify useful work.
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
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = [
        {
            "snapshot_id": "snapshot-A",
            "capture_epoch": 0,
            "restore_epoch": 1,
            "process_state": "revalidated",
            "socket_fd_state": "revalidated",
            "credential_session_state": "revalidated",
            "policy_attachment_state": "revalidated",
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
            "event_id": "event-restore-observation-without-snapshot-binding",
            "event_type": "lifecycle",
            "occurred_at_utc": "2026-08-11T03:00:02Z",
            "monotonic_ns": 3000,
            "policy_epoch": 0,
            "authority_epoch": 0,
            "restore_epoch": 1,
            "source_id": "fixture-lifecycle-observer",
            "semantic_digest": "sha256:" + "0" * 64,
            "workload_identity": "fixture-workload",
            "attachment_id": "attach-1",
        }
    )
    _rebind(document)

    # A restore observation in the right epoch/context is not proof that it
    # corresponds to the continuity record's exact snapshot identity.
    assert sandbox_validator.expected_verdict(document) != "PASS"
