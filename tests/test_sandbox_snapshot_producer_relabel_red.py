import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def _passing_lifecycle_document():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
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
            "evidence_event_ids": ["event-restore-observation"],
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
            "event_id": "event-restore-observation",
            "event_type": "lifecycle",
            "occurred_at_utc": "2026-08-11T03:00:02Z",
            "monotonic_ns": 3000,
            "policy_epoch": 0,
            "authority_epoch": 0,
            "restore_epoch": 1,
            "snapshot_id": "snapshot-A",
            "source_id": "fixture-lifecycle-observer",
            "semantic_digest": "sha256:" + "0" * 64,
            "workload_identity": "fixture-workload",
            "attachment_id": "attach-1",
        }
    )
    _rebind(document)
    assert validator.expected_verdict(document) == "PASS"
    return document


def test_snapshot_identity_cannot_be_relabelled_by_same_evidence_producer():
    document = _passing_lifecycle_document()

    # Both copies of snapshot identity are producer-controlled. If changing
    # them together plus recomputing envelope-local digests still yields PASS,
    # equality is only self-consistency rather than provenance.
    document["lifecycle_continuity"][0]["snapshot_id"] = "snapshot-B"
    lifecycle_event = next(event for event in document["events"] if event["event_type"] == "lifecycle")
    lifecycle_event["snapshot_id"] = "snapshot-B"
    _rebind(document)

    assert validator.expected_verdict(document) != "PASS"
