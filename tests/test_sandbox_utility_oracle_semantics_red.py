import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_oracle_digest_alone_cannot_prove_action_resource_and_observed_result():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"

    utility_event = next(
        event for event in document["events"] if event["event_id"] == "event-workspace-utility"
    )

    # PR #50 adds an oracle_ref digest, but the event still does not carry the
    # operation/resource/result evidence that PR #49's falsifiable claim requires.
    assert utility_event["event_type"] == "utility"
    assert "oracle_ref" in utility_event
    assert "action" not in utility_event
    assert "resource" not in utility_event
    assert "observed_result" not in utility_event

    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert any("utility" in error.lower() and "oracle" in error.lower() for error in errors)
