import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_lifecycle_revalidated_requires_bound_continuity_evidence():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = []
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) != "PASS"
