import copy
import json
from pathlib import Path

import scripts.validate_sandbox_evidence as validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def _rebind(document):
    for event in document.get("events", []):
        event["semantic_digest"] = validator.event_semantic_digest(event)
    for attachment in document.get("policy_attachments", []):
        attachment_event = next(
            event
            for event in document.get("events", [])
            if event.get("event_type") == "policy-attachment"
            and event.get("attachment_id") == attachment.get("attachment_id")
        )
        attachment["evidence_digest"] = attachment_event["semantic_digest"]
    document["policy_history_digest"] = validator.policy_history_digest(document)
    document["authority_digest"] = validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = validator.artifact_digest(document)
    return document


def test_signed_execution_attestation_cannot_replay_across_changed_authority_semantics():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    # Make the deliberately permissive red-control envelope nominally PASS while
    # retaining the exact canonical probe/run context covered by the signed
    # execution-attestation fixture.
    document["assertions"][0]["state"] = "PASS"
    document["verdict"] = "PASS"
    _rebind(document)
    assert validator.expected_verdict(copy.deepcopy(document)) == "PASS"

    # Rewrite the authority source at the same numeric authority/policy epochs.
    # A producer can recompute every envelope-local digest, but cannot obtain a
    # fresh runner signature. Replaying the old attestation must therefore not
    # certify execution under this changed authority context.
    document["policy_history"][0]["source_principal_id"] = "different-authority-principal"
    _rebind(document)

    assert validator.expected_verdict(document) != "PASS"
