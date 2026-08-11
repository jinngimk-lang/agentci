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
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


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
    """Return the authority-bearing subset this envelope can verify internally.

    This is not a substitute for a signed external AuthorityBundle. It only binds
    the authority epochs/principals/attachments/events carried by this envelope so
    that a digest field cannot be changed independently of those semantics.
    """

    return {
        "policy_history": [
            {
                "policy_epoch": item.get("policy_epoch"),
                "authority_epoch": item.get("authority_epoch"),
                "source_principal_id": item.get("source_principal_id"),
            }
            for item in document.get("policy_history", [])
        ],
        "policy_attachments": [
            {
                "attachment_id": item.get("attachment_id"),
                "workload_identity": item.get("workload_identity"),
                "policy_epoch": item.get("policy_epoch"),
                "policy_digest": item.get("policy_digest"),
                "state": item.get("state"),
            }
            for item in document.get("policy_attachments", [])
        ],
        "events": [
            {
                "event_id": item.get("event_id"),
                "authority_epoch": item.get("authority_epoch"),
                "decision_id": item.get("decision_id"),
                "receipt_id": item.get("receipt_id"),
            }
            for item in document.get("events", [])
        ],
    }


def authority_binding_digest(document: dict[str, Any]) -> str:
    return digest_value(authority_binding_projection(document))


def event_semantic_digest(event: dict[str, Any]) -> str:
    candidate = copy.deepcopy(event)
    candidate.pop("semantic_digest", None)
    return digest_value(candidate)


def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False):
        return "UNVERIFIED"
    if document.get("execution_status") != "completed":
        return "UNVERIFIED"

    telemetry = document.get("telemetry", [])
    mandatory_telemetry = [item for item in telemetry if item.get("coverage") == "mandatory"]
    if not mandatory_telemetry:
        return "UNVERIFIED"
    if any(item.get("health") != "healthy" for item in mandatory_telemetry):
        return "UNVERIFIED"

    assertions = document.get("assertions", [])
    if any(item.get("state") == "FAIL" for item in assertions):
        return "FAIL"

    mandatory = [item for item in assertions if item.get("mandatory")]
    if not mandatory:
        return "UNVERIFIED"

    incomplete = [
        item
        for item in mandatory
        if item.get("state") in {"UNVERIFIED", "NOT-APPLICABLE"}
    ]
    if incomplete:
        if any(item.get("state") == "PASS" for item in mandatory):
            return "PARTIAL"
        return "UNVERIFIED"

    if all(item.get("state") == "PASS" for item in mandatory):
        return "PASS"
    return "UNVERIFIED"


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("apiVersion") != "agentci.dev/sandbox/v0alpha1":
        errors.append("unexpected apiVersion")
    if document.get("kind") != "EvidenceEnvelope":
        errors.append("validator only accepts EvidenceEnvelope")
    if document.get("verdict_rule_version") != VERDICT_RULE:
        errors.append("unexpected verdict rule version")

    canonicalization = document.get("canonicalization", {})
    if canonicalization.get("algorithm") != CANONICALIZATION:
        errors.append("unexpected canonicalization algorithm")
    expected_digest = artifact_digest(document)
    if canonicalization.get("artifact_digest") != expected_digest:
        errors.append("artifact digest mismatch")

    expected_history_digest = policy_history_digest(document)
    if document.get("policy_history_digest") != expected_history_digest:
        errors.append("policy history digest mismatch")

    expected_authority_digest = authority_binding_digest(document)
    if document.get("authority_digest") != expected_authority_digest:
        errors.append("authority digest mismatch")

    epochs = {entry.get("policy_epoch") for entry in document.get("policy_history", [])}
    if None in epochs or not epochs:
        errors.append("policy history must contain concrete epochs")

    events = document.get("events", [])
    event_ids = {event.get("event_id") for event in events}
    for event in events:
        if event.get("policy_epoch") not in epochs:
            errors.append(f"event {event.get('event_id')} references unknown policy epoch")
        if event.get("semantic_digest") != event_semantic_digest(event):
            errors.append(f"event {event.get('event_id')} semantic digest mismatch")

    attachments = document.get("policy_attachments", [])
    for attachment in attachments:
        if attachment.get("policy_epoch") not in epochs:
            errors.append(f"attachment {attachment.get('attachment_id')} references unknown policy epoch")

    for assertion in document.get("assertions", []):
        for event_id in assertion.get("evidence_event_ids", []):
            if event_id not in event_ids:
                errors.append(
                    f"assertion {assertion.get('assertion_id')} references missing evidence event {event_id}"
                )

    verdict = expected_verdict(document)
    if document.get("verdict") != verdict:
        errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")

    if document.get("verdict") == "PASS":
        mandatory_telemetry = [
            item for item in document.get("telemetry", []) if item.get("coverage") == "mandatory"
        ]
        if not mandatory_telemetry:
            errors.append("PASS requires mandatory telemetry evidence")
        elif any(item.get("health") != "healthy" for item in mandatory_telemetry):
            errors.append("PASS requires every mandatory telemetry collector to be healthy")

        if any(
            item.get("mandatory") and item.get("state") == "NOT-APPLICABLE"
            for item in document.get("assertions", [])
        ):
            errors.append("PASS cannot hide a mandatory assertion as not-applicable")

        if any(item.get("state") == "FAIL" for item in document.get("assertions", [])):
            errors.append("PASS contains a failed assertion")

        if not any(item.get("state") == "effective" for item in attachments):
            errors.append("PASS requires effective policy attachment evidence")

        material_unverified = [
            key
            for key, value in document.get("post_conditions", {}).items()
            if value == "unverified"
        ]
        if material_unverified:
            errors.append("PASS contains unverified post-conditions: " + ", ".join(material_unverified))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--print-digest", action="store_true")
    args = parser.parse_args()

    document = json.loads(args.path.read_text(encoding="utf-8"))
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
