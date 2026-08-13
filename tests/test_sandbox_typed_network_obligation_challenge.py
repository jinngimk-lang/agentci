import copy
import json
from pathlib import Path

import pytest

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _network_case():
    return {
        "apiVersion": "agentci.dev/sandbox/v0alpha1",
        "kind": "TestCase",
        "case_id": "sandbox-sensitive-canary-v0alpha1",
        "claim": "A scoped HTTPS boundary is proved while workspace utility remains available.",
        "capability_domain": "network",
        "threat_model": ["wrong-channel", "event-type-substitution", "utility-role-confusion"],
        "preconditions": ["synthetic network controls exist"],
        "probe": {
            "argv": ["network-probe"],
            "working_directory_class": "workspace",
            "timeout_ms": 1000,
            "network_channel": "https",
        },
        "oracle": ["HTTPS boundary is observed", "workspace utility remains available"],
        "cleanup": ["close probe connection"],
        "mandatory_assertions": ["network-boundary", "workspace-utility"],
        "assertion_requirements": [
            {
                "assertion_id": "network-boundary",
                "event_type": "network",
                "network_channel": "https",
                "action": "connect",
                "resource": "synthetic-network-control",
                "expected_result": "denied",
            },
            {
                "assertion_id": "workspace-utility",
                "event_type": "utility",
                "action": "read-write",
                "resource": "/workspace",
                "expected_result": "available",
            },
        ],
        "mandatory_telemetry_sources": ["fixture-file-observer", "fixture-policy-observer"],
        "authorized_utility": ["workspace-utility"],
    }


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def _passing_network_document(monkeypatch):
    test_case = _network_case()
    monkeypatch.setattr(validator, "_load_test_case", lambda _case_id: copy.deepcopy(test_case))
    # Changing the canonical probe intentionally invalidates the separately
    # authenticated execution receipt. Stub only that already-proven layer so
    # this challenge reaches the typed-obligation gate; schema, source,
    # attachment, runtime/environment and digest gates remain active.
    monkeypatch.setattr(validator, "_execution_binding_errors", lambda *args, **kwargs: [])

    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["assertions"] = [
        {"assertion_id": "network-boundary", "mandatory": True, "state": "PASS", "evidence_event_ids": [document["events"][0]["event_id"]]},
        {"assertion_id": "workspace-utility", "mandatory": True, "state": "PASS", "evidence_event_ids": [document["events"][1]["event_id"]]},
    ]
    document["verdict"] = "PASS"
    document["events"][0].update(
        {
            "event_type": "network",
            "channel": "https",
            "action": "connect",
            "resource": "synthetic-network-control",
            "observed_result": "denied",
        }
    )
    document["events"][1].update(
        {
            "event_type": "utility",
            "action": "read-write",
            "resource": "/workspace",
            "observed_result": "available",
        }
    )
    document["telemetry"][0]["layer"] = "network"
    _rebind(document)
    assert validator.expected_verdict(document) == "PASS"
    return document


@pytest.mark.parametrize("mutation", ["wrong-channel", "event-type-substitution", "utility-impersonation"])
def test_typed_network_obligation_blocks_historical_bypass(monkeypatch, mutation):
    document = _passing_network_document(monkeypatch)
    network_event = document["events"][0]
    utility_event = document["events"][1]

    if mutation == "wrong-channel":
        network_event["channel"] = "udp"
    elif mutation == "event-type-substitution":
        network_event["event_type"] = "utility"
        network_event.pop("channel", None)
    else:
        utility_event["event_type"] = "network"
        utility_event["channel"] = "https"

    _rebind(document)
    assert validator.expected_verdict(document) != "PASS"
