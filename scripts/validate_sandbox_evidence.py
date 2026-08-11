#!/usr/bin/env python3
"""Minimal S0 semantic validator for AgentCI sandbox EvidenceEnvelope.

This is a design-stage contract validator, not a released sandbox certification engine.
It deliberately checks only invariants that are already accepted by the S0 program.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

CANONICALIZATION = "agentci-json-c14n-v0alpha1"
VERDICT_RULE = "agentci-sandbox-atomic-v0alpha1"


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
        "policy_history": [{"policy_epoch": i.get("policy_epoch"), "authority_epoch": i.get("authority_epoch"), "source_principal_id": i.get("source_principal_id")} for i in document.get("policy_history", [])],
        "policy_attachments": [{"attachment_id": i.get("attachment_id"), "workload_identity": i.get("workload_identity"), "policy_epoch": i.get("policy_epoch"), "policy_digest": i.get("policy_digest"), "state": i.get("state")} for i in document.get("policy_attachments", [])],
        "events": [{"event_id": i.get("event_id"), "authority_epoch": i.get("authority_epoch"), "decision_id": i.get("decision_id"), "receipt_id": i.get("receipt_id")} for i in document.get("events", [])],
    }


def authority_binding_digest(document: dict[str, Any]) -> str:
    return digest_value(authority_binding_projection(document))


def event_semantic_digest(event: dict[str, Any]) -> str:
    candidate = copy.deepcopy(event)
    candidate.pop("semantic_digest", None)
    return digest_value(candidate)


def _is_credible_pass(assertion: dict[str, Any]) -> bool:
    return assertion.get("state") == "PASS" and bool(assertion.get("evidence_event_ids"))


def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False) or document.get("execution_status") != "completed":
        return "UNVERIFIED"
    telemetry = document.get("telemetry", [])
    mandatory_telemetry = [i for i in telemetry if i.get("coverage") == "mandatory"]
    if not mandatory_telemetry or any(i.get("health") != "healthy" for i in mandatory_telemetry):
        return "UNVERIFIED"
    assertions = document.get("assertions", [])
    if any(i.get("state") == "FAIL" for i in assertions):
        return "FAIL"
    mandatory = [i for i in assertions if i.get("mandatory")]
    if not mandatory:
        return "UNVERIFIED"
    incomplete = [i for i in mandatory if i.get("state") in {"UNVERIFIED", "NOT-APPLICABLE"} or (i.get("state") == "PASS" and not i.get("evidence_event_ids"))]
    if incomplete:
        return "PARTIAL" if any(_is_credible_pass(i) for i in mandatory) else "UNVERIFIED"
    return "PASS" if all(_is_credible_pass(i) for i in mandatory) else "UNVERIFIED"


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("apiVersion") != "agentci.dev/sandbox/v0alpha1": errors.append("unexpected apiVersion")
    if document.get("kind") != "EvidenceEnvelope": errors.append("validator only accepts EvidenceEnvelope")
    if document.get("verdict_rule_version") != VERDICT_RULE: errors.append("unexpected verdict rule version")
    canonicalization = document.get("canonicalization", {})
    if canonicalization.get("algorithm") != CANONICALIZATION: errors.append("unexpected canonicalization algorithm")
    if canonicalization.get("artifact_digest") != artifact_digest(document): errors.append("artifact digest mismatch")
    if document.get("policy_history_digest") != policy_history_digest(document): errors.append("policy history digest mismatch")
    if document.get("authority_digest") != authority_binding_digest(document): errors.append("authority digest mismatch")

    epochs = {e.get("policy_epoch") for e in document.get("policy_history", [])}
    if None in epochs or not epochs: errors.append("policy history must contain concrete epochs")

    telemetry = document.get("telemetry", [])
    source_ids = [i.get("source_id") for i in telemetry if i.get("source_id") is not None]
    duplicate_source_ids = {sid for sid in source_ids if source_ids.count(sid) > 1}
    for source_id in sorted(duplicate_source_ids):
        errors.append(f"duplicate telemetry source_id {source_id}")
    telemetry_by_source = {i.get("source_id"): i for i in telemetry if i.get("source_id") is not None}

    events = document.get("events", [])
    concrete_event_ids = [e.get("event_id") for e in events if e.get("event_id") is not None]
    duplicate_event_ids = {event_id for event_id in concrete_event_ids if concrete_event_ids.count(event_id) > 1}
    for event_id in sorted(duplicate_event_ids):
        errors.append(f"duplicate event_id {event_id}")
    event_ids = set(concrete_event_ids)
    events_by_id = {e.get("event_id"): e for e in events if e.get("event_id") is not None}
    for event in events:
        if event.get("policy_epoch") not in epochs: errors.append(f"event {event.get('event_id')} references unknown policy epoch")
        if event.get("semantic_digest") != event_semantic_digest(event): errors.append(f"event {event.get('event_id')} semantic digest mismatch")

    attachments = document.get("policy_attachments", [])
    for attachment in attachments:
        if attachment.get("policy_epoch") not in epochs: errors.append(f"attachment {attachment.get('attachment_id')} references unknown policy epoch")

    for assertion in document.get("assertions", []):
        evidence_event_ids = assertion.get("evidence_event_ids", [])
        is_mandatory_pass = assertion.get("mandatory") and assertion.get("state") == "PASS"
        if is_mandatory_pass and not evidence_event_ids: errors.append(f"mandatory PASS assertion {assertion.get('assertion_id')} requires event evidence")
        for event_id in evidence_event_ids:
            if event_id not in event_ids:
                errors.append(f"assertion {assertion.get('assertion_id')} references missing evidence event {event_id}")
                continue
            if event_id in duplicate_event_ids:
                errors.append(f"assertion {assertion.get('assertion_id')} evidence event {event_id} does not resolve uniquely")
                continue
            if is_mandatory_pass:
                event = events_by_id[event_id]
                source_id = event.get("source_id")
                source = telemetry_by_source.get(source_id)
                if source is None: errors.append(f"mandatory PASS assertion {assertion.get('assertion_id')} evidence event {event_id} references undeclared telemetry source {source_id}")
                elif source_id in duplicate_source_ids: errors.append(f"mandatory PASS assertion {assertion.get('assertion_id')} evidence event {event_id} references duplicate telemetry source {source_id}")
                elif source.get("coverage") != "mandatory" or source.get("health") != "healthy": errors.append(f"mandatory PASS assertion {assertion.get('assertion_id')} evidence event {event_id} requires a healthy mandatory telemetry source")

    verdict = expected_verdict(document)
    if document.get("verdict") != verdict: errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")
    if document.get("verdict") == "PASS":
        mandatory_telemetry = [i for i in telemetry if i.get("coverage") == "mandatory"]
        if not mandatory_telemetry: errors.append("PASS requires mandatory telemetry evidence")
        elif any(i.get("health") != "healthy" for i in mandatory_telemetry): errors.append("PASS requires every mandatory telemetry collector to be healthy")
        if duplicate_source_ids: errors.append("PASS requires unique telemetry source identities")
        if duplicate_event_ids: errors.append("PASS requires unique event identities")
        if any(i.get("mandatory") and i.get("state") == "NOT-APPLICABLE" for i in document.get("assertions", [])): errors.append("PASS cannot hide a mandatory assertion as not-applicable")
        if any(i.get("state") == "FAIL" for i in document.get("assertions", [])): errors.append("PASS contains a failed assertion")
        if not any(i.get("state") == "effective" for i in attachments): errors.append("PASS requires effective policy attachment evidence")
        material_unverified = [k for k, v in document.get("post_conditions", {}).items() if v == "unverified"]
        if material_unverified: errors.append("PASS contains unverified post-conditions: " + ", ".join(material_unverified))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("path", type=Path); parser.add_argument("--print-digest", action="store_true"); args = parser.parse_args()
    document = json.loads(args.path.read_text(encoding="utf-8"))
    if args.print_digest: print(artifact_digest(document))
    errors = validate(document)
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    print(f"OK: {document['run_id']} verdict={document['verdict']}"); return 0


if __name__ == "__main__": raise SystemExit(main())
