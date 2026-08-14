from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import validate_sandbox_evidence as evidence_validator
from tests.test_sandbox_receipt_contract_red import (
    PASS_EVIDENCE,
    _add_cleanup_events,
    _assemble,
    _complete_bundle,
    _inventory_item,
    _manifest_digest,
    _replay,
    _success,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mutation", ["monotonic_ns", "signature_shape"])
def test_assembly_rejects_malformed_cleanup_object_before_semantics_or_signature(mutation: str):
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    cleanup = bundle["cleanup_attestation"]
    if mutation == "monotonic_ns":
        cleanup["cleanup_events"][0]["monotonic_ns"] = "not-an-integer"
    else:
        cleanup["signature_b64"] = 7

    result = _assemble(document, bundle)
    assert result.evidence_valid is True
    assert result.receipt_valid is False
    assert result.error_codes == ("E_RECEIPT_OBJECT_SCHEMA_INVALID",)
    assert result.manifest is None


@pytest.mark.parametrize("mutation", ["monotonic_ns", "signature_shape"])
def test_replay_rejects_malformed_cleanup_object_before_semantics_or_signature(mutation: str):
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = copy.deepcopy(_success(document, bundle).manifest)
    artifact = next(item for item in manifest["artifacts"] if item["role"] == "cleanup")
    if mutation == "monotonic_ns":
        artifact["content"]["cleanup_events"][0]["monotonic_ns"] = "not-an-integer"
    else:
        artifact["content"]["signature_b64"] = 7
    replacement = _inventory_item("cleanup", artifact["content"])
    artifact.update(replacement)
    inventory = next(item for item in manifest["artifact_inventory"] if item["role"] == "cleanup")
    inventory.update(replacement)
    manifest["manifest_digest"] = _manifest_digest(manifest)

    replay = _replay(manifest, bundle)
    assert replay.valid is False
    assert replay.error_codes == ("E_RECEIPT_OBJECT_SCHEMA_INVALID",)


def test_legal_cleanup_event_changes_artifact_and_authority_binding_digests():
    document = json.loads(PASS_EVIDENCE.read_text(encoding="utf-8"))
    augmented = copy.deepcopy(document)
    test_case = json.loads(
        (ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json").read_text(
            encoding="utf-8"
        )
    )
    _add_cleanup_events(augmented, test_case)
    augmented["authority_digest"] = evidence_validator.authority_binding_digest(augmented)
    augmented["canonicalization"]["artifact_digest"] = evidence_validator.artifact_digest(augmented)
    assert evidence_validator.validate(augmented) == []

    assert evidence_validator.artifact_digest(document) != evidence_validator.artifact_digest(augmented)
    assert evidence_validator.authority_binding_digest(document) != evidence_validator.authority_binding_digest(
        augmented
    )


def test_artifact_digest_handles_non_object_event_after_validation_rejects_it():
    document = json.loads(PASS_EVIDENCE.read_text(encoding="utf-8"))
    document["events"].append("not-an-event-object")

    assert "schema validation failed" in evidence_validator.validate(document)
    assert evidence_validator.artifact_digest(document).startswith("sha256:")


def test_cli_print_digest_handles_non_object_event_without_traceback(tmp_path: Path):
    document = json.loads(PASS_EVIDENCE.read_text(encoding="utf-8"))
    document["events"].append("not-an-event-object")
    evidence = tmp_path / "malformed-event.json"
    evidence.write_text(json.dumps(document), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))

    completed = subprocess.run(
        [sys.executable, "-m", "agentci.cli", "sandbox", "verify", str(evidence), "--json", "--print-digest"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["valid"] is False
    assert "schema validation failed" in payload["errors"]
    assert payload["artifact_digest"].startswith("sha256:")
    assert "Traceback" not in completed.stderr
