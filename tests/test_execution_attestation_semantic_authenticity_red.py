import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as evidence
from scripts.execution_attestation import execution_attestation_valid

ROOT = Path(__file__).resolve().parents[1]
RED_FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_external_execution_attestation_covers_assertion_semantics():
    document = json.loads(RED_FIXTURE.read_text(encoding="utf-8"))
    process_event = next(item for item in document["events"] if item["event_type"] == "process")
    assert execution_attestation_valid(document, process_event["event_id"], process_event["source_id"])

    tampered = copy.deepcopy(document)
    event = next(item for item in tampered["events"] if item.get("resource") == "/synthetic-sensitive-canary")
    event["observed_result"] = "denied"
    event["semantic_digest"] = evidence.event_semantic_digest(event)

    assert not execution_attestation_valid(tampered, process_event["event_id"], process_event["source_id"])
