import copy
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


def _passing_revalidated_snapshot():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = [
        {
            "snapshot_id": "snapshot-A",
            "capture_epoch": 10,
            "restore_epoch": 11,
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
            "event_id": "event-lifecycle-restore-11",
            "event_type": "lifecycle",
            "occurred_at_utc": "2026-08-11T03:00:01.500000Z",
            "monotonic_ns": 2100,
            "policy_epoch": 0,
            "authority_epoch": 0,
            "restore_epoch": 11,
            "source_id": "fixture-lifecycle-observer",
            "semantic_digest": "sha256:" + "0" * 64,
            "workload_identity": "fixture-workload",
            "attachment_id": "attach-1",
        }
    )
    _rebind(document)
    assert validator.expected_verdict(document) == "PASS"
    return document


def test_snapshot_identity_relabel_cannot_reuse_restore_observation():
    document = _passing_revalidated_snapshot()
    tampered = copy.deepcopy(document)
    tampered["lifecycle_continuity"][0]["snapshot_id"] = "snapshot-B"
    _rebind(tampered)

    assert validator.expected_verdict(tampered) != "PASS"
