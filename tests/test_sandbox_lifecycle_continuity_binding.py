import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_lifecycle_revalidated_rejects_unbound_self_declared_continuity():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
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
    # No lifecycle event, snapshot observation, restore_epoch event binding, or
    # evidence reference proves the continuity object above. Merely choosing
    # safe-looking enum values must not turn an unknown restore into PASS.
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) != "PASS"
