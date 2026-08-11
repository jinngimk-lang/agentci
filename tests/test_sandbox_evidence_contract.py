import copy
import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, expected_verdict, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
SCHEMA = ROOT / "schemas" / "sandbox-certification-v0alpha1.schema.json"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _rehash(document):
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
