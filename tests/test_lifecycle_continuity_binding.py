import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def test_lifecycle_revalidated_rejects_unbound_self_declared_continuity():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = [
        {
            "snapshot_id": "self-declared-snapshot-without-observation",
            "capture_epoch": 100,
            "restore_epoch": 101,
            "process_state": "revalidated",
            "socket_fd_state": "revalidated",
            "credential_session_state": "revalidated",
            "policy_attachment_state": "revalidated",
        }
    ]
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)

    errors = validator.validate(document)
    assert validator.expected_verdict(document) == "UNVERIFIED"
    assert "lifecycle continuity self-declared-snapshot-without-observation requires exactly one observed lifecycle event" in errors
