import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def test_lifecycle_revalidated_requires_bound_continuity_evidence():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = []
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)

    errors = validator.validate(document)
    assert validator.expected_verdict(document) == "UNVERIFIED"
    assert "revalidated lifecycle state requires observed lifecycle continuity" in errors
