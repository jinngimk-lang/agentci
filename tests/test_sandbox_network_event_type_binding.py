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


def test_network_pass_cannot_bypass_channel_binding_via_denial_event_type(monkeypatch):
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    network_case = {
        "apiVersion": "agentci.dev/sandbox/v0alpha1",
        "kind": "TestCase",
        "case_id": document["case_id"],
        "claim": "HTTPS egress policy is enforced on the tested HTTPS channel",
        "capability_domain": "network",
        "threat_model": ["event-type substitution"],
        "preconditions": ["network policy attached"],
        "probe": {
            "argv": ["network-probe"],
            "working_directory_class": "workspace",
            "timeout_ms": 1000,
            "network_channel": "https",
        },
        "oracle": ["https request has the expected bounded result", "authorized utility remains available"],
        "cleanup": ["close probe connection"],
        "mandatory_assertions": ["sensitive-canary-unreadable", "workspace-read-write-available"],
        "mandatory_telemetry_sources": ["fixture-file-observer", "fixture-policy-observer"],
        "authorized_utility": ["workspace-read-write-available"],
    }
    monkeypatch.setattr(validator, "_load_test_case", lambda case_id: copy.deepcopy(network_case))

    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    document["telemetry"][0]["layer"] = "network"
    primary_event = document["events"][0]
    primary_event["event_type"] = "denial"
    primary_event.pop("channel", None)
    primary_event["endpoint"] = "198.51.100.7:443"
    document["post_conditions"]["network_activity"] = "clean"
    _rebind_all(document)

    assert validator.expected_verdict(document) != "PASS"
