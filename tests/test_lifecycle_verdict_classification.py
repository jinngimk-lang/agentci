import json
from pathlib import Path

import pytest

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    assert expected_verdict(document) == "PASS"
    return document


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("network_activity", "residual"),
        ("credential_state", "residual"),
    ],
)
def test_authenticated_material_residual_is_backend_fail(field, value):
    document = _passing_fixture()
    document["post_conditions"][field] = value
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) == "FAIL"


def test_unattested_preserved_lifecycle_is_unverified_not_backend_fail():
    document = _passing_fixture()
    document["post_conditions"]["lifecycle_state"] = "preserved"
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) == "UNVERIFIED"


def test_missing_lifecycle_revalidation_evidence_is_unverified_not_backend_fail():
    document = _passing_fixture()
    document["post_conditions"]["lifecycle_state"] = "revalidated"
    document["lifecycle_continuity"] = []
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)

    assert expected_verdict(document) == "UNVERIFIED"
