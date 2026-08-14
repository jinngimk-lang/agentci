#!/usr/bin/env python3
"""S0 semantic validator for AgentCI sandbox EvidenceEnvelope.

Design-stage only: this is not a released sandbox certification engine and
never upgrades observation into authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import FormatError

try:
    from scripts.execution_attestation import execution_attestation_valid
    from scripts.lifecycle_attestation import lifecycle_attestation_valid
    from scripts.runtime_environment_attestation import runtime_environment_attestation_valid
except ModuleNotFoundError:  # direct script execution from repository root
    from execution_attestation import execution_attestation_valid
    from lifecycle_attestation import lifecycle_attestation_valid
    from runtime_environment_attestation import runtime_environment_attestation_valid

CANONICALIZATION = "agentci-json-c14n-v0alpha1"
VERDICT_RULE = "agentci-sandbox-atomic-v0alpha1"
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "sandbox-certification-v0alpha1.schema.json"
TEST_CASE_DIR = ROOT / "examples" / "sandbox" / "testcases"
EVENT_SOURCE_LAYERS = {
    "process": {"process"},
    "file": {"filesystem"},
    "network": {"network"},
    "credential": {"credential"},
    "control-plane": {"control-plane"},
    "policy-delta": {"control-plane"},
    "policy-attachment": {"control-plane"},
    "lifecycle": {"lifecycle"},
    "cleanup": {"process", "filesystem", "network", "lifecycle", "control-plane"},
}
PROBE_EVENT_TYPES = {
    "filesystem": {"file"},
    "network": {"network"},
    "credential": {"credential"},
    "process": {"process"},
    "lifecycle": {"lifecycle"},
    "control-plane": {"control-plane"},
}


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_evidence_json(raw: str) -> dict[str, Any]:
    document = json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    if not isinstance(document, dict):
        raise ValueError("evidence root must be a JSON object")
    return document


def canonical_value_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_value_bytes(value)).hexdigest()


def canonical_bytes(document: dict[str, Any]) -> bytes:
    candidate = copy.deepcopy(document)
    if isinstance(candidate.get("canonicalization"), dict):
        candidate["canonicalization"].pop("artifact_digest", None)
    case_id = candidate.get("case_id")
    # Typed cleanup requirements were added to the canonical TestCase without
    # changing the legacy EvidenceEnvelope digest contract. Evidence events,
    # including legal cleanup events, remain part of the envelope digest.
    test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    digest_case = copy.deepcopy(test_case) if test_case is not None else None
    if digest_case is not None:
        digest_case.pop("cleanup_requirements", None)
    return canonical_value_bytes(
        {"evidence": candidate, "test_case_digest": digest_value(digest_case) if digest_case is not None else None}
    )


def artifact_digest(document: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def policy_history_digest(document: dict[str, Any]) -> str:
    return digest_value(document.get("policy_history", []))


def authority_binding_projection(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_history": [
            {
                "policy_epoch": x.get("policy_epoch"),
                "authority_epoch": x.get("authority_epoch"),
                "source_principal_id": x.get("source_principal_id"),
            }
            for x in document.get("policy_history", [])
        ],
        "policy_attachments": [
            {
                "attachment_id": x.get("attachment_id"),
                "workload_identity": x.get("workload_identity"),
                "policy_epoch": x.get("policy_epoch"),
                "policy_digest": x.get("policy_digest"),
                "state": x.get("state"),
            }
            for x in document.get("policy_attachments", [])
        ],
        "events": [
            {
                "event_id": x.get("event_id"),
                "authority_epoch": x.get("authority_epoch"),
                "decision_id": x.get("decision_id"),
                "receipt_id": x.get("receipt_id"),
                "workload_identity": x.get("workload_identity"),
                "attachment_id": x.get("attachment_id"),
            }
            for x in document.get("events", [])
            if isinstance(x, dict)
        ],
    }


def authority_binding_digest(document: dict[str, Any]) -> str:
    return digest_value(authority_binding_projection(document))


def event_semantic_digest(event: dict[str, Any]) -> str:
    candidate = copy.deepcopy(event)
    candidate.pop("semantic_digest", None)
    return digest_value(candidate)


def execution_binding_id(document: dict[str, Any], test_case: dict[str, Any], event: dict[str, Any]) -> str:
    """Deterministic identity for one canonical probe execution context."""
    return digest_value(
        {
            "run_id": document.get("run_id"),
            "case_id": document.get("case_id"),
            "attempt": document.get("attempt"),
            "probe": test_case.get("probe"),
            "workload_identity": event.get("workload_identity"),
            "policy_epoch": event.get("policy_epoch"),
            "authority_epoch": event.get("authority_epoch"),
        }
    )


@lru_cache(maxsize=1)
def _schema_validator() -> Draft202012Validator:
    schema = load_evidence_json(SCHEMA_PATH.read_text())
    envelope = {
        "$schema": schema["$schema"],
        "$id": schema.get("$id", "") + "#EvidenceEnvelopeValidation",
        "$defs": schema["$defs"],
        "$ref": "#/$defs/EvidenceEnvelope",
    }
    return Draft202012Validator(envelope, format_checker=FormatChecker())


@lru_cache(maxsize=1)
def _test_case_validator() -> Draft202012Validator:
    schema = load_evidence_json(SCHEMA_PATH.read_text())
    test_case = {
        "$schema": schema["$schema"],
        "$id": schema.get("$id", "") + "#TestCaseValidation",
        "$defs": schema["$defs"],
        "$ref": "#/$defs/TestCase",
    }
    return Draft202012Validator(test_case, format_checker=FormatChecker())


def _requirement_map(test_case: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    requirements = test_case.get("assertion_requirements", [])
    ids = [item.get("assertion_id") for item in requirements if isinstance(item, dict)]
    if len(ids) != len(requirements) or len(set(ids)) != len(ids):
        return None
    mandatory_ids = set(test_case.get("mandatory_assertions", []))
    if set(ids) != mandatory_ids:
        return None
    by_id = {item["assertion_id"]: item for item in requirements}
    utility_ids = set(test_case.get("authorized_utility", []))
    for utility_id in utility_ids:
        requirement = by_id.get(utility_id)
        if requirement is None or requirement.get("event_type") != "utility":
            return None
        if not requirement.get("action") or not requirement.get("resource") or not requirement.get("expected_result"):
            return None
    capability_domain = test_case.get("capability_domain")
    expected_types = PROBE_EVENT_TYPES.get(capability_domain)
    if expected_types:
        probe_candidates = [
            requirement
            for assertion_id, requirement in by_id.items()
            if assertion_id not in utility_ids and requirement.get("event_type") in expected_types
        ]
        if len(probe_candidates) != 1:
            return None
        if not probe_candidates[0].get("expected_result"):
            return None
        probe_channel = test_case.get("probe", {}).get("network_channel")
        if capability_domain == "network":
            if not probe_channel or probe_candidates[0].get("network_channel") != probe_channel:
                return None
    return by_id


@lru_cache(maxsize=64)
def _load_test_case(case_id: str) -> dict[str, Any] | None:
    if not isinstance(case_id, str) or not case_id or "/" in case_id or "\\" in case_id or case_id in {".", ".."}:
        return None
    path = TEST_CASE_DIR / f"{case_id}.json"
    if not path.is_file():
        return None
    try:
        test_case = load_evidence_json(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    if list(_test_case_validator().iter_errors(test_case)):
        return None
    if test_case.get("kind") != "TestCase" or test_case.get("case_id") != case_id:
        return None
    utility_ids = test_case.get("authorized_utility", [])
    mandatory_ids = set(test_case.get("mandatory_assertions", []))
    if len(set(utility_ids)) != len(utility_ids) or any(x not in mandatory_ids for x in utility_ids):
        return None
    if _requirement_map(test_case) is None:
        return None
    return test_case


def _source_suitable_for_event(test_case: dict[str, Any], source: dict[str, Any], event_type: Any) -> bool:
    source_id = source.get("source_id")
    if source_id not in set(test_case.get("mandatory_telemetry_sources", [])):
        return False
    required_layers = EVENT_SOURCE_LAYERS.get(event_type)
    return required_layers is None or source.get("layer") in required_layers


def _event_matches_requirement(event: dict[str, Any], requirement: dict[str, Any]) -> bool:
    if event.get("event_type") != requirement.get("event_type"):
        return False
    checks = {
        "channel": requirement.get("network_channel"),
        "action": requirement.get("action"),
        "resource": requirement.get("resource"),
        "observed_result": requirement.get("expected_result"),
    }
    return all(expected is None or event.get(field) == expected for field, expected in checks.items())


def _source_suitable_for_requirement(test_case: dict[str, Any], source: dict[str, Any], requirement: dict[str, Any]) -> bool:
    if source.get("source_id") not in set(test_case.get("mandatory_telemetry_sources", [])):
        return False
    event_type = requirement.get("event_type")
    if event_type == "utility":
        return source.get("layer") in {"workspace", "filesystem", "process", test_case.get("capability_domain")}
    required_layers = EVENT_SOURCE_LAYERS.get(event_type)
    return required_layers is None or source.get("layer") in required_layers


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_fields_valid(document: dict[str, Any]) -> bool:
    checker = FormatChecker()
    values = [
        x.get("effective_at_utc")
        for x in document.get("policy_history", [])
        if isinstance(x, dict)
    ] + [
        x.get("occurred_at_utc") for x in document.get("events", []) if isinstance(x, dict)
    ]
    for value in values:
        try:
            checker.check(value, "date-time")
        except FormatError:
            return False
    return True


def _duplicates(values: list[Any]) -> set[Any]:
    return {v for v in values if v is not None and values.count(v) > 1}


def _residual_errors(document: dict[str, Any]) -> list[str]:
    post, errors = document.get("post_conditions", {}), []
    if post.get("descendants") == "residual":
        errors.append("residual descendants violate PASS")
    if post.get("filesystem_residue") == "residual":
        errors.append("residual filesystem state violates PASS")
    if post.get("sockets") == "residual":
        errors.append("residual sockets violate PASS")
    if post.get("network_activity") == "residual":
        errors.append("residual network activity violates PASS")
    if post.get("credential_state") == "residual":
        errors.append("residual credential state violates PASS")
    return errors


def _authority_expansion_errors(document: dict[str, Any]) -> list[str]:
    gated = {"expansion", "lateral", "unknown"}
    errors = []
    for policy in document.get("policy_history", []):
        delta_class = policy.get("delta_class")
        if delta_class in gated:
            errors.append(
                f"privilege {delta_class} requires external authenticated authority evidence; "
                "EvidenceEnvelope source/decision/receipt references alone are insufficient"
            )
    return errors


def _event_not_after(provenance: dict[str, Any], event: dict[str, Any]) -> bool:
    pmono, emono = provenance.get("monotonic_ns"), event.get("monotonic_ns")
    ptime, etime = _parse_datetime(provenance.get("occurred_at_utc")), _parse_datetime(event.get("occurred_at_utc"))
    return (
        isinstance(pmono, int)
        and isinstance(emono, int)
        and pmono <= emono
        and ptime is not None
        and etime is not None
        and ptime <= etime
    )


def _execution_binding_errors(
    document: dict[str, Any],
    test_case: dict[str, Any] | None,
    telemetry_by_source: dict[str, dict[str, Any]],
    events_by_id: dict[str, dict[str, Any]],
    duplicate_events: set[Any],
    assertion: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if test_case is None or not assertion.get("mandatory") or assertion.get("state") not in {"PASS", "FAIL"}:
        return errors
    canonical_sources = set(test_case.get("mandatory_telemetry_sources", []))
    for event_id in assertion.get("evidence_event_ids", []):
        if event_id in duplicate_events or event_id not in events_by_id:
            continue
        event = events_by_id[event_id]
        binding_id = execution_binding_id(document, test_case, event)
        if not isinstance(event_id, str) or not event_id.startswith(binding_id + ":"):
            errors.append(
                f"assertion {assertion.get('assertion_id')} evidence event {event_id} is not bound to exact canonical probe execution"
            )
            continue
        execution_event = events_by_id.get(binding_id)
        if execution_event is None or binding_id in duplicate_events:
            errors.append(f"assertion {assertion.get('assertion_id')} requires exactly one execution provenance event {binding_id}")
            continue
        source = telemetry_by_source.get(execution_event.get("source_id"))
        if execution_event.get("event_type") != "process":
            errors.append(f"execution provenance event {binding_id} must be a process observation")
        elif (
            source is None
            or source.get("source_id") not in canonical_sources
            or source.get("coverage") != "mandatory"
            or source.get("health") != "healthy"
        ):
            errors.append(f"execution provenance event {binding_id} requires a healthy canonical mandatory observer")
        elif not execution_attestation_valid(document, binding_id, execution_event.get("source_id")):
            errors.append(f"execution provenance event {binding_id} lacks valid external execution attestation")
        elif (
            execution_event.get("workload_identity") != event.get("workload_identity")
            or execution_event.get("policy_epoch") != event.get("policy_epoch")
            or execution_event.get("authority_epoch") != event.get("authority_epoch")
        ):
            errors.append(f"execution provenance event {binding_id} does not match assertion evidence execution context")
        elif not _event_not_after(execution_event, event):
            errors.append(f"execution provenance event {binding_id} must occur at or before assertion evidence")
    return errors


def _lifecycle_errors(
    document: dict[str, Any],
    telemetry_by_source: dict[str, dict[str, Any]],
    events_by_id: dict[str, dict[str, Any]],
    duplicate_events: set[Any],
    attachments: list[dict[str, Any]],
    duplicate_attachments: set[Any],
) -> list[str]:
    post = document.get("post_conditions", {})
    state = post.get("lifecycle_state")
    if state == "preserved":
        return ["preserved lifecycle state is not fresh/revalidated evidence"]
    if state != "revalidated":
        return []

    errors: list[str] = []
    continuity = document.get("lifecycle_continuity", [])
    if not continuity:
        return ["revalidated lifecycle state requires observed lifecycle continuity"]

    safe_states = {"revalidated", "revoked", "replaced"}
    for item in continuity:
        snapshot_id = item.get("snapshot_id")
        capture_epoch = item.get("capture_epoch")
        restore_epoch = item.get("restore_epoch")
        if not isinstance(capture_epoch, int) or not isinstance(restore_epoch, int) or restore_epoch <= capture_epoch:
            errors.append(f"lifecycle continuity {snapshot_id} requires advancing restore epoch")
        for field in ("process_state", "socket_fd_state", "credential_session_state", "policy_attachment_state"):
            if item.get(field) not in safe_states:
                errors.append(f"lifecycle continuity {snapshot_id} has unsafe or unverified {field}")

        evidence_ids = item.get("evidence_event_ids", [])
        if len(evidence_ids) != 1:
            errors.append(f"lifecycle continuity {snapshot_id} requires exactly one observed lifecycle event")
            continue
        event_id = evidence_ids[0]
        if event_id in duplicate_events or event_id not in events_by_id:
            errors.append(f"lifecycle continuity {snapshot_id} evidence event does not resolve uniquely")
            continue
        event = events_by_id[event_id]
        source = telemetry_by_source.get(event.get("source_id"))
        if event.get("event_type") != "lifecycle":
            errors.append(f"lifecycle continuity {snapshot_id} must bind a lifecycle event")
        if event.get("snapshot_id") != snapshot_id:
            errors.append(f"lifecycle continuity {snapshot_id} does not bind exact snapshot identity")
        if event.get("restore_epoch") != restore_epoch:
            errors.append(f"lifecycle continuity {snapshot_id} restore epoch does not match observed event")
        if source is None or source.get("coverage") != "mandatory" or source.get("health") != "healthy" or source.get("layer") != "lifecycle":
            errors.append(f"lifecycle continuity {snapshot_id} requires healthy mandatory lifecycle telemetry")
        epoch, workload, attachment_id = event.get("policy_epoch"), event.get("workload_identity"), event.get("attachment_id")
        matching = [
            attachment
            for attachment in attachments
            if attachment.get("state") == "effective"
            and attachment.get("policy_epoch") == epoch
            and attachment.get("workload_identity") == workload
            and attachment.get("attachment_id") == attachment_id
            and attachment.get("attachment_id") not in duplicate_attachments
        ]
        if not workload or not attachment_id or len(matching) != 1:
            errors.append(f"lifecycle continuity {snapshot_id} requires one effective attachment for observed restore context")
        if not lifecycle_attestation_valid(document, item, event):
            errors.append(f"lifecycle continuity {snapshot_id} lacks valid external snapshot/restore attestation")
    return errors


def _evidence_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if list(_schema_validator().iter_errors(document)) or not _format_fields_valid(document):
        # Semantic validation assumes the strict object shapes guaranteed by
        # the schema. Fail closed before projection arithmetic can dereference
        # a malformed list member; digesting remains independently available.
        return ["schema validation failed"]
    if document.get("apiVersion") != "agentci.dev/sandbox/v0alpha1":
        errors.append("unexpected apiVersion")
    if document.get("kind") != "EvidenceEnvelope":
        errors.append("validator only accepts EvidenceEnvelope")
    if document.get("verdict_rule_version") != VERDICT_RULE:
        errors.append("unexpected verdict rule version")
    canonicalization = document.get("canonicalization", {})
    if canonicalization.get("algorithm") != CANONICALIZATION:
        errors.append("unexpected canonicalization algorithm")
    if canonicalization.get("artifact_digest") != artifact_digest(document):
        errors.append("artifact digest mismatch")
    if document.get("policy_history_digest") != policy_history_digest(document):
        errors.append("policy history digest mismatch")
    if document.get("authority_digest") != authority_binding_digest(document):
        errors.append("authority digest mismatch")
    errors.extend(_authority_expansion_errors(document))
    if not runtime_environment_attestation_valid(document):
        errors.append("runtime/environment provenance is not independently bound to this execution")

    case_id = document.get("case_id")
    test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    requirements = _requirement_map(test_case) if test_case is not None else None
    if test_case is None or requirements is None:
        errors.append(f"case_id {case_id} does not resolve to one canonical typed TestCase")

    history = document.get("policy_history", [])
    epochs = [x.get("policy_epoch") for x in history]
    duplicate_epochs = _duplicates(epochs)
    if not epochs or any(x is None for x in epochs):
        errors.append("policy history must contain concrete epochs")
    for epoch in sorted(duplicate_epochs):
        errors.append(f"duplicate policy_epoch {epoch}")
    previous_epoch = previous_monotonic = None
    for item in history:
        epoch, monotonic = item.get("policy_epoch"), item.get("effective_at_monotonic_ns")
        if isinstance(epoch, int) and isinstance(previous_epoch, int) and epoch < previous_epoch:
            errors.append("policy history epochs must strictly increase in document order")
        if isinstance(monotonic, int) and isinstance(previous_monotonic, int) and monotonic <= previous_monotonic:
            errors.append("policy history monotonic time must strictly increase with epoch")
        if isinstance(epoch, int):
            previous_epoch = epoch
        if isinstance(monotonic, int):
            previous_monotonic = monotonic
    history_by_epoch = {
        x.get("policy_epoch"): x
        for x in history
        if isinstance(x.get("policy_epoch"), int) and x.get("policy_epoch") not in duplicate_epochs
    }

    telemetry = document.get("telemetry", [])
    source_ids = [x.get("source_id") for x in telemetry]
    duplicate_sources = _duplicates(source_ids)
    for source_id in sorted(duplicate_sources):
        errors.append(f"duplicate telemetry source_id {source_id}")
    telemetry_by_source = {
        x.get("source_id"): x
        for x in telemetry
        if x.get("source_id") is not None and x.get("source_id") not in duplicate_sources
    }
    if test_case is not None:
        for source_id in test_case.get("mandatory_telemetry_sources", []):
            if source_id in duplicate_sources:
                errors.append(f"canonical mandatory telemetry source {source_id} does not resolve uniquely")
                continue
            source = telemetry_by_source.get(source_id)
            if source is None:
                errors.append(f"canonical mandatory telemetry source {source_id} is missing from EvidenceEnvelope")
            elif source.get("coverage") != "mandatory" or source.get("health") != "healthy":
                errors.append(f"canonical mandatory telemetry source {source_id} requires mandatory coverage and healthy status")

    events = document.get("events", [])
    event_values = [x.get("event_id") for x in events]
    duplicate_events = _duplicates(event_values)
    for event_id in sorted(duplicate_events):
        errors.append(f"duplicate event_id {event_id}")
    event_ids = {x for x in event_values if x is not None}
    events_by_id = {
        x.get("event_id"): x
        for x in events
        if x.get("event_id") is not None and x.get("event_id") not in duplicate_events
    }
    event_sources = {x.get("source_id") for x in events}
    for source in telemetry:
        if source.get("coverage") == "mandatory" and source.get("source_id") not in event_sources:
            errors.append(f"mandatory telemetry source {source.get('source_id')} has no events")
    for event in events:
        event_id, source_id = event.get("event_id"), event.get("source_id")
        if source_id not in telemetry_by_source and source_id not in duplicate_sources:
            errors.append(f"event {event_id} references undeclared telemetry source {source_id}")
        policy = history_by_epoch.get(event.get("policy_epoch"))
        if policy is None:
            errors.append(f"event {event_id} references unknown policy epoch")
        else:
            if event.get("authority_epoch") != policy.get("authority_epoch"):
                errors.append(f"event {event_id} authority epoch does not match policy epoch")
            if (
                isinstance(event.get("monotonic_ns"), int)
                and isinstance(policy.get("effective_at_monotonic_ns"), int)
                and event["monotonic_ns"] < policy["effective_at_monotonic_ns"]
            ):
                errors.append(f"event {event_id} monotonic time precedes effective policy epoch")
            event_time, policy_time = _parse_datetime(event.get("occurred_at_utc")), _parse_datetime(policy.get("effective_at_utc"))
            if event_time is not None and policy_time is not None and event_time < policy_time:
                errors.append(f"event {event_id} wall-clock time precedes effective policy epoch")
        if event.get("semantic_digest") != event_semantic_digest(event):
            errors.append(f"event {event_id} semantic digest mismatch")

    attachment_events_by_digest: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("event_type") == "policy-attachment" and event.get("semantic_digest") == event_semantic_digest(event):
            attachment_events_by_digest.setdefault(event.get("semantic_digest"), []).append(event)

    attachments = document.get("policy_attachments", [])
    attachment_ids = [x.get("attachment_id") for x in attachments]
    duplicate_attachments = _duplicates(attachment_ids)
    for attachment_id in sorted(duplicate_attachments):
        errors.append(f"duplicate attachment_id {attachment_id}")
    effective_bindings = [
        (attachment.get("workload_identity"), attachment.get("policy_epoch"))
        for attachment in attachments
        if attachment.get("state") == "effective"
    ]
    for workload_identity, policy_epoch in sorted(
        _duplicates(effective_bindings), key=lambda value: (str(value[0]), str(value[1]))
    ):
        errors.append(
            f"multiple effective policy attachments for workload {workload_identity} and policy epoch {policy_epoch} are ambiguous"
        )
    for attachment in attachments:
        attachment_id = attachment.get("attachment_id")
        policy = history_by_epoch.get(attachment.get("policy_epoch"))
        if policy is None:
            errors.append(f"attachment {attachment_id} references unknown policy epoch")
            continue
        if attachment.get("state") == "effective":
            if attachment.get("policy_digest") != policy.get("policy_digest"):
                errors.append(f"effective attachment {attachment_id} policy digest does not match policy epoch")
            if len(attachment_events_by_digest.get(attachment.get("evidence_digest"), [])) != 1:
                errors.append(
                    f"effective attachment {attachment_id} evidence digest does not bind exactly one policy-attachment event"
                )

    errors.extend(
        _lifecycle_errors(
            document,
            telemetry_by_source,
            events_by_id,
            duplicate_events,
            attachments,
            duplicate_attachments,
        )
    )

    assertions = document.get("assertions", [])
    assertion_ids = [x.get("assertion_id") for x in assertions]
    duplicate_assertions = _duplicates(assertion_ids)
    for assertion_id in sorted(duplicate_assertions):
        errors.append(f"duplicate assertion_id {assertion_id}")
    if test_case is not None:
        canonical_mandatory = set(test_case.get("mandatory_assertions", []))
        present_mandatory = {
            assertion.get("assertion_id")
            for assertion in assertions
            if assertion.get("mandatory") and assertion.get("assertion_id") not in duplicate_assertions
        }
        for assertion_id in sorted(canonical_mandatory - present_mandatory):
            errors.append(f"canonical mandatory assertion {assertion_id} is missing from EvidenceEnvelope")

    for assertion in assertions:
        assertion_id = assertion.get("assertion_id")
        evidence_ids = assertion.get("evidence_event_ids", [])
        mandatory_pass = assertion.get("mandatory") and assertion.get("state") == "PASS"
        if mandatory_pass and not evidence_ids:
            errors.append(f"mandatory PASS assertion {assertion_id} requires event evidence")
        if mandatory_pass and test_case is not None and assertion_id not in set(test_case.get("mandatory_assertions", [])):
            errors.append(f"mandatory PASS assertion {assertion_id} is not bound by canonical TestCase")
        errors.extend(
            _execution_binding_errors(
                document,
                test_case,
                telemetry_by_source,
                events_by_id,
                duplicate_events,
                assertion,
            )
        )

        requirement = requirements.get(assertion_id) if requirements is not None else None
        if mandatory_pass and requirement is None:
            errors.append(f"mandatory PASS assertion {assertion_id} has no unique typed canonical requirement")
        if mandatory_pass and requirement is not None:
            matching_requirement_events = [
                events_by_id[event_id]
                for event_id in evidence_ids
                if event_id in events_by_id and event_id not in duplicate_events and _event_matches_requirement(events_by_id[event_id], requirement)
            ]
            if not matching_requirement_events:
                errors.append(f"mandatory PASS assertion {assertion_id} has no evidence matching its typed canonical requirement")

        for event_id in evidence_ids:
            if event_id not in event_ids:
                errors.append(f"assertion {assertion_id} references missing evidence event {event_id}")
                continue
            if event_id in duplicate_events:
                errors.append(f"assertion {assertion_id} evidence event {event_id} does not resolve uniquely")
                continue
            if mandatory_pass:
                event = events_by_id[event_id]
                source = telemetry_by_source.get(event.get("source_id"))
                if source is None:
                    errors.append(
                        f"mandatory PASS assertion {assertion_id} evidence event {event_id} references undeclared telemetry source {event.get('source_id')}"
                    )
                elif source.get("coverage") != "mandatory" or source.get("health") != "healthy":
                    errors.append(
                        f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires a healthy mandatory telemetry source"
                    )
                elif requirement is not None and _event_matches_requirement(event, requirement) and not _source_suitable_for_requirement(test_case, source, requirement):
                    errors.append(
                        f"mandatory PASS assertion {assertion_id} evidence event {event_id} fails typed canonical source suitability"
                    )
                elif requirement is None or not _event_matches_requirement(event, requirement):
                    pass

                epoch, workload, attachment_id = event.get("policy_epoch"), event.get("workload_identity"), event.get("attachment_id")
                matching = [
                    x
                    for x in attachments
                    if x.get("state") == "effective"
                    and x.get("policy_epoch") == epoch
                    and x.get("workload_identity") == workload
                    and x.get("attachment_id") == attachment_id
                    and x.get("attachment_id") not in duplicate_attachments
                ]
                if not workload or not attachment_id or len(matching) != 1:
                    errors.append(
                        f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires exactly one effective attachment with matching workload identity for policy epoch {epoch}"
                    )
                else:
                    attachment = matching[0]
                    provenance = attachment_events_by_digest.get(attachment.get("evidence_digest"), [])
                    if len(provenance) != 1:
                        errors.append(
                            f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires exactly one attachment effectiveness provenance event"
                        )
                    else:
                        provenance_event = provenance[0]
                        if (
                            provenance_event.get("attachment_id") != attachment.get("attachment_id")
                            or provenance_event.get("workload_identity") != attachment.get("workload_identity")
                            or provenance_event.get("policy_epoch") != attachment.get("policy_epoch")
                        ):
                            errors.append(
                                f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires matching attachment provenance identity"
                            )
                        else:
                            provenance_source_id = provenance_event.get("source_id")
                            provenance_source = telemetry_by_source.get(provenance_source_id)
                            if provenance_source_id in duplicate_sources or provenance_source is None:
                                errors.append(
                                    f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance from exactly one declared telemetry source"
                                )
                            elif provenance_source.get("coverage") != "mandatory" or provenance_source.get("health") != "healthy":
                                errors.append(
                                    f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance from a healthy mandatory telemetry source"
                                )
                            elif test_case is None or not _source_suitable_for_event(test_case, provenance_source, provenance_event.get("event_type")):
                                errors.append(
                                    f"mandatory PASS assertion {assertion_id} evidence event {event_id} attachment provenance fails canonical TestCase source suitability"
                                )
                            elif not _event_not_after(provenance_event, event):
                                errors.append(
                                    f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance at or before the PASS event on both clocks"
                                )
    return errors


def _is_credible_pass(assertion: dict[str, Any]) -> bool:
    return assertion.get("state") == "PASS" and bool(assertion.get("evidence_event_ids"))


def _authorized_utility_complete(document: dict[str, Any]) -> bool:
    case_id = document.get("case_id")
    test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    if test_case is None:
        return False
    requirements = _requirement_map(test_case)
    if requirements is None:
        return False
    assertions = document.get("assertions", [])
    duplicates = _duplicates([x.get("assertion_id") for x in assertions])
    by_id = {
        x.get("assertion_id"): x
        for x in assertions
        if x.get("assertion_id") is not None and x.get("assertion_id") not in duplicates
    }
    events = document.get("events", [])
    duplicate_event_ids = _duplicates([x.get("event_id") for x in events])
    events_by_id = {
        x.get("event_id"): x
        for x in events
        if x.get("event_id") is not None and x.get("event_id") not in duplicate_event_ids
    }
    for utility_id in test_case.get("authorized_utility", []):
        assertion = by_id.get(utility_id)
        requirement = requirements.get(utility_id)
        if assertion is None or requirement is None or not assertion.get("mandatory") or not _is_credible_pass(assertion):
            return False
        utility_events = [events_by_id.get(event_id) for event_id in assertion.get("evidence_event_ids", [])]
        if not any(event is not None and _event_matches_requirement(event, requirement) for event in utility_events):
            return False
    return True


def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False) or document.get("execution_status") != "completed":
        return "UNVERIFIED"
    if _evidence_errors(document):
        return "UNVERIFIED"
    if _residual_errors(document):
        return "FAIL"
    if not any(x.get("state") == "effective" for x in document.get("policy_attachments", [])):
        return "UNVERIFIED"
    mandatory_telemetry = [x for x in document.get("telemetry", []) if x.get("coverage") == "mandatory"]
    if not mandatory_telemetry or any(x.get("health") != "healthy" for x in mandatory_telemetry):
        return "UNVERIFIED"
    assertions = document.get("assertions", [])
    if any(x.get("state") == "FAIL" for x in assertions):
        return "FAIL"
    if not _authorized_utility_complete(document):
        return "UNVERIFIED"
    mandatory = [x for x in assertions if x.get("mandatory")]
    if not mandatory:
        return "UNVERIFIED"
    incomplete = [
        x
        for x in mandatory
        if x.get("state") in {"UNVERIFIED", "NOT-APPLICABLE"}
        or (x.get("state") == "PASS" and not x.get("evidence_event_ids"))
    ]
    if incomplete:
        return "PARTIAL" if any(_is_credible_pass(x) for x in mandatory) else "UNVERIFIED"
    return "PASS" if all(_is_credible_pass(x) for x in mandatory) else "UNVERIFIED"


def validate(document: dict[str, Any]) -> list[str]:
    errors = _evidence_errors(document)
    if errors == ["schema validation failed"]:
        return errors
    errors.extend(_residual_errors(document))
    verdict = expected_verdict(document)
    if document.get("verdict") != verdict:
        errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")
    if document.get("verdict") == "PASS":
        mandatory = [x for x in document.get("telemetry", []) if x.get("coverage") == "mandatory"]
        if not mandatory:
            errors.append("PASS requires mandatory telemetry evidence")
        elif any(x.get("health") != "healthy" for x in mandatory):
            errors.append("PASS requires every mandatory telemetry collector to be healthy")
        if not _authorized_utility_complete(document):
            errors.append("PASS requires every canonical authorized utility assertion to have typed credible evidence")
        if any(x.get("mandatory") and x.get("state") == "NOT-APPLICABLE" for x in document.get("assertions", [])):
            errors.append("PASS cannot hide a mandatory assertion as not-applicable")
        if any(x.get("state") == "FAIL" for x in document.get("assertions", [])):
            errors.append("PASS contains a failed assertion")
        if not any(x.get("state") == "effective" for x in document.get("policy_attachments", [])):
            errors.append("PASS requires effective policy attachment evidence")
        unverified = [k for k, v in document.get("post_conditions", {}).items() if v == "unverified"]
        if unverified:
            errors.append("PASS contains unverified post-conditions: " + ", ".join(unverified))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--print-digest", action="store_true")
    args = parser.parse_args()
    try:
        document = load_evidence_json(args.path.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid raw evidence JSON: {exc}")
        return 1
    if args.print_digest:
        print(artifact_digest(document))
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {document['run_id']} verdict={document['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
