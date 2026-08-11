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


def canonical_bytes(document: dict[str, Any]) -> bytes:
    candidate = copy.deepcopy(document)
    canonicalization = candidate.get("canonicalization")
    if isinstance(canonicalization, dict):
        canonicalization.pop("artifact_digest", None)
    return json.dumps(
        candidate,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_digest(document: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False):
        return "UNVERIFIED"
    if document.get("execution_status") != "completed":
        return "UNVERIFIED"

    telemetry = document.get("telemetry", [])
    if any(
        item.get("coverage") == "mandatory"
        and item.get("health") not in {"healthy", "degraded"}
        for item in telemetry
    ):
        return "UNVERIFIED"

    assertions = document.get("assertions", [])
    mandatory = [item for item in assertions if item.get("mandatory")]
    if not mandatory:
        return "UNVERIFIED"
    if any(item.get("state") == "FAIL" for item in mandatory):
        return "FAIL"
    if any(item.get("state") == "UNVERIFIED" for item in mandatory):
        if any(item.get("state") == "PASS" for item in mandatory):
            return "PARTIAL"
        return "UNVERIFIED"
    if all(item.get("state") in {"PASS", "NOT-APPLICABLE"} for item in mandatory):
        if any(item.get("state") == "PASS" for item in mandatory):
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

    epochs = {entry.get("policy_epoch") for entry in document.get("policy_history", [])}
    if None in epochs or not epochs:
        errors.append("policy history must contain concrete epochs")
    for event in document.get("events", []):
        if event.get("policy_epoch") not in epochs:
            errors.append(f"event {event.get('event_id')} references unknown policy epoch")

    attachments = document.get("policy_attachments", [])
    for attachment in attachments:
        if attachment.get("policy_epoch") not in epochs:
            errors.append(f"attachment {attachment.get('attachment_id')} references unknown policy epoch")

    verdict = expected_verdict(document)
    if document.get("verdict") != verdict:
        errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")

    if document.get("verdict") == "PASS":
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
