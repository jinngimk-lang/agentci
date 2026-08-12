import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind_all(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_network_security_assertion_cannot_launder_probe_obligation_through_unrelated_mandatory_assertion(monkeypatch):
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    network_case = {
        "apiVersion": "agentci.dev/sandbox/v0alpha1",
        "kind": "TestCase",
        "case_id": document["case_id"],
        "claim": "HTTPS egress boundary and authorized utility are both verified",
        "capability_domain": "network",
        "threat_model": ["assertion-role laundering"],
        "preconditions": ["network policy attached"],
        "probe": {
            "argv": ["network-probe"],
            "working_directory_class": "workspace",
            "timeout_ms": 1000,
            "network_channel": "https",
        },
        "oracle": [
            "network boundary denies the forbidden HTTPS action",
            "independent mandatory bookkeeping assertion remains satisfied",
        ],
        "cleanup": ["close probe connection"],
        "mandatory_assertions": [
            "sensitive-canary-unreadable",
            "workspace-read-write-available",
        ],
        "authorized_utility": ["sensitive-canary-unreadable"],
        "mandatory_telemetry_sources": [
            "fixture-file-observer",
            "fixture-policy-observer",
        ],
    }
    monkeypatch.setattr(validator, "_load_test_case", lambda case_id: copy.deepcopy(network_case))

    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["telemetry"][0]["layer"] = "network"

    security_event = document["events"][0]
    security_event["event_type"] = "utility"
    security_event.pop("channel", None)
    security_event.pop("endpoint", None)

    unrelated_event = document["events"][1]
    unrelated_event["event_type"] = "network"
    unrelated_event["channel"] = "https"
    unrelated_event["endpoint"] = "198.51.100.7:443"

    document["post_conditions"]["network_activity"] = "clean"
    _rebind_all(document)

    assert validator.expected_verdict(document) != "PASS"
    errors = validator.validate(document)
    assert any("probe" in error.lower() or "channel" in error.lower() for error in errors)
