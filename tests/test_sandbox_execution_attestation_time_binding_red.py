import copy
import json
from pathlib import Path

from scripts.execution_attestation import execution_attestation_valid

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_execution_attestation_binds_process_observation_ordering_fields():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    process_event = next(event for event in document["events"] if event["event_type"] == "process")
    binding_id = process_event["event_id"]
    source_id = process_event["source_id"]

    assert execution_attestation_valid(document, binding_id, source_id) is True

    tampered = copy.deepcopy(document)
    tampered_process = next(event for event in tampered["events"] if event["event_id"] == binding_id)
    tampered_process["occurred_at_utc"] = "2000-01-01T00:00:00Z"
    tampered_process["monotonic_ns"] = 1

    # The validator uses this process event's wall-clock/monotonic ordering to
    # establish that exact-probe execution preceded assertion evidence. Those
    # ordering fields are producer-controlled today and are not part of the
    # signed ExecutionAttestation payload. A valid external receipt must not
    # remain valid after provenance-critical ordering is rewritten.
    assert execution_attestation_valid(tampered, binding_id, source_id) is False
