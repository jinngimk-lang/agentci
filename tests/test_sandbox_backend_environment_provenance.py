import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, authority_binding_digest, event_semantic_digest, expected_verdict, policy_history_digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-control-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []): event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _passing_fixture():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert expected_verdict(document) == "PASS"
    return document


def test_pass_evidence_must_bind_exact_backend_and_environment_provenance():
    document = _passing_fixture()
    document["backend"]["provider"] = "different-provider"
    document["backend"]["version"] = "different-version"
    document["backend"]["build_or_image_digest"] = "sha256:" + "9" * 64
    document["backend"]["effective_backend_instance"] = "different-instance"
    document["environment_fingerprint"] = "sha256:" + "8" * 64
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
