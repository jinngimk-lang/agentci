import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def test_assertion_side_ordering_cannot_be_rewritten_to_manufacture_causality():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    # Preserve the genuine PASS observation but rewrite only assertion-side
    # ordering fields consumed by causal validation.
    tampered = copy.deepcopy(document)
    sensitive_assertion = next(
        assertion
        for assertion in tampered["assertions"]
        if assertion["assertion_id"] == "sensitive-canary-unreadable"
    )
    evidence_id = sensitive_assertion["evidence_event_ids"][0]
    evidence_event = next(event for event in tampered["events"] if event["event_id"] == evidence_id)
    evidence_event["occurred_at_utc"] = "2026-08-11T03:00:09Z"
    evidence_event["monotonic_ns"] = 9000
    evidence_event["semantic_digest"] = validator.event_semantic_digest(evidence_event)
    tampered["canonicalization"]["artifact_digest"] = validator.artifact_digest(tampered)

    # A producer-recomputable assertion timestamp must not be enough to prove
    # that authenticated probe execution occurred before this evidence.
    errors = validator.validate(tampered)
    assert validator.expected_verdict(tampered) == "UNVERIFIED"
    assert any("lacks valid external execution attestation" in error for error in errors)
