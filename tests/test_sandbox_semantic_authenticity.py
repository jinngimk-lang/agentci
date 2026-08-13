import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as evidence
from scripts.execution_attestation import TRUSTED_RSA_KEYS, execution_attestation_valid
from scripts.runtime_environment_attestation import TRUSTED_ATTESTERS

ROOT = Path(__file__).resolve().parents[1]
RED_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
PASS_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def test_execution_attestation_does_not_authenticate_authority_references():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    process_event = next(item for item in document["events"] if item["event_type"] == "process")
    assert execution_attestation_valid(document, process_event["event_id"], process_event["source_id"])

    tampered = copy.deepcopy(document)
    event = next(item for item in tampered["events"] if item.get("resource") == "/synthetic-sensitive-canary")
    event["decision_id"] = "authority-decision-is-out-of-scope"
    event["receipt_id"] = "authority-receipt-is-out-of-scope"
    event["semantic_digest"] = evidence.event_semantic_digest(event)

    assert execution_attestation_valid(tampered, process_event["event_id"], process_event["source_id"])


def test_genuine_denied_observation_is_a_valid_pass_fixture():
    document = json.loads(PASS_FIXTURE.read_text(encoding="utf-8"))
    event = next(item for item in document["events"] if item.get("resource") == "/synthetic-sensitive-canary")

    assert event["observed_result"] == "denied"
    assert evidence.expected_verdict(document) == "PASS"
    assert evidence.validate(document) == []


def test_execution_and_runtime_fixture_trust_domains_use_distinct_keys():
    execution_key = TRUSTED_RSA_KEYS["fixture-runner-key-v4"]
    runtime_key = TRUSTED_ATTESTERS["fixture-pass-runtime-observer"]

    assert runtime_key["key_id"] != "fixture-runner-key-v4"
    assert runtime_key["modulus_hex"] != execution_key["modulus_hex"]
