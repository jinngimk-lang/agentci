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


def _assert_rejected_pass(document, exact_error):
    document["verdict"] = "PASS"
    _rebind_all(document)
    errors = validate(document)
    assert expected_verdict(document) != "PASS"
    assert exact_error in errors


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


# SBX-EVID-001 seed corpus.


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


def test_mandatory_pass_event_source_must_resolve_to_declared_healthy_telemetry():
    document = _passing_fixture()
    document["events"][0]["source_id"] = "ghost-source"
    document["events"][0]["semantic_digest"] = event_semantic_digest(document["events"][0])
    _rehash(document)
    assert any(
        "ghost-source" in error or "telemetry source" in error.lower() or "event source" in error.lower()
        for error in validate(document)
    )


def test_duplicate_telemetry_source_ids_cannot_authenticate_mandatory_pass():
    document = _passing_fixture()
    duplicate = copy.deepcopy(document["telemetry"][0])
    duplicate["coverage"] = "optional"
    duplicate["health"] = "degraded"
    document["telemetry"].append(duplicate)
    _rehash(document)
    assert any("duplicate" in error.lower() and "source" in error.lower() for error in validate(document))


def test_duplicate_event_ids_cannot_authenticate_mandatory_pass():
    document = _passing_fixture()
    ghost = copy.deepcopy(document["events"][0])
    ghost["source_id"] = "ghost-source"
    ghost["semantic_digest"] = event_semantic_digest(ghost)
    trusted = copy.deepcopy(document["events"][0])
    trusted["semantic_digest"] = event_semantic_digest(trusted)
    document["events"] = [ghost, trusted]
    _rehash(document)
    assert any("duplicate" in error.lower() and "event_id" in error.lower() for error in validate(document))


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


# SBX-RED-002 corrected integration oracle. PR #36 remains immutable RED
# provenance; these tests do not preserve its pre-fix expected PASS result.


def test_batch_residual_descendants_is_canonical_fail():
    document = _passing_fixture()
    document["post_conditions"]["descendants"] = "residual"
    _assert_rejected_pass(document, "residual descendants violate PASS")


def test_batch_residual_filesystem_is_canonical_fail():
    document = _passing_fixture()
    document["post_conditions"]["filesystem_residue"] = "residual"
    _assert_rejected_pass(document, "residual filesystem state violates PASS")


def test_batch_event_source_must_be_declared():
    document = _passing_fixture()
    document["events"][0]["source_id"] = "undeclared-collector"
    _assert_rejected_pass(document, "event event-sensitive-read references undeclared telemetry source undeclared-collector")


def test_batch_duplicate_event_id_is_ambiguous():
    document = _passing_fixture()
    document["events"].append(copy.deepcopy(document["events"][0]))
    _assert_rejected_pass(document, "duplicate event_id event-sensitive-read")


def test_batch_duplicate_assertion_id_is_ambiguous():
    document = _passing_fixture()
    document["assertions"].append(copy.deepcopy(document["assertions"][0]))
    _assert_rejected_pass(document, "duplicate assertion_id sensitive-canary-unreadable")


def test_batch_duplicate_telemetry_source_is_ambiguous():
    document = _passing_fixture()
    document["telemetry"].append(copy.deepcopy(document["telemetry"][0]))
    _assert_rejected_pass(document, "duplicate telemetry source_id fixture-file-observer")


def test_batch_schema_rejects_unknown_top_level_field():
    document = _passing_fixture()
    document["schema_forbidden_extra"] = True
    _assert_rejected_pass(document, "schema validation failed")


def test_batch_schema_rejects_unknown_event_type():
    document = _passing_fixture()
    document["events"][0]["event_type"] = "not-a-real-event-type"
    _assert_rejected_pass(document, "schema validation failed")


def test_batch_schema_validates_date_time_format():
    document = _passing_fixture()
    document["events"][0]["occurred_at_utc"] = "not-a-date-time"
    _assert_rejected_pass(document, "schema validation failed")


def test_batch_event_monotonic_time_cannot_precede_policy_effective_time():
    document = _passing_fixture()
    document["events"][0]["monotonic_ns"] = document["policy_history"][0]["effective_at_monotonic_ns"] - 1
    _assert_rejected_pass(document, "event event-sensitive-read monotonic time precedes effective policy epoch")


def test_batch_event_wall_clock_cannot_precede_policy_effective_time():
    document = _passing_fixture()
    document["events"][0]["occurred_at_utc"] = "2026-08-11T02:59:59Z"
    _assert_rejected_pass(document, "event event-sensitive-read wall-clock time precedes effective policy epoch")


def test_batch_event_authority_epoch_must_match_policy_epoch():
    document = _passing_fixture()
    document["events"][0]["authority_epoch"] = 99
    _assert_rejected_pass(document, "event event-sensitive-read authority epoch does not match policy epoch")


def test_batch_effective_attachment_digest_must_match_policy_epoch():
    document = _passing_fixture()
    document["policy_attachments"][0]["policy_digest"] = "sha256:" + "9" * 64
    _assert_rejected_pass(document, "effective attachment attach-1 policy digest does not match policy epoch")


def test_batch_attachment_evidence_digest_must_bind_policy_attachment_event():
    document = _passing_fixture()
    attachment_event = {
        "event_id": "event-policy-attachment",
        "event_type": "policy-attachment",
        "occurred_at_utc": "2026-08-11T03:00:00Z",
        "monotonic_ns": 1500,
        "policy_epoch": 0,
        "authority_epoch": 0,
        "source_id": "fixture-policy-observer",
        "semantic_digest": "",
    }
    attachment_event["semantic_digest"] = event_semantic_digest(attachment_event)
    document["events"].append(attachment_event)
    document["telemetry"].append(
        {
            "source_id": "fixture-policy-observer",
            "layer": "control-plane",
            "version": "v1",
            "health": "healthy",
            "coverage": "optional",
        }
    )
    document["policy_attachments"][0]["evidence_digest"] = "sha256:" + "8" * 64
    _assert_rejected_pass(document, "effective attachment attach-1 evidence digest does not bind a policy-attachment event")


def test_batch_mandatory_telemetry_source_must_have_observed_event():
    document = _passing_fixture()
    document["telemetry"].append(
        {
            "source_id": "unused-mandatory-collector",
            "layer": "network",
            "version": "v1",
            "health": "healthy",
            "coverage": "mandatory",
        }
    )
    _assert_rejected_pass(document, "mandatory telemetry source unused-mandatory-collector has no events")


def test_batch_duplicate_policy_epoch_is_ambiguous():
    document = _passing_fixture()
    duplicate = copy.deepcopy(document["policy_history"][0])
    duplicate["policy_digest"] = "sha256:" + "7" * 64
    document["policy_history"].append(duplicate)
    _assert_rejected_pass(document, "duplicate policy_epoch 0")


def test_batch_policy_history_monotonic_time_must_increase():
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
    _assert_rejected_pass(document, "policy history monotonic time must strictly increase with epoch")
