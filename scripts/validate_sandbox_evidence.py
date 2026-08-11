#!/usr/bin/env python3
"""Minimal S0 semantic validator for AgentCI sandbox EvidenceEnvelope.

Design-stage only: this is not a released sandbox certification engine.
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

CANONICALIZATION = "agentci-json-c14n-v0alpha1"
VERDICT_RULE = "agentci-sandbox-atomic-v0alpha1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "sandbox-certification-v0alpha1.schema.json"


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_evidence_json(raw: str) -> dict[str, Any]:
    """Parse raw evidence without silently collapsing contradictory object keys."""
    document = json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    if not isinstance(document, dict):
        raise ValueError("evidence root must be a JSON object")
    return document


def canonical_value_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_value_bytes(value)).hexdigest()


def canonical_bytes(document: dict[str, Any]) -> bytes:
    candidate = copy.deepcopy(document)
    canonicalization = candidate.get("canonicalization")
    if isinstance(canonicalization, dict):
        canonicalization.pop("artifact_digest", None)
    return canonical_value_bytes(candidate)


def artifact_digest(document: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def policy_history_digest(document: dict[str, Any]) -> str:
    return digest_value(document.get("policy_history", []))


def authority_binding_projection(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_history": [
            {"policy_epoch": item.get("policy_epoch"), "authority_epoch": item.get("authority_epoch"), "source_principal_id": item.get("source_principal_id")}
            for item in document.get("policy_history", [])
        ],
        "policy_attachments": [
            {"attachment_id": item.get("attachment_id"), "workload_identity": item.get("workload_identity"), "policy_epoch": item.get("policy_epoch"), "policy_digest": item.get("policy_digest"), "state": item.get("state")}
            for item in document.get("policy_attachments", [])
        ],
        "events": [
            {"event_id": item.get("event_id"), "authority_epoch": item.get("authority_epoch"), "decision_id": item.get("decision_id"), "receipt_id": item.get("receipt_id")}
            for item in document.get("events", [])
        ],
    }


def authority_binding_digest(document: dict[str, Any]) -> str:
    return digest_value(authority_binding_projection(document))


def event_semantic_digest(event: dict[str, Any]) -> str:
    candidate = copy.deepcopy(event)
    candidate.pop("semantic_digest", None)
    return digest_value(candidate)


@lru_cache(maxsize=1)
def _schema_validator() -> Draft202012Validator:
    schema = load_evidence_json(SCHEMA_PATH.read_text(encoding="utf-8"))
    envelope_schema = {"$schema": schema["$schema"], "$id": schema.get("$id", "") + "#EvidenceEnvelopeValidation", "$defs": schema["$defs"], "$ref": "#/$defs/EvidenceEnvelope"}
    return Draft202012Validator(envelope_schema, format_checker=FormatChecker())


def _format_fields_valid(document: dict[str, Any]) -> bool:
    checker = FormatChecker()
    values = [item.get("effective_at_utc") for item in document.get("policy_history", [])]
    values.extend(event.get("occurred_at_utc") for event in document.get("events", []))
    for value in values:
        try:
            checker.check(value, "date-time")
        except FormatError:
            return False
    return True


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duplicates(values: list[Any]) -> set[Any]:
    return {value for value in values if value is not None and values.count(value) > 1}


def _residual_errors(document: dict[str, Any]) -> list[str]:
    post = document.get("post_conditions", {})
    errors: list[str] = []
    if post.get("descendants") == "residual": errors.append("residual descendants violate PASS")
    if post.get("filesystem_residue") == "residual": errors.append("residual filesystem state violates PASS")
    if post.get("sockets") == "residual": errors.append("residual sockets violate PASS")
    return errors


def _evidence_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if list(_schema_validator().iter_errors(document)) or not _format_fields_valid(document): errors.append("schema validation failed")
    if document.get("apiVersion") != "agentci.dev/sandbox/v0alpha1": errors.append("unexpected apiVersion")
    if document.get("kind") != "EvidenceEnvelope": errors.append("validator only accepts EvidenceEnvelope")
    if document.get("verdict_rule_version") != VERDICT_RULE: errors.append("unexpected verdict rule version")
    canonicalization = document.get("canonicalization", {})
    if canonicalization.get("algorithm") != CANONICALIZATION: errors.append("unexpected canonicalization algorithm")
    if canonicalization.get("artifact_digest") != artifact_digest(document): errors.append("artifact digest mismatch")
    if document.get("policy_history_digest") != policy_history_digest(document): errors.append("policy history digest mismatch")
    if document.get("authority_digest") != authority_binding_digest(document): errors.append("authority digest mismatch")
    history = document.get("policy_history", [])
    epoch_values = [item.get("policy_epoch") for item in history]
    duplicate_epochs = _duplicates(epoch_values)
    if not epoch_values or any(value is None for value in epoch_values): errors.append("policy history must contain concrete epochs")
    for epoch in sorted(duplicate_epochs): errors.append(f"duplicate policy_epoch {epoch}")
    previous_epoch = previous_monotonic = None
    for item in history:
        epoch, monotonic = item.get("policy_epoch"), item.get("effective_at_monotonic_ns")
        if isinstance(epoch, int) and isinstance(previous_epoch, int) and epoch < previous_epoch: errors.append("policy history epochs must strictly increase in document order")
        if isinstance(monotonic, int) and isinstance(previous_monotonic, int) and monotonic <= previous_monotonic: errors.append("policy history monotonic time must strictly increase with epoch")
        if isinstance(epoch, int): previous_epoch = epoch
        if isinstance(monotonic, int): previous_monotonic = monotonic
    history_by_epoch = {item.get("policy_epoch"): item for item in history if isinstance(item.get("policy_epoch"), int) and item.get("policy_epoch") not in duplicate_epochs}
    telemetry = document.get("telemetry", [])
    source_values = [item.get("source_id") for item in telemetry]
    duplicate_sources = _duplicates(source_values)
    for source_id in sorted(duplicate_sources): errors.append(f"duplicate telemetry source_id {source_id}")
    telemetry_by_source = {item.get("source_id"): item for item in telemetry if item.get("source_id") is not None and item.get("source_id") not in duplicate_sources}
    events = document.get("events", [])
    event_values = [event.get("event_id") for event in events]
    duplicate_events = _duplicates(event_values)
    for event_id in sorted(duplicate_events): errors.append(f"duplicate event_id {event_id}")
    event_ids = {value for value in event_values if value is not None}
    events_by_id = {event.get("event_id"): event for event in events if event.get("event_id") is not None and event.get("event_id") not in duplicate_events}
    event_sources = {event.get("source_id") for event in events}
    for source in telemetry:
        if source.get("coverage") == "mandatory" and source.get("source_id") not in event_sources: errors.append(f"mandatory telemetry source {source.get('source_id')} has no events")
    for event in events:
        event_id, source_id = event.get("event_id"), event.get("source_id")
        if source_id not in telemetry_by_source and source_id not in duplicate_sources: errors.append(f"event {event_id} references undeclared telemetry source {source_id}")
        policy_entry = history_by_epoch.get(event.get("policy_epoch"))
        if policy_entry is None: errors.append(f"event {event_id} references unknown policy epoch")
        else:
            if event.get("authority_epoch") != policy_entry.get("authority_epoch"): errors.append(f"event {event_id} authority epoch does not match policy epoch")
            event_mono, policy_mono = event.get("monotonic_ns"), policy_entry.get("effective_at_monotonic_ns")
            if isinstance(event_mono, int) and isinstance(policy_mono, int) and event_mono < policy_mono: errors.append(f"event {event_id} monotonic time precedes effective policy epoch")
            event_time, policy_time = _parse_datetime(event.get("occurred_at_utc")), _parse_datetime(policy_entry.get("effective_at_utc"))
            if event_time is not None and policy_time is not None and event_time < policy_time: errors.append(f"event {event_id} wall-clock time precedes effective policy epoch")
        if event.get("semantic_digest") != event_semantic_digest(event): errors.append(f"event {event_id} semantic digest mismatch")
    attachment_event_digests = {event.get("semantic_digest") for event in events if event.get("event_type") == "policy-attachment" and event.get("semantic_digest") == event_semantic_digest(event)}
    attachments = document.get("policy_attachments", [])
    attachment_values = [item.get("attachment_id") for item in attachments]
    for attachment_id in sorted(_duplicates(attachment_values)): errors.append(f"duplicate attachment_id {attachment_id}")
    for attachment in attachments:
        attachment_id, policy_entry = attachment.get("attachment_id"), history_by_epoch.get(attachment.get("policy_epoch"))
        if policy_entry is None:
            errors.append(f"attachment {attachment_id} references unknown policy epoch"); continue
        if attachment.get("state") == "effective":
            if attachment.get("policy_digest") != policy_entry.get("policy_digest"): errors.append(f"effective attachment {attachment_id} policy digest does not match policy epoch")
            if attachment.get("evidence_digest") not in attachment_event_digests: errors.append(f"effective attachment {attachment_id} evidence digest does not bind a policy-attachment event")
    assertions = document.get("assertions", [])
    assertion_values = [item.get("assertion_id") for item in assertions]
    for assertion_id in sorted(_duplicates(assertion_values)): errors.append(f"duplicate assertion_id {assertion_id}")
    for assertion in assertions:
        assertion_id, evidence_ids = assertion.get("assertion_id"), assertion.get("evidence_event_ids", [])
        mandatory_pass = assertion.get("mandatory") and assertion.get("state") == "PASS"
        if mandatory_pass and not evidence_ids: errors.append(f"mandatory PASS assertion {assertion_id} requires event evidence")
        for event_id in evidence_ids:
            if event_id not in event_ids: errors.append(f"assertion {assertion_id} references missing evidence event {event_id}"); continue
            if event_id in duplicate_events: errors.append(f"assertion {assertion_id} evidence event {event_id} does not resolve uniquely"); continue
            if mandatory_pass:
                event = events_by_id[event_id]; source_id = event.get("source_id"); source = telemetry_by_source.get(source_id)
                if source is None: errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} references undeclared telemetry source {source_id}")
                elif source.get("coverage") != "mandatory" or source.get("health") != "healthy": errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires a healthy mandatory telemetry source")
    return errors


def _is_credible_pass(assertion: dict[str, Any]) -> bool:
    return assertion.get("state") == "PASS" and bool(assertion.get("evidence_event_ids"))


def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False) or document.get("execution_status") != "completed": return "UNVERIFIED"
    if _evidence_errors(document): return "UNVERIFIED"
    if _residual_errors(document): return "FAIL"
    mandatory_telemetry = [item for item in document.get("telemetry", []) if item.get("coverage") == "mandatory"]
    if not mandatory_telemetry or any(item.get("health") != "healthy" for item in mandatory_telemetry): return "UNVERIFIED"
    assertions = document.get("assertions", [])
    if any(item.get("state") == "FAIL" for item in assertions): return "FAIL"
    mandatory = [item for item in assertions if item.get("mandatory")]
    if not mandatory: return "UNVERIFIED"
    incomplete = [item for item in mandatory if item.get("state") in {"UNVERIFIED", "NOT-APPLICABLE"} or (item.get("state") == "PASS" and not item.get("evidence_event_ids"))]
    if incomplete: return "PARTIAL" if any(_is_credible_pass(item) for item in mandatory) else "UNVERIFIED"
    return "PASS" if all(_is_credible_pass(item) for item in mandatory) else "UNVERIFIED"


def validate(document: dict[str, Any]) -> list[str]:
    errors = _evidence_errors(document); errors.extend(_residual_errors(document)); verdict = expected_verdict(document)
    if document.get("verdict") != verdict: errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")
    if document.get("verdict") == "PASS":
        telemetry, attachments = document.get("telemetry", []), document.get("policy_attachments", [])
        mandatory = [item for item in telemetry if item.get("coverage") == "mandatory"]
        if not mandatory: errors.append("PASS requires mandatory telemetry evidence")
        elif any(item.get("health") != "healthy" for item in mandatory): errors.append("PASS requires every mandatory telemetry collector to be healthy")
        if any(item.get("mandatory") and item.get("state") == "NOT-APPLICABLE" for item in document.get("assertions", [])): errors.append("PASS cannot hide a mandatory assertion as not-applicable")
        if any(item.get("state") == "FAIL" for item in document.get("assertions", [])): errors.append("PASS contains a failed assertion")
        if not any(item.get("state") == "effective" for item in attachments): errors.append("PASS requires effective policy attachment evidence")
        unverified = [key for key, value in document.get("post_conditions", {}).items() if value == "unverified"]
        if unverified: errors.append("PASS contains unverified post-conditions: " + ", ".join(unverified))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("path", type=Path); parser.add_argument("--print-digest", action="store_true"); args = parser.parse_args()
    try:
        document = load_evidence_json(args.path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid raw evidence JSON: {exc}"); return 1
    if args.print_digest: print(artifact_digest(document))
    errors = validate(document)
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    print(f"OK: {document['run_id']} verdict={document['verdict']}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
