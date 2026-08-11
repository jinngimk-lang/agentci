import copy
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


def _accepted_pass_after_mutation(document):
    document["verdict"] = "PASS"
    _rebind_all(document)
    assert expected_verdict(document) == "PASS"
    return validate(document)


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
    _rehash(document)
    assert any("unknown policy epoch" in error for error in validate(document))


def test_material_unverified_assertion_is_not_pass():
    document = _fixture()
    document["assertions"] = [
        {
            "assertion_id": "utility",
            "mandatory": True,
            "state": "PASS",
            "evidence_event_ids": ["event-sensitive-read"],
        },
        {
            "assertion_id": "network-channel",
            "mandatory": True,
            "state": "UNVERIFIED",
            "evidence_event_ids": [],
        },
    ]
    document["verdict"] = "PARTIAL"
    _rehash(document)
    assert expected_verdict(document) == "PARTIAL"
    assert validate(document) == []


def test_digest_is_key_order_deterministic():
    document = _fixture()
    reversed_document = dict(reversed(list(document.items())))
    assert artifact_digest(document) == artifact_digest(reversed_document)


def test_schema_separates_network_capability_from_transport():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    policy = schema["$defs"]["PolicySpec"]["properties"]
    assert "network_capabilities" in policy
    assert "enforcement_transports" in policy
    channels = schema["$defs"]["NetworkChannel"]["enum"]
    assert {"http", "proxied-tcp", "direct-tcp", "udp", "icmp", "dns", "unix-socket", "ingress", "tunnel"}.issubset(channels)


def test_schema_tracks_attachment_and_restore_continuity():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    attachment_states = schema["$defs"]["PolicyAttachment"]["properties"]["state"]["enum"]
    assert attachment_states == ["configured", "selected", "attached", "effective", "failed", "unverified"]
    continuity = schema["$defs"]["LifecycleContinuity"]["properties"]
    assert {"process_state", "socket_fd_state", "credential_session_state", "policy_attachment_state"}.issubset(continuity)


# SBX-EVID-001 RED corpus: every mutation below must stop a recorded PASS.


def test_pass_requires_mandatory_telemetry():
    document = _passing_fixture()
    document["telemetry"] = []
    _rehash(document)
    assert any("telemetry" in error for error in validate(document))


def test_degraded_mandatory_collector_cannot_support_pass():
    document = _passing_fixture()
    document["telemetry"][0]["health"] = "degraded"
    _rehash(document)
    assert any("collector" in error or "telemetry" in error for error in validate(document))


def test_mandatory_not_applicable_cannot_be_hidden_inside_pass():
    document = _passing_fixture()
    document["assertions"].append(
        {
            "assertion_id": "material-network-check",
            "mandatory": True,
            "state": "NOT-APPLICABLE",
            "evidence_event_ids": [],
        }
    )
    document["verdict"] = "PASS"
    _rehash(document)
    assert any("not-applicable" in error.lower() or "verdict mismatch" in error for error in validate(document))


def test_assertion_evidence_refs_must_resolve_to_existing_events():
    document = _passing_fixture()
    document["assertions"][0]["evidence_event_ids"] = ["missing-event"]
    _rehash(document)
    assert any("missing-event" in error or "evidence event" in error for error in validate(document))


def test_mandatory_pass_requires_nonempty_event_evidence():
    document = _passing_fixture()
    document["assertions"][0]["evidence_event_ids"] = []
    document["events"] = []
    _rehash(document)
    assert any("mandatory pass" in error.lower() or "evidence" in error.lower() for error in validate(document))


def test_failed_assertion_cannot_be_downgraded_to_optional_to_create_pass():
    document = _passing_fixture()
    document["assertions"].append(
        {
            "assertion_id": "material-sensitive-read-failure",
            "mandatory": False,
            "state": "FAIL",
            "evidence_event_ids": ["event-sensitive-read"],
        }
    )
    document["verdict"] = "PASS"
    _rehash(document)
    assert any("failed assertion" in error.lower() or "verdict mismatch" in error for error in validate(document))


def test_pass_requires_effective_policy_attachment():
    document = _passing_fixture()
    document["policy_attachments"] = []
    _rehash(document)
    assert any("attachment" in error for error in validate(document))


def test_policy_history_digest_must_bind_the_actual_history():
    document = _passing_fixture()
    document["policy_history_digest"] = "sha256:" + "a" * 64
    _rehash(document)
    assert any("policy history digest" in error.lower() for error in validate(document))


def test_authority_digest_must_bind_the_authority_projection():
    document = _passing_fixture()
    document["authority_digest"] = "sha256:" + "b" * 64
    _rehash(document)
    assert any("authority digest" in error.lower() for error in validate(document))


def test_event_semantic_digest_must_bind_event_semantics():
    document = _passing_fixture()
    document["events"][0]["semantic_digest"] = "sha256:" + "c" * 64
    _rehash(document)
    assert any("semantic digest" in error.lower() for error in validate(document))


# SBX-RED-002: Supervisor Cycle 6 remaining second-layer false-PASS corpus.
# Each mutation fully re-binds current integrity fields, then expects semantic
# validation to reject the recorded PASS for the intended missing rule.


def test_red002_residual_descendants_must_reject_pass():
    document = _passing_fixture()
    document["post_conditions"]["descendants"] = "residual"
    errors = _accepted_pass_after_mutation(document)
    assert any("descendant" in error.lower() or "residual" in error.lower() for error in errors)


def test_red002_residual_filesystem_state_must_reject_pass():
    document = _passing_fixture()
    document["post_conditions"]["filesystem_residue"] = "residual"
    errors = _accepted_pass_after_mutation(document)
    assert any("filesystem" in error.lower() or "residual" in error.lower() for error in errors)


def test_red002_event_source_must_bind_to_declared_telemetry_source():
    document = _passing_fixture()
    document["events"][0]["source_id"] = "undeclared-collector"
    errors = _accepted_pass_after_mutation(document)
    assert any("source" in error.lower() or "collector" in error.lower() for error in errors)


def test_red002_duplicate_event_id_must_reject_pass():
    document = _passing_fixture()
    duplicate = copy.deepcopy(document["events"][0])
    duplicate["event_type"] = "network"
    document["events"].append(duplicate)
    errors = _accepted_pass_after_mutation(document)
    assert any("duplicate" in error.lower() and "event" in error.lower() for error in errors)


def test_red002_duplicate_assertion_id_must_reject_pass():
    document = _passing_fixture()
    document["assertions"].append(copy.deepcopy(document["assertions"][0]))
    errors = _accepted_pass_after_mutation(document)
    assert any("duplicate" in error.lower() and "assert" in error.lower() for error in errors)


def test_red002_duplicate_telemetry_source_id_must_reject_pass():
    document = _passing_fixture()
    document["telemetry"].append(copy.deepcopy(document["telemetry"][0]))
    errors = _accepted_pass_after_mutation(document)
    assert any("duplicate" in error.lower() and ("telemetry" in error.lower() or "source" in error.lower()) for error in errors)


def test_red002_unknown_top_level_field_must_execute_schema_and_reject_pass():
    document = _passing_fixture()
    document["schema_forbidden_extra"] = True
    errors = _accepted_pass_after_mutation(document)
    assert any("schema" in error.lower() or "additional" in error.lower() for error in errors)


def test_red002_invalid_event_type_must_execute_schema_and_reject_pass():
    document = _passing_fixture()
    document["events"][0]["event_type"] = "not-a-real-event-type"
    errors = _accepted_pass_after_mutation(document)
    assert any("schema" in error.lower() or "event_type" in error.lower() or "event type" in error.lower() for error in errors)


def test_red002_invalid_event_datetime_must_execute_format_validation():
    document = _passing_fixture()
    document["events"][0]["occurred_at_utc"] = "not-a-date-time"
    errors = _accepted_pass_after_mutation(document)
    assert any("date" in error.lower() or "time" in error.lower() or "schema" in error.lower() for error in errors)


def test_red002_event_monotonic_time_before_policy_effective_time_must_reject_pass():
    document = _passing_fixture()
    document["events"][0]["monotonic_ns"] = document["policy_history"][0]["effective_at_monotonic_ns"] - 1
    errors = _accepted_pass_after_mutation(document)
    assert any("monotonic" in error.lower() or "time" in error.lower() for error in errors)


def test_red002_event_wall_clock_before_policy_effective_time_must_reject_pass():
    document = _passing_fixture()
    document["events"][0]["occurred_at_utc"] = "2026-08-11T02:59:59Z"
    errors = _accepted_pass_after_mutation(document)
    assert any("occurred" in error.lower() or "effective" in error.lower() or "time" in error.lower() for error in errors)


def test_red002_event_authority_epoch_must_match_effective_policy_history():
    document = _passing_fixture()
    document["events"][0]["authority_epoch"] = 99
    errors = _accepted_pass_after_mutation(document)
    assert any("authority" in error.lower() and "epoch" in error.lower() for error in errors)


def test_red002_effective_attachment_policy_digest_must_match_policy_epoch():
    document = _passing_fixture()
    document["policy_attachments"][0]["policy_digest"] = "sha256:" + "9" * 64
    errors = _accepted_pass_after_mutation(document)
    assert any("attachment" in error.lower() and "policy" in error.lower() for error in errors)


def test_red002_attachment_evidence_digest_must_bind_real_evidence_object():
    document = _passing_fixture()
    document["policy_attachments"][0]["evidence_digest"] = "sha256:" + "8" * 64
    errors = _accepted_pass_after_mutation(document)
    assert any("attachment" in error.lower() and "evidence" in error.lower() for error in errors)


def test_red002_healthy_mandatory_collector_without_claim_event_must_reject_pass():
    document = _passing_fixture()
    document["telemetry"][0]["source_id"] = "healthy-but-unrelated-collector"
    errors = _accepted_pass_after_mutation(document)
    assert any("collector" in error.lower() or "source" in error.lower() or "claim" in error.lower() for error in errors)


def test_red002_duplicate_policy_epoch_must_reject_pass():
    document = _passing_fixture()
    duplicate = copy.deepcopy(document["policy_history"][0])
    duplicate["policy_digest"] = "sha256:" + "7" * 64
    document["policy_history"].append(duplicate)
    errors = _accepted_pass_after_mutation(document)
    assert any("duplicate" in error.lower() and "epoch" in error.lower() for error in errors)


def test_red002_later_policy_epoch_monotonic_regression_must_reject_pass():
    document = _passing_fixture()
    document["policy_history"].append(
        {
            "policy_epoch": 1,
            "policy_digest": "sha256:" + "6" * 64,
            "authority_epoch": 0,
            "effective_at_utc": "2026-08-11T03:00:02Z",
            "effective_at_monotonic_ns": 999,
            "source_principal_id": "supervisor-fixture",
            "delta_class": "no-op",
        }
    )
    errors = _accepted_pass_after_mutation(document)
    assert any("monotonic" in error.lower() or "order" in error.lower() or "epoch" in error.lower() for error in errors)
