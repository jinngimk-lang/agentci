import copy
import json
from pathlib import Path

import pytest

from scripts.validate_sandbox_evidence import (
    artifact_digest,
    authority_binding_digest,
    event_semantic_digest,
    expected_verdict,
    load_evidence_json,
    policy_history_digest,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
SCHEMA = ROOT / "schemas" / "sandbox-certification-v0alpha1.schema.json"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _rehash(document):
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = event_semantic_digest(event)
    document["policy_history_digest"] = policy_history_digest(document)
    document["authority_digest"] = authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = artifact_digest(document)
    return document


def _passing_fixture():
    document = _fixture()
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rehash(document)
    assert expected_verdict(document) == "PASS"
    assert validate(document) == []
    return document


def _assert_rejected_pass(document, exact_error):
    document["verdict"] = "PASS"
    _rebind_all(document)
    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert exact_error in errors


def test_raw_duplicate_top_level_key_is_rejected_before_semantic_validation():
    raw = FIXTURE.read_text(encoding="utf-8")
    raw = raw.replace('"kind": "EvidenceEnvelope",', '"kind": "EvidenceEnvelope",\n  "kind": "Observation",', 1)
    with pytest.raises(ValueError, match="duplicate JSON object key: kind"):
        load_evidence_json(raw)


def test_raw_duplicate_nested_security_key_is_rejected_before_digesting():
    raw = FIXTURE.read_text(encoding="utf-8")
    raw = raw.replace('"policy_epoch": 0,', '"policy_epoch": 0,\n      "policy_epoch": 99,', 1)
    with pytest.raises(ValueError, match="duplicate JSON object key: policy_epoch"):
        load_evidence_json(raw)


def test_red_control_is_deterministically_fail():
    document = _fixture()
    assert expected_verdict(document) == "FAIL"
    assert validate(document) == []


def test_unexecuted_case_cannot_be_pass():
    document = _fixture()
    document["probe_executed"] = False
    document["verdict"] = "PASS"
    _rehash(document)
    assert expected_verdict(document) == "UNVERIFIED"
    assert any("verdict mismatch" in error for error in validate(document))


def test_harness_error_cannot_be_backend_pass():
    document = _fixture()
    document["execution_status"] = "harness-error"
    document["verdict"] = "PASS"
    _rehash(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_event_must_bind_to_effective_policy_epoch():
    document = _fixture()
    document["events"][0]["policy_epoch"] = 99
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_policy_epoch_authority_mismatch_is_unverified():
    document = _fixture()
    document["events"][0]["authority_epoch"] = 99
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_event_before_policy_effective_time_is_unverified():
    document = _fixture()
    document["events"][0]["monotonic_ns"] = 1
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_event_before_policy_effective_wall_clock_is_unverified():
    document = _fixture()
    document["events"][0]["occurred_at_utc"] = "2026-08-10T23:59:59Z"
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_policy_history_epochs_must_be_unique():
    document = _fixture()
    duplicate = copy.deepcopy(document["policy_history"][0])
    duplicate["effective_at_monotonic_ns"] += 1
    document["policy_history"].append(duplicate)
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_policy_history_monotonic_time_must_increase():
    document = _fixture()
    second = copy.deepcopy(document["policy_history"][0])
    second["policy_epoch"] = 2
    second["effective_at_monotonic_ns"] = document["policy_history"][0]["effective_at_monotonic_ns"]
    document["policy_history"].append(second)
    _rebind_all(document)
    assert expected_verdict(document) == "UNVERIFIED"


def test_pass_requires_mandatory_telemetry():
    document = _passing_fixture()
    document["telemetry"] = []
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_degraded_mandatory_collector_cannot_support_pass():
    document = _passing_fixture()
    document["telemetry"][0]["health"] = "degraded"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_mandatory_not_applicable_cannot_be_hidden_inside_pass():
    document = _passing_fixture()
    document["assertions"][0]["state"] = "NOT-APPLICABLE"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_assertion_evidence_refs_must_resolve_to_existing_events():
    document = _passing_fixture()
    document["assertions"][0]["evidence_event_ids"] = ["missing-event"]
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_failed_assertion_cannot_be_downgraded_to_optional_to_create_pass():
    document = _passing_fixture()
    document["assertions"].append({"assertion_id": "optional-fail", "mandatory": False, "state": "FAIL", "evidence_event_ids": []})
    _rebind_all(document)
    assert expected_verdict(document) == "FAIL"


def test_pass_requires_authorized_utility_evidence():
    document = _passing_fixture()
    document["assertions"] = [x for x in document["assertions"] if x["assertion_id"] != "workspace-read-write-available"]
    document["events"] = [x for x in document["events"] if x["event_id"] != "event-workspace-utility"]
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("authorized utility" in error for error in validate({**document, "verdict": "PASS", "canonicalization": {**document["canonicalization"], "artifact_digest": artifact_digest({**document, "verdict": "PASS"})}}))


def test_pass_requires_effective_policy_attachment():
    document = _passing_fixture()
    document["policy_attachments"] = []
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_pass_event_requires_effective_attachment_for_governing_policy_epoch():
    document = _passing_fixture()
    p1 = copy.deepcopy(document["policy_history"][0])
    p1["policy_epoch"] = 1
    p1["policy_digest"] = "sha256:" + "4" * 64
    p1["authority_epoch"] = 1
    p1["effective_at_utc"] = "2026-08-11T03:00:02Z"
    p1["effective_at_monotonic_ns"] = 2500
    p1["previous_policy_digest"] = document["policy_history"][0]["policy_digest"]
    document["policy_history"].append(p1)
    event = document["events"][0]
    event["policy_epoch"] = 1
    event["authority_epoch"] = 1
    event["occurred_at_utc"] = "2026-08-11T03:00:03Z"
    event["monotonic_ns"] = 3000
    document["verdict"] = "PASS"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("effective attachment" in error and "policy epoch 1" in error for error in validate(document))


def test_pass_event_attachment_must_match_workload_identity():
    document = _passing_fixture()
    document["policy_attachments"][0]["workload_identity"] = "different-workload"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"
    assert any("workload identity" in error for error in validate(document))


def test_pass_event_cannot_be_authenticated_by_attachment_that_becomes_effective_later():
    document = _passing_fixture()
    attachment_event = next(event for event in document["events"] if event["event_type"] == "policy-attachment")
    pass_event = document["events"][0]
    attachment_event["occurred_at_utc"] = "2026-08-11T03:00:02Z"
    attachment_event["monotonic_ns"] = pass_event["monotonic_ns"] + 1
    document["policy_attachments"][0]["evidence_digest"] = event_semantic_digest(attachment_event)
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_policy_history_digest_must_bind_the_actual_history():
    document = _passing_fixture()
    document["policy_history_digest"] = "sha256:" + "0" * 64
    _rehash(document)
    assert expected_verdict(document) != "PASS"


def test_authority_digest_must_bind_the_authority_projection():
    document = _passing_fixture()
    document["authority_digest"] = "sha256:" + "0" * 64
    _rehash(document)
    assert expected_verdict(document) != "PASS"


def test_event_semantic_digest_must_bind_event_semantics():
    document = _passing_fixture()
    document["events"][0]["semantic_digest"] = "sha256:" + "0" * 64
    _rehash(document)
    assert expected_verdict(document) != "PASS"


def test_mandatory_pass_requires_event_evidence():
    document = _passing_fixture()
    document["assertions"][0]["evidence_event_ids"] = []
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_mandatory_pass_event_source_must_be_declared_and_healthy():
    document = _passing_fixture()
    document["events"][0]["source_id"] = "ghost-source"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_duplicate_telemetry_source_id_is_rejected():
    document = _passing_fixture()
    document["telemetry"].append(copy.deepcopy(document["telemetry"][0]))
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_duplicate_event_id_is_rejected():
    document = _passing_fixture()
    document["events"].append(copy.deepcopy(document["events"][0]))
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_duplicate_assertion_id_is_rejected():
    document = _passing_fixture()
    document["assertions"].append(copy.deepcopy(document["assertions"][0]))
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_duplicate_attachment_id_is_rejected():
    document = _passing_fixture()
    document["policy_attachments"].append(copy.deepcopy(document["policy_attachments"][0]))
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_invalid_event_datetime_is_unverified():
    document = _passing_fixture()
    document["events"][0]["occurred_at_utc"] = "not-a-date-time"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_invalid_policy_datetime_is_unverified():
    document = _passing_fixture()
    document["policy_history"][0]["effective_at_utc"] = "not-a-date-time"
    _rebind_all(document)
    assert expected_verdict(document) != "PASS"


def test_schema_exists_and_defines_four_distinct_objects():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert {"PolicySpec", "Observation", "TestCase", "EvidenceEnvelope"}.issubset(schema["$defs"])
