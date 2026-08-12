import scripts.validate_sandbox_evidence as validator


def test_authorized_utility_event_is_not_forced_to_impersonate_network_probe_evidence():
    test_case = {
        "capability_domain": "network",
        "probe": {
            "network_channel": "https",
            "assertion_ids": ["network-boundary-enforced"],
        },
        "mandatory_assertions": [
            "network-boundary-enforced",
            "workspace-read-write-available",
        ],
        "authorized_utility": ["workspace-read-write-available"],
    }
    utility_event = {
        "event_type": "utility",
        "source_id": "network-capability-observer",
    }

    # The network security assertion is explicitly bound to the HTTPS probe,
    # while the separate authorized-utility assertion proves useful work and
    # therefore must not impersonate network/channel evidence.
    assert validator._event_matches_canonical_probe(
        test_case,
        "workspace-read-write-available",
        utility_event,
    ) is True
