from __future__ import annotations

import copy
from datetime import datetime
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import validate_sandbox_evidence as evidence_validator
from tests.test_sandbox_receipt_contract_red import (
    PASS_EVIDENCE,
    _assemble,
    _complete_bundle,
    _digest,
    _inventory_item,
    _manifest_digest,
    _replay,
    _resign,
    _success,
)


def _sidecar_event_bundle():
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    cleanup_events = [event for event in document["events"] if event["event_type"] == "cleanup"]
    document["events"] = [event for event in document["events"] if event["event_type"] != "cleanup"]
    document["authority_digest"] = evidence_validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = evidence_validator.artifact_digest(document)

    for observer in bundle["observer_attestations"]:
        source_id = observer["telemetry_source"]["source_id"]
        events = [event for event in document["events"] if event["source_id"] == source_id]
        ordered_by_utc = sorted(
            events,
            key=lambda event: datetime.fromisoformat(event["occurred_at_utc"].replace("Z", "+00:00")),
        )
        observer["event_bindings"] = sorted(
            (
                {"event_id": event["event_id"], "semantic_digest": event["semantic_digest"]}
                for event in events
            ),
            key=lambda item: item["event_id"],
        )
        observer["event_set_digest"] = _digest(observer["event_bindings"])
        observer["observation_window"] = {
            "opened_at_utc": ordered_by_utc[0]["occurred_at_utc"],
            "opened_at_monotonic_ns": min(event["monotonic_ns"] for event in events),
            "closed_at_utc": ordered_by_utc[-1]["occurred_at_utc"],
            "closed_at_monotonic_ns": max(event["monotonic_ns"] for event in events),
        }
        observer.update(_resign(observer, bundle["_observer_private"]))
    bundle["cleanup_attestation"]["cleanup_events"] = cleanup_events
    bundle["cleanup_attestation"]["observation_window"] = {
        "opened_at_utc": min(event["occurred_at_utc"] for event in cleanup_events),
        "opened_at_monotonic_ns": min(event["monotonic_ns"] for event in cleanup_events),
        "closed_at_utc": max(event["occurred_at_utc"] for event in cleanup_events),
        "closed_at_monotonic_ns": max(event["monotonic_ns"] for event in cleanup_events),
    }
    bundle["cleanup_attestation"] = _resign(
        bundle["cleanup_attestation"], bundle["_cleanup_private"]
    )
    assert _assemble(document, bundle).receipt_valid is True
    return document, bundle


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("unsigned", "E_RECEIPT_UNTRUSTED_ATTESTER"),
        ("omitted", "E_RECEIPT_CLEANUP_UNKNOWN_EVENT"),
        ("wrong_source", "E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH"),
        ("collision", "E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH"),
    ],
)
def test_signed_cleanup_event_set_is_complete_semantic_and_collision_free(mutation: str, code: str):
    document, bundle = _sidecar_event_bundle()
    cleanup = bundle["cleanup_attestation"]
    if mutation == "unsigned":
        event = cleanup["cleanup_events"][0]
        event["occurred_at_utc"] = "2026-08-11T03:00:02.500000Z"
        event["semantic_digest"] = evidence_validator.event_semantic_digest(event)
    elif mutation == "omitted":
        cleanup["cleanup_events"].pop()
        bundle["cleanup_attestation"] = _resign(cleanup, bundle["_cleanup_private"])
    elif mutation == "wrong_source":
        event = cleanup["cleanup_events"][0]
        event["source_id"] = "attacker-source"
        event["semantic_digest"] = evidence_validator.event_semantic_digest(event)
        bundle["cleanup_attestation"] = _resign(cleanup, bundle["_cleanup_private"])
    else:
        event = cleanup["cleanup_events"][0]
        old_id = event["event_id"]
        event["event_id"] = document["events"][0]["event_id"]
        for result in cleanup["requirement_results"]:
            result["event_ids"] = [event["event_id"] if item == old_id else item for item in result["event_ids"]]
            result["result_set_digest"] = _digest(result["event_ids"])
        bundle["cleanup_attestation"] = _resign(cleanup, bundle["_cleanup_private"])

    result = _assemble(document, bundle)
    assert result.receipt_valid is False
    assert result.error_codes == (code,)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("utc_reversed", "E_RECEIPT_CLEANUP_WINDOW_REVERSED"),
        ("utc_coverage", "E_RECEIPT_CLEANUP_WINDOW_COVERAGE_GAP"),
    ],
)
def test_cleanup_observation_window_is_closed_ordered_and_covers_signed_events(mutation: str, code: str):
    document, bundle = _sidecar_event_bundle()
    cleanup = bundle["cleanup_attestation"]
    if mutation == "utc_reversed":
        cleanup["observation_window"]["closed_at_utc"] = "2026-08-11T02:59:59Z"
    else:
        cleanup["observation_window"]["opened_at_utc"] = "2026-08-11T03:00:03Z"
    bundle["cleanup_attestation"] = _resign(cleanup, bundle["_cleanup_private"])

    result = _assemble(document, bundle)
    assert result.receipt_valid is False
    assert result.error_codes == (code,)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("utc_reversed", "E_RECEIPT_OBSERVER_WINDOW_REVERSED"),
        ("utc_coverage", "E_RECEIPT_OBSERVER_WINDOW_COVERAGE_GAP"),
    ],
)
def test_observer_window_checks_utc_order_and_coverage(mutation: str, code: str):
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    observer = bundle["observer_attestations"][1]
    if mutation == "utc_reversed":
        observer["observation_window"]["closed_at_utc"] = "2026-08-11T02:59:59Z"
    else:
        observer["observation_window"]["opened_at_utc"] = "2026-08-11T03:00:00.250000Z"
    bundle["observer_attestations"][1] = _resign(observer, bundle["_observer_private"])

    result = _assemble(document, bundle)
    assert result.receipt_valid is False
    assert result.error_codes == (code,)


def test_replay_rejects_joint_embedded_schema_testcase_inventory_and_manifest_rewrite():
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = copy.deepcopy(_success(document, bundle).manifest)
    for role, field in (("schema", "description"), ("test_case", "claim")):
        artifact = next(item for item in manifest["artifacts"] if item["role"] == role)
        artifact["content"][field] = "attacker-weakened"
        replacement = _inventory_item(role, artifact["content"])
        artifact.update(replacement)
        inventory = next(item for item in manifest["artifact_inventory"] if item["role"] == role)
        inventory.update(replacement)
    manifest["manifest_digest"] = _manifest_digest(manifest)

    replay = _replay(manifest, bundle)
    assert replay.valid is False
    assert replay.error_codes == ("E_RECEIPT_MANIFEST_INVALID",)


def test_replay_rejects_observer_roles_beyond_embedded_mandatory_telemetry():
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = copy.deepcopy(_success(document, bundle).manifest)
    extra = copy.deepcopy(next(item for item in manifest["artifacts"] if item["role"].startswith("observer:")))
    extra["role"] = "observer:attacker-extra"
    manifest["artifacts"].append(extra)
    manifest["artifact_inventory"].append({key: value for key, value in extra.items() if key != "content"})
    manifest["manifest_digest"] = _manifest_digest(manifest)

    replay = _replay(manifest, bundle)
    assert replay.valid is False
    assert replay.error_codes == ("E_RECEIPT_OBSERVER_SOURCE_PROJECTION_MISMATCH",)


def test_replay_rejects_unexpected_non_observer_artifact_role():
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = copy.deepcopy(_success(document, bundle).manifest)
    extra = copy.deepcopy(manifest["artifacts"][0])
    extra["role"] = "attacker-extension"
    manifest["artifacts"].append(extra)
    manifest["artifact_inventory"].append({key: value for key, value in extra.items() if key != "content"})
    manifest["manifest_digest"] = _manifest_digest(manifest)

    replay = _replay(manifest, bundle)
    assert replay.valid is False
    assert replay.error_codes == ("E_RECEIPT_ARTIFACT_ROLE_UNEXPECTED",)


def test_public_receipt_objects_have_strict_machine_schema():
    root = Path(__file__).resolve().parents[1]
    schema_path = root / "schemas" / "sandbox-receipt-v0alpha1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = _success(document, bundle).manifest
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    objects = [*bundle["observer_attestations"], bundle["cleanup_attestation"], manifest]
    for value in objects:
        assert list(validator.iter_errors(value)) == []
        attacked = copy.deepcopy(value)
        attacked["unexpected_contract_field"] = True
        assert list(validator.iter_errors(attacked)), value["kind"]
