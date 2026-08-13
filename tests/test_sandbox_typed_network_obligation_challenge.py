import copy

import pytest

from scripts.validate_sandbox_evidence import _event_matches_requirement


def _network_requirement():
    return {
        "assertion_id": "network-boundary",
        "event_type": "network",
        "network_channel": "https",
        "action": "connect",
        "resource": "synthetic-network-control",
        "expected_result": "denied",
    }


def _network_event():
    return {
        "event_type": "network",
        "channel": "https",
        "action": "connect",
        "resource": "synthetic-network-control",
        "observed_result": "denied",
    }


@pytest.mark.parametrize(
    ("mutation", "field", "value"),
    [
        ("wrong-channel", "channel", "udp"),
        ("event-type-substitution", "event_type", "utility"),
        ("wrong-result", "observed_result", "allowed"),
    ],
)
def test_network_requirement_rejects_historical_semantic_substitution(mutation, field, value):
    requirement = _network_requirement()
    event = _network_event()
    assert _event_matches_requirement(event, requirement)

    tampered = copy.deepcopy(event)
    tampered[field] = value
    assert not _event_matches_requirement(tampered, requirement), mutation


def test_authorized_utility_cannot_be_impersonated_by_nominal_network_event():
    requirement = {
        "assertion_id": "workspace-utility",
        "event_type": "utility",
        "action": "read-write",
        "resource": "/workspace",
        "expected_result": "available",
    }
    utility_event = {
        "event_type": "utility",
        "action": "read-write",
        "resource": "/workspace",
        "observed_result": "available",
    }
    assert _event_matches_requirement(utility_event, requirement)

    impersonation = {
        "event_type": "network",
        "channel": "https",
        "action": "read-write",
        "resource": "/workspace",
        "observed_result": "available",
    }
    assert not _event_matches_requirement(impersonation, requirement)
