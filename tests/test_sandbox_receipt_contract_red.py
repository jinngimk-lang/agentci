from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import secrets
from typing import Any, Callable

import pytest

from scripts import validate_sandbox_evidence as evidence_validator


ROOT = Path(__file__).resolve().parents[1]
PASS_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"
FAIL_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
TEST_CASE = ROOT / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"
RUNTIME_DIR = ROOT / "examples" / "sandbox" / "runtime-environment-attestations"
EXECUTION_DIR = ROOT / "examples" / "sandbox" / "execution-attestations"
ALGORITHM = "rsa-pkcs1v15-sha256"
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _probable_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if candidate % prime == 0:
            return candidate == prime
    exponent, shifts = candidate - 1, 0
    while exponent % 2 == 0:
        exponent //= 2
        shifts += 1
    for base in (2, 3, 5, 7, 11, 13, 17):
        witness = pow(base, exponent, candidate)
        if witness in (1, candidate - 1):
            continue
        for _ in range(shifts - 1):
            witness = pow(witness, 2, candidate)
            if witness == candidate - 1:
                break
        else:
            return False
    return True


def _prime(bits: int = 384) -> int:
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if _probable_prime(candidate):
            return candidate


def _keypair() -> tuple[dict[str, int | str], tuple[int, int]]:
    exponent = 65537
    while True:
        p, q = _prime(), _prime()
        if p != q and math.gcd(exponent, (p - 1) * (q - 1)) == 1:
            break
    modulus = p * q
    private_exponent = pow(exponent, -1, (p - 1) * (q - 1))
    return {"modulus_hex": format(modulus, "x"), "exponent": exponent}, (modulus, private_exponent)


def _sign(payload: dict[str, Any], private_key: tuple[int, int]) -> dict[str, Any]:
    signed = copy.deepcopy(payload)
    modulus, private_exponent = private_key
    size = (modulus.bit_length() + 7) // 8
    digest_info = _DIGEST_INFO_PREFIX + hashlib.sha256(_canonical_bytes(signed)).digest()
    encoded = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), private_exponent, modulus).to_bytes(size, "big")
    signed["signature_b64"] = base64.b64encode(signature).decode()
    return signed


def _resign(sidecar: dict[str, Any], private_key: tuple[int, int]) -> dict[str, Any]:
    payload = copy.deepcopy(sidecar)
    payload.pop("signature_b64", None)
    return _sign(payload, private_key)


def _typed_test_case() -> dict[str, Any]:
    test_case = json.loads(TEST_CASE.read_text(encoding="utf-8"))
    test_case["cleanup_requirements"] = [
        {
            "requirement_id": "cleanup-descendants",
            "dimension": "descendants",
            "expected_state": "clean",
            "event_type": "cleanup",
            "expected_result": "clean",
        },
        {
            "requirement_id": "cleanup-filesystem-residue",
            "dimension": "filesystem_residue",
            "expected_state": "clean",
            "event_type": "cleanup",
            "expected_result": "clean",
        },
    ]
    return test_case


def _add_cleanup_events(document: dict[str, Any], test_case: dict[str, Any]) -> None:
    binding = document["assertions"][0]["evidence_event_ids"][0].split(":event-", 1)[0]
    for offset, requirement in enumerate(test_case["cleanup_requirements"], start=1):
        event = {
            "event_id": f"{binding}:event-{requirement['requirement_id']}",
            "event_type": "cleanup",
            "occurred_at_utc": f"2026-08-11T03:00:0{offset + 1}Z",
            "monotonic_ns": 3000 + offset,
            "policy_epoch": document["policy_history"][-1]["policy_epoch"],
            "authority_epoch": document["policy_history"][-1]["authority_epoch"],
            "source_id": "fixture-policy-observer",
            "workload_identity": "fixture-workload",
            "attachment_id": "attach-1",
            "action": "verify-cleanup",
            "resource": requirement["dimension"],
            "observed_result": "clean",
        }
        event["semantic_digest"] = evidence_validator.event_semantic_digest(event)
        document["events"].append(event)


def _observer_projection(document: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    event_bindings = sorted(
        (
            {"event_id": event["event_id"], "semantic_digest": event["semantic_digest"]}
            for event in document["events"]
            if event["source_id"] == source["source_id"]
        ),
        key=lambda item: item["event_id"],
    )
    events = [event for event in document["events"] if event["source_id"] == source["source_id"]]
    return {
        "apiVersion": "agentci.dev/sandbox-observer-attestation/v0alpha1",
        "kind": "ObserverAttestation",
        "attester_id": "fixture-observer-attester",
        "trust_epoch": 1,
        "run_id": document["run_id"],
        "case_id": document["case_id"],
        "attempt": document["attempt"],
        "evidence_artifact_digest": evidence_validator.artifact_digest(document),
        "test_case_digest": _digest(_typed_test_case()),
        "backend_instance": document["backend"]["effective_backend_instance"],
        "environment_fingerprint": document["environment_fingerprint"],
        "policy_history_digest": document["policy_history_digest"],
        "authority_digest": document["authority_digest"],
        "telemetry_source": copy.deepcopy(source),
        "observation_window": {
            "opened_at_utc": min(event["occurred_at_utc"] for event in events),
            "opened_at_monotonic_ns": min(event["monotonic_ns"] for event in events),
            "closed_at_utc": max(event["occurred_at_utc"] for event in events),
            "closed_at_monotonic_ns": max(event["monotonic_ns"] for event in events),
        },
        "event_bindings": event_bindings,
        "event_set_digest": _digest(event_bindings),
        "key_id": "ephemeral-observer-key",
        "algorithm": ALGORITHM,
    }


def _cleanup_projection(document: dict[str, Any], test_case: dict[str, Any]) -> dict[str, Any]:
    results = []
    for requirement in test_case["cleanup_requirements"]:
        event_ids = sorted(
            event["event_id"]
            for event in document["events"]
            if event["event_type"] == requirement["event_type"]
            and event.get("resource") == requirement["dimension"]
            and event.get("observed_result") == requirement["expected_result"]
        )
        results.append(
            {
                "requirement_id": requirement["requirement_id"],
                "dimension": requirement["dimension"],
                "state": document["post_conditions"][requirement["dimension"]],
                "event_ids": event_ids,
                "result_set_digest": _digest(event_ids),
            }
        )
    return {
        "apiVersion": "agentci.dev/sandbox-cleanup-attestation/v0alpha1",
        "kind": "CleanupAttestation",
        "attester_id": "fixture-cleanup-attester",
        "trust_epoch": 1,
        "run_id": document["run_id"],
        "case_id": document["case_id"],
        "attempt": document["attempt"],
        "evidence_artifact_digest": evidence_validator.artifact_digest(document),
        "test_case_digest": _digest(test_case),
        "backend_instance": document["backend"]["effective_backend_instance"],
        "environment_fingerprint": document["environment_fingerprint"],
        "policy_history_digest": document["policy_history_digest"],
        "authority_digest": document["authority_digest"],
        "requirement_results": results,
        "key_id": "ephemeral-cleanup-key",
        "algorithm": ALGORITHM,
    }


def _inventory_item(role: str, artifact: dict[str, Any], *, content: bytes | None = None) -> dict[str, Any]:
    payload = copy.deepcopy(artifact)
    payload.pop("signature_b64", None)
    content_bytes = content if content is not None else _canonical_bytes(artifact)
    return {
        "role": role,
        "content_digest": "sha256:" + hashlib.sha256(content_bytes).hexdigest(),
        "payload_digest": _digest(payload),
        "signature_verified": role in {"runtime", "execution", "cleanup"}
        or role.startswith("observer:"),
    }


def _complete_bundle(evidence_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    document = json.loads(evidence_path.read_text(encoding="utf-8"))
    test_case = _typed_test_case()
    _add_cleanup_events(document, test_case)
    document["authority_digest"] = evidence_validator.authority_binding_digest(document)
    document["canonicalization"]["artifact_digest"] = evidence_validator.artifact_digest(document)
    observer_public, observer_private = _keypair()
    cleanup_public, cleanup_private = _keypair()
    observers = [
        _sign(_observer_projection(document, source), observer_private)
        for source in document["telemetry"]
        if source["coverage"] == "mandatory"
    ]
    cleanup = _sign(_cleanup_projection(document, test_case), cleanup_private)
    runtime = json.loads((RUNTIME_DIR / f"{document['run_id']}.json").read_text(encoding="utf-8"))
    execution = json.loads((EXECUTION_DIR / f"{document['run_id']}.json").read_text(encoding="utf-8"))
    inventory = [
        _inventory_item("evidence", document),
        _inventory_item("test_case", test_case),
        _inventory_item("runtime", runtime),
        _inventory_item("execution", execution),
        *[
            _inventory_item(f"observer:{observer['telemetry_source']['source_id']}", observer)
            for observer in observers
        ],
        _inventory_item("cleanup", cleanup),
    ]
    bundle = {
        "test_case": test_case,
        "observer_attestations": observers,
        "cleanup_attestation": cleanup,
        "artifact_inventory": inventory,
        "trusted_observers": {
            "fixture-observer-attester": {
                **observer_public,
                "trust_epoch": 1,
                "key_id": "ephemeral-observer-key",
                "algorithm": ALGORITHM,
            }
        },
        "trusted_cleanup_attesters": {
            "fixture-cleanup-attester": {
                **cleanup_public,
                "trust_epoch": 1,
                "key_id": "ephemeral-cleanup-key",
                "algorithm": ALGORITHM,
            }
        },
        "_observer_private": observer_private,
        "_cleanup_private": cleanup_private,
    }
    return document, bundle


def _assemble(document: dict[str, Any], bundle: dict[str, Any]):
    from agentci.sandbox.receipt import assemble_receipt

    return assemble_receipt(
        document,
        test_case=bundle["test_case"],
        observer_attestations=bundle["observer_attestations"],
        cleanup_attestation=bundle["cleanup_attestation"],
        artifact_inventory=bundle["artifact_inventory"],
        trusted_observers=bundle["trusted_observers"],
        trusted_cleanup_attesters=bundle["trusted_cleanup_attesters"],
    )


def _success(document: dict[str, Any], bundle: dict[str, Any]):
    result = _assemble(document, bundle)
    assert result.evidence_valid is True
    assert result.receipt_valid is True
    assert result.error_codes == ()
    assert result.manifest["apiVersion"] == "agentci.dev/sandbox-verification-receipt/v0alpha1"
    assert result.manifest["kind"] == "EvidenceVerificationReceiptManifest"
    assert result.manifest["run_id"] == document["run_id"]
    assert result.manifest["evidence_artifact_digest"] == evidence_validator.artifact_digest(document)
    assert result.manifest["recorded_verdict"] == document["verdict"]
    assert result.manifest["expected_verdict"] == evidence_validator.expected_verdict(document)
    assert result.manifest["certification_claim"] is False
    assert result.manifest["artifact_inventory"] == bundle["artifact_inventory"]
    assert result.manifest["manifest_digest"].startswith("sha256:")
    return result


def _attack(
    code: str,
    mutate: Callable[[dict[str, Any], dict[str, Any]], None],
    *,
    evidence_path: Path = PASS_EVIDENCE,
):
    document, bundle = _complete_bundle(evidence_path)
    _success(document, bundle)
    attacked_document, attacked_bundle = copy.deepcopy(document), copy.deepcopy(bundle)
    mutate(attacked_document, attacked_bundle)
    result = _assemble(attacked_document, attacked_bundle)
    assert result.evidence_valid is True
    assert result.receipt_valid is False
    assert result.error_codes == (code,)
    assert result.manifest is None
    _success(document, bundle)


def test_complete_pass_bundle_assembles_literal_content_addressed_manifest():
    document, bundle = _complete_bundle(PASS_EVIDENCE)
    _success(document, bundle)


def test_complete_valid_fail_bundle_preserves_fail_and_non_certification():
    document, bundle = _complete_bundle(FAIL_EVIDENCE)
    result = _success(document, bundle)
    assert result.manifest["recorded_verdict"] == "FAIL"
    assert result.manifest["expected_verdict"] == "FAIL"
    assert result.manifest["certification_claim"] is False


def test_duplicate_observer_is_rejected():
    def mutate(_document, bundle):
        bundle["observer_attestations"].append(copy.deepcopy(bundle["observer_attestations"][0]))

    _attack("E_RECEIPT_DUPLICATE_OBSERVER_BINDING", mutate)


def test_event_addition_outside_signed_event_set_is_rejected():
    def mutate(document, _bundle):
        event = copy.deepcopy(document["events"][0])
        event["event_id"] += "-added"
        event["semantic_digest"] = evidence_validator.event_semantic_digest(event)
        document["events"].append(event)
        document["canonicalization"]["artifact_digest"] = evidence_validator.artifact_digest(document)

    _attack("E_RECEIPT_OBSERVER_EVENT_SET_MISMATCH", mutate)


def test_unknown_event_reference_in_signed_observer_is_rejected():
    def mutate(_document, bundle):
        sidecar = bundle["observer_attestations"][0]
        sidecar["event_bindings"][0]["event_id"] = "unknown-event"
        sidecar["event_set_digest"] = _digest(sidecar["event_bindings"])
        bundle["observer_attestations"][0] = _resign(sidecar, bundle["_observer_private"])

    _attack("E_RECEIPT_OBSERVER_UNKNOWN_EVENT", mutate)


def test_missing_mandatory_observer_is_rejected():
    def mutate(_document, bundle):
        bundle["observer_attestations"].pop()

    _attack("E_RECEIPT_MISSING_OBSERVER_BINDING", mutate)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("evidence_artifact_digest", "sha256:" + "6" * 64, "E_RECEIPT_OBSERVER_EVIDENCE_MISMATCH"),
        ("test_case_digest", "sha256:" + "5" * 64, "E_RECEIPT_OBSERVER_TEST_CASE_MISMATCH"),
    ],
)
def test_observer_evidence_and_test_case_scope_is_rejected(field: str, value: str, code: str):
    def mutate(_document, bundle):
        sidecar = bundle["observer_attestations"][0]
        sidecar[field] = value
        bundle["observer_attestations"][0] = _resign(sidecar, bundle["_observer_private"])

    _attack(code, mutate)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("run_id", "other-run", "E_RECEIPT_OBSERVER_RUN_MISMATCH"),
        ("case_id", "other-case", "E_RECEIPT_OBSERVER_CASE_MISMATCH"),
        ("attempt", 2, "E_RECEIPT_OBSERVER_ATTEMPT_MISMATCH"),
        ("backend_instance", "other-backend", "E_RECEIPT_OBSERVER_BACKEND_MISMATCH"),
        ("environment_fingerprint", "sha256:" + "9" * 64, "E_RECEIPT_OBSERVER_ENVIRONMENT_MISMATCH"),
        ("policy_history_digest", "sha256:" + "8" * 64, "E_RECEIPT_OBSERVER_POLICY_MISMATCH"),
        ("authority_digest", "sha256:" + "7" * 64, "E_RECEIPT_OBSERVER_AUTHORITY_MISMATCH"),
    ],
)
def test_observer_scope_cross_binding_is_rejected(field: str, value: Any, code: str):
    def mutate(_document, bundle):
        sidecar = bundle["observer_attestations"][0]
        sidecar[field] = value
        bundle["observer_attestations"][0] = _resign(sidecar, bundle["_observer_private"])

    _attack(code, mutate)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("open", "E_RECEIPT_OBSERVER_WINDOW_OPEN"),
        ("reversed", "E_RECEIPT_OBSERVER_WINDOW_REVERSED"),
        ("gap", "E_RECEIPT_OBSERVER_WINDOW_COVERAGE_GAP"),
    ],
)
def test_observation_window_must_be_closed_ordered_and_cover_events(mutation: str, code: str):
    def mutate(_document, bundle):
        sidecar = bundle["observer_attestations"][0]
        window = sidecar["observation_window"]
        if mutation == "open":
            window["closed_at_utc"] = None
            window["closed_at_monotonic_ns"] = None
        elif mutation == "reversed":
            window["closed_at_monotonic_ns"] = window["opened_at_monotonic_ns"] - 1
        else:
            window["opened_at_monotonic_ns"] += 1
        bundle["observer_attestations"][0] = _resign(sidecar, bundle["_observer_private"])

    _attack(code, mutate)


def test_in_scope_not_applicable_cleanup_state_is_rejected():
    def mutate(document, bundle):
        document["post_conditions"]["descendants"] = "not-applicable"
        document["canonicalization"]["artifact_digest"] = evidence_validator.artifact_digest(document)
        result = bundle["cleanup_attestation"]["requirement_results"][0]
        result["state"] = "not-applicable"
        bundle["cleanup_attestation"] = _resign(result and bundle["cleanup_attestation"], bundle["_cleanup_private"])

    _attack("E_RECEIPT_CLEANUP_IN_SCOPE_NOT_APPLICABLE", mutate)


def test_missing_cleanup_binding_is_rejected():
    def mutate(_document, bundle):
        bundle["cleanup_attestation"] = None

    _attack("E_RECEIPT_MISSING_CLEANUP_BINDING", mutate)


def test_cleanup_requirement_omission_is_rejected():
    def mutate(_document, bundle):
        sidecar = bundle["cleanup_attestation"]
        sidecar["requirement_results"].pop()
        bundle["cleanup_attestation"] = _resign(sidecar, bundle["_cleanup_private"])

    _attack("E_RECEIPT_CLEANUP_REQUIREMENT_MISSING", mutate)


def test_cleanup_unknown_event_reference_is_rejected():
    def mutate(_document, bundle):
        sidecar = bundle["cleanup_attestation"]
        result = sidecar["requirement_results"][0]
        result["event_ids"] = ["unknown-cleanup-event"]
        result["result_set_digest"] = _digest(result["event_ids"])
        bundle["cleanup_attestation"] = _resign(sidecar, bundle["_cleanup_private"])

    _attack("E_RECEIPT_CLEANUP_UNKNOWN_EVENT", mutate)


def test_cleanup_result_set_digest_tamper_is_rejected():
    def mutate(_document, bundle):
        sidecar = bundle["cleanup_attestation"]
        sidecar["requirement_results"][0]["result_set_digest"] = "sha256:" + "0" * 64
        bundle["cleanup_attestation"] = _resign(sidecar, bundle["_cleanup_private"])

    _attack("E_RECEIPT_CLEANUP_RESULT_SET_MISMATCH", mutate)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("run_id", "other-run", "E_RECEIPT_CLEANUP_RUN_MISMATCH"),
        ("case_id", "other-case", "E_RECEIPT_CLEANUP_CASE_MISMATCH"),
        ("attempt", 2, "E_RECEIPT_CLEANUP_ATTEMPT_MISMATCH"),
        ("backend_instance", "other-backend", "E_RECEIPT_CLEANUP_BACKEND_MISMATCH"),
        ("environment_fingerprint", "sha256:" + "4" * 64, "E_RECEIPT_CLEANUP_ENVIRONMENT_MISMATCH"),
        ("policy_history_digest", "sha256:" + "3" * 64, "E_RECEIPT_CLEANUP_POLICY_MISMATCH"),
        ("authority_digest", "sha256:" + "2" * 64, "E_RECEIPT_CLEANUP_AUTHORITY_MISMATCH"),
        ("evidence_artifact_digest", "sha256:" + "1" * 64, "E_RECEIPT_CLEANUP_EVIDENCE_MISMATCH"),
        ("test_case_digest", "sha256:" + "a" * 64, "E_RECEIPT_CLEANUP_TEST_CASE_MISMATCH"),
    ],
)
def test_cleanup_scope_cross_binding_is_rejected(field: str, value: Any, code: str):
    def mutate(_document, bundle):
        sidecar = bundle["cleanup_attestation"]
        sidecar[field] = value
        bundle["cleanup_attestation"] = _resign(sidecar, bundle["_cleanup_private"])

    _attack(code, mutate)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("missing", "E_RECEIPT_INVENTORY_ROLE_MISSING"),
        ("duplicate", "E_RECEIPT_INVENTORY_ROLE_DUPLICATE"),
        ("digest", "E_RECEIPT_INVENTORY_DIGEST_MISMATCH"),
    ],
)
def test_artifact_inventory_is_complete_unique_and_content_addressed(mutation: str, code: str):
    def mutate(_document, bundle):
        if mutation == "missing":
            bundle["artifact_inventory"] = [
                item for item in bundle["artifact_inventory"] if item["role"] != "cleanup"
            ]
        elif mutation == "duplicate":
            evidence_item = next(item for item in bundle["artifact_inventory"] if item["role"] == "evidence")
            bundle["artifact_inventory"].append(copy.deepcopy(evidence_item))
        else:
            bundle["artifact_inventory"][0]["content_digest"] = "sha256:" + "0" * 64

    _attack(code, mutate)


def test_public_replay_revalidates_manifest_digest_and_inventory():
    from agentci.sandbox.receipt import validate_receipt_manifest

    document, bundle = _complete_bundle(PASS_EVIDENCE)
    manifest = _success(document, bundle).manifest
    assert validate_receipt_manifest(manifest).valid is True
    tampered = copy.deepcopy(manifest)
    tampered["artifact_inventory"][0]["payload_digest"] = "sha256:" + "0" * 64
    replay = validate_receipt_manifest(tampered)
    assert replay.valid is False
    assert replay.error_codes == ("E_RECEIPT_INVENTORY_DIGEST_MISMATCH",)
