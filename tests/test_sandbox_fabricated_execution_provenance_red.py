import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_fabricated_process_provenance_cannot_make_unexecuted_probe_pass(monkeypatch):
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    original_case = validator._load_test_case(document["case_id"])
    assert original_case is not None

    changed_case = copy.deepcopy(original_case)
    changed_case["probe"]["argv"] = ["synthetic-probe-that-did-not-run", "--safe"]
    monkeypatch.setattr(validator, "_load_test_case", lambda case_id: copy.deepcopy(changed_case))

    # Forge a fresh execution namespace entirely from producer-controlled
    # envelope fields while retaining otherwise genuine PASS semantics.
    assertion_events = []
    for assertion in document["assertions"]:
        for event_id in assertion["evidence_event_ids"]:
            assertion_events.append(next(event for event in document["events"] if event["event_id"] == event_id))

    sample_event = assertion_events[0]
    fresh_binding = validator.execution_binding_id(document, changed_case, sample_event)

    rename = {}
    for event in assertion_events:
        suffix = event["event_id"].split(":", 2)[-1]
        new_id = f"{fresh_binding}:{suffix}"
        rename[event["event_id"]] = new_id
        event["event_id"] = new_id

    for assertion in document["assertions"]:
        assertion["evidence_event_ids"] = [rename[event_id] for event_id in assertion["evidence_event_ids"]]

    execution_event = next(event for event in document["events"] if event["event_type"] == "process")
    execution_event["event_id"] = fresh_binding
    execution_event["workload_identity"] = sample_event["workload_identity"]
    execution_event["policy_epoch"] = sample_event["policy_epoch"]
    execution_event["authority_epoch"] = sample_event["authority_epoch"]

    _rebind_all(document)

    # A malicious producer can calculate the same deterministic binding and
    # manufacture the process event without executing the changed probe. That is
    # self-consistency, not machine-verifiable execution provenance.
    errors = validator.validate(document)
    assert validator.expected_verdict(document) == "UNVERIFIED"
    assert f"execution provenance event {fresh_binding} lacks valid external execution attestation" in errors
