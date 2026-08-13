import copy

import pytest

import scripts.validate_sandbox_evidence as validator


def _network_case():
    return {
        "apiVersion": "agentci.dev/sandbox/v0alpha1",
        "kind": "TestCase",
        "case_id": "typed-network-challenge",
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
        "mandatory_telemetry_sources": ["network-observer", "workspace-observer"],
        "authorized_utility": ["workspace-utility"],
    }


def test_typed_requirement_map_makes_network_and_utility_roles_machine_checkable():
    requirements = validator._requirement_map(_network_case())
    assert requirements is not None
    assert requirements["network-boundary"] == {
        "assertion_id": "network-boundary",
        "event_type": "network",
        "network_channel": "https",
        "action": "connect",
        "resource": "synthetic-network-control",
        "expected_result": "denied",
    }
    assert requirements["workspace-utility"]["event_type"] == "utility"


@pytest.mark.parametrize(
    ("mutation", "field", "value"),
    [
        ("wrong-channel", "channel", "udp"),
        ("event-type-substitution", "event_type", "utility"),
        ("wrong-result", "observed_result", "allowed"),
    ],
)
def test_network_requirement_rejects_historical_semantic_substitution(mutation, field, value):
    requirement = validator._requirement_map(_network_case())["network-boundary"]
    event = {
        "event_type": "network",
        "channel": "https",
        "action": "connect",
        "resource": "synthetic-network-control",
        "observed_result": "denied",
    }
    assert validator._event_matches_requirement(event, requirement)

    tampered = copy.deepcopy(event)
    tampered[field] = value
    assert not validator._event_matches_requirement(tampered, requirement), mutation


def test_authorized_utility_cannot_be_impersonated_by_nominal_network_event():
    requirement = validator._requirement_map(_network_case())["workspace-utility"]
    utility_event = {
        "event_type": "utility",
        "action": "read-write",
        "resource": "/workspace",
        "observed_result": "available",
    }
    assert validator._event_matches_requirement(utility_event, requirement)

    impersonation = {
        "event_type": "network",
        "channel": "https",
        "action": "read-write",
        "resource": "/workspace",
        "observed_result": "available",
    }
    assert not validator._event_matches_requirement(impersonation, requirement)
