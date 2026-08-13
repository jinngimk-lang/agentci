import json
from pathlib import Path

from scripts.validate_sandbox_evidence import (
    artifact_digest,
    authority_binding_digest,
    event_semantic_digest,
    expected_verdict,
    policy_history_digest,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    assert expected_verdict(document) == "PASS"
    assert validate(document) == []
    return document


def test_pass_rejects_workload_self_sourced_privilege_expansion_without_external_authority():
    document = _passing_fixture()

    # The same workload that benefits from the policy is now recorded as the
    # source of a privilege-expanding epoch. No separately authenticated
    # external authority/grant/decision is present in the EvidenceEnvelope.
    policy = document["policy_history"][0]
    policy["delta_class"] = "expansion"
    policy["source_principal_id"] = "fixture-workload"
    _rebind_all(document)

    assert expected_verdict(document) != "PASS"
    errors = validate(document)
    assert any("expansion" in error.lower() and "authority" in error.lower() for error in errors)
