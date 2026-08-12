import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, event_semantic_digest, expected_verdict, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_authorized_utility_pass_requires_oracle_bound_evidence():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"

    utility_event = next(
        event for event in document["events"] if event["event_id"] == "event-workspace-utility"
    )

    # RED provenance: PR #49 proved event_type=utility alone could satisfy
    # authorized utility. Remove the new immutable TestCase-oracle binding,
    # re-digest the mutated event/document, and require fail-closed behavior.
    utility_event.pop("oracle_ref")
    utility_event["semantic_digest"] = event_semantic_digest(utility_event)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert any("utility" in error.lower() and "oracle" in error.lower() for error in errors)
