import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_authorized_utility_pass_requires_oracle_bound_action_resource_and_result():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"

    utility_event = next(
        event for event in document["events"] if event["event_id"] == "event-workspace-utility"
    )

    # The current event only says event_type=utility. It does not prove which
    # authorized operation ran, which resource it exercised, or what result the
    # TestCase oracle observed. A generic utility-shaped event must not be able
    # to satisfy the workspace-read-write authorized-utility requirement.
    assert utility_event["event_type"] == "utility"
    assert "action" not in utility_event
    assert "resource" not in utility_event
    assert "observed_result" not in utility_event

    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert any("utility" in error.lower() and "oracle" in error.lower() for error in errors)
