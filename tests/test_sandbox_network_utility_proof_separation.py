import scripts.validate_sandbox_evidence as validator


def test_authorized_utility_event_is_not_forced_to_impersonate_network_probe_evidence():
    test_case = {
        "capability_domain": "network",
        "probe": {"network_channel": "https"},
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

    # The network security assertion still requires typed HTTPS evidence, but
    # the separate authorized-utility assertion proves useful work rather than
    # the transport channel itself. Role separation must not force every
    # evidence event in a network TestCase to become a network/channel event.
    assert validator._event_matches_canonical_probe(
        test_case,
        "workspace-read-write-available",
        utility_event,
    ) is True
