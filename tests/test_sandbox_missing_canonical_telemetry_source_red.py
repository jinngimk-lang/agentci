import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
TESTCASE = ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_pass_requires_every_canonical_mandatory_telemetry_source(monkeypatch, tmp_path):
    testcase_dir = tmp_path / "testcases"
    testcase_dir.mkdir()
    testcase = json.loads(TESTCASE.read_text(encoding="utf-8"))
    testcase["mandatory_telemetry_sources"].append("fixture-process-observer")
    (testcase_dir / TESTCASE.name).write_text(json.dumps(testcase), encoding="utf-8")

    monkeypatch.setattr(validator, "TEST_CASE_DIR", testcase_dir)
    validator._load_test_case.cache_clear()

    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    # Deliberately omit the newly canonical mandatory source from the envelope.
    assert {source["source_id"] for source in document["telemetry"]} == {
        "fixture-file-observer",
        "fixture-policy-observer",
    }
    _rebind_all(document)

    # A canonical mandatory collector is absent, so PASS must be impossible.
    assert validator.expected_verdict(document) != "PASS"
