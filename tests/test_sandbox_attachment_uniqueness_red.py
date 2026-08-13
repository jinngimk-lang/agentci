import copy
import json
from pathlib import Path

from scripts.validate_sandbox_evidence import (
    artifact_digest,
    authority_binding_digest,
    event_semantic_digest,
    expected_verdict,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    assert expected_verdict(document) == "PASS"
    return document


def test_pass_rejects_multiple_effective_attachments_for_same_workload_and_epoch():
    document = _passing_fixture()

    second_attachment = copy.deepcopy(document["policy_attachments"][0])
    second_attachment["attachment_id"] = "attach-2"

    second_provenance = {
        "event_id": "event-policy-attachment-ambiguous",
        "event_type": "policy-attachment",
        "occurred_at_utc": "2026-08-11T03:00:00Z",
        "monotonic_ns": 1550,
        "policy_epoch": 0,
        "authority_epoch": 0,
        "source_id": "fixture-policy-observer",
        "workload_identity": "fixture-workload",
        "attachment_id": "attach-2",
    }
    second_provenance["semantic_digest"] = event_semantic_digest(second_provenance)
    second_attachment["evidence_digest"] = second_provenance["semantic_digest"]

    document["policy_attachments"].append(second_attachment)
    document["events"].append(second_provenance)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) != "PASS"
