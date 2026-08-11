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
