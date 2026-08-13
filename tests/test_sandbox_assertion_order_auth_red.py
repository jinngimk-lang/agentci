import copy
import json
from pathlib import Path

from scripts.validate_sandbox_evidence import artifact_digest, event_semantic_digest, expected_verdict

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_assertion_side_ordering_cannot_be_rewritten_to_manufacture_causality():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    # Preserve the externally authenticated process observation from #82, but
    # make the red-control assertion nominally PASS and rewrite only the
    # assertion-side ordering fields. These fields remain producer-local even
    # though _event_not_after() relies on them for causal ordering.
    tampered = copy.deepcopy(document)
    sensitive_assertion = next(
        assertion
        for assertion in tampered["assertions"]
        if assertion["assertion_id"] == "sensitive-canary-unreadable"
    )
    sensitive_assertion["state"] = "PASS"
    tampered["verdict"] = "PASS"

    evidence_id = sensitive_assertion["evidence_event_ids"][0]
    evidence_event = next(event for event in tampered["events"] if event["event_id"] == evidence_id)
    evidence_event["occurred_at_utc"] = "2026-08-11T03:00:09Z"
    evidence_event["monotonic_ns"] = 9000
    evidence_event["semantic_digest"] = event_semantic_digest(evidence_event)
    tampered["canonicalization"]["artifact_digest"] = artifact_digest(tampered)

    # A producer-recomputable assertion timestamp must not be enough to prove
    # that authenticated probe execution occurred before this evidence.
    assert expected_verdict(tampered) != "PASS"
