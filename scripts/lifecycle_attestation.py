"""S0 stand-in for authenticated lifecycle/snapshot provenance.

The EvidenceEnvelope is not the trust root. A signed sidecar binds one observed
restore event to the exact snapshot identity and run/backend/environment scope.
This proves only the bounded S0 evidence-authenticity property; it is not
provider-native snapshot attestation or a sandbox security verdict.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_DIR = ROOT / "examples" / "sandbox" / "lifecycle-attestations"
ALGORITHM = "rsa-pkcs1v15-sha256"

TRUSTED_ATTESTERS = {
    "fixture-lifecycle-observer": {
        "trust_epoch": 1,
        "key_id": "fixture-lifecycle-key-v1",
        "modulus_hex": "af3a870794dda6f4ce58f422680fef9b08adb7f38233d1faa761ff635b0c4c7b1c85483451e72ef1c28c4485cffb0c886f48157b394838fe6fc0e10adb018a608759d6fa25392205d8b467a77caaaa2886e6c201f15d4ef24b5f7b82e3fc3a439d897d1b907c9c496f1534820755909fa62fe294a098486f793590e913842e3ff169e3d6610ebf5d2f516f7ea9b9040e94306f8872bdaeb57605bf02813a9a812d76dec62424705bad1cc655507dba9da35833409133b15fb8272862112de8968ff53247aff35c9442a8786636adbe35e6cab07e8b59e310fcb070270b8c94917526d3aa12edb5d40c6d5226070fa24c9e0aab0562dd06e946340811433b77f1",
        "exponent": 65537,
        "backend_instance": "red-control-1",
        "environment_fingerprint": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }
}

_SHA256_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _safe_token(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "/" in value or "\\" in value or value in {".", ".."}:
        return None
    return value


def _rsa_pkcs1v15_sha256_verify(message: bytes, signature_b64: Any, trust: dict[str, Any]) -> bool:
    if not isinstance(signature_b64, str):
        return False
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        modulus = int(trust["modulus_hex"], 16)
        exponent = int(trust["exponent"])
    except (ValueError, TypeError, KeyError):
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    encoded = pow(int.from_bytes(signature, "big"), exponent, modulus).to_bytes(size, "big")
    digest_info = _SHA256_DIGEST_INFO_PREFIX + hashlib.sha256(message).digest()
    padding_len = size - len(digest_info) - 3
    if padding_len < 8:
        return False
    expected = b"\x00\x01" + (b"\xff" * padding_len) + b"\x00" + digest_info
    return encoded == expected


def lifecycle_attestation_valid(document: dict[str, Any], continuity: dict[str, Any], event: dict[str, Any]) -> bool:
    """Verify one exact snapshot/restore observation outside envelope-local integrity."""
    run_id = _safe_token(document.get("run_id"))
    case_id = _safe_token(document.get("case_id"))
    restore_epoch = continuity.get("restore_epoch")
    if run_id is None or case_id is None or not isinstance(restore_epoch, int) or restore_epoch < 0:
        return False
    if event.get("event_type") != "lifecycle" or event.get("restore_epoch") != restore_epoch:
        return False

    path = ATTESTATION_DIR / f"{run_id}-{restore_epoch}.json"
    if not path.is_file():
        return False
    try:
        attestation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(attestation, dict):
        return False

    attester_id = attestation.get("attester_id")
    trust = TRUSTED_ATTESTERS.get(attester_id)
    if trust is None or attestation.get("trust_epoch") != trust.get("trust_epoch"):
        return False
    if attestation.get("key_id") != trust.get("key_id") or attestation.get("algorithm") != ALGORITHM:
        return False

    backend = document.get("backend")
    if not isinstance(backend, dict):
        return False
    environment_fingerprint = document.get("environment_fingerprint")
    payload = {
        "attestation_id": attestation.get("attestation_id"),
        "attester_id": attester_id,
        "trust_epoch": attestation.get("trust_epoch"),
        "run_id": run_id,
        "case_id": case_id,
        "attempt": document.get("attempt"),
        "event_id": event.get("event_id"),
        "source_id": event.get("source_id"),
        "snapshot_id": continuity.get("snapshot_id"),
        "capture_epoch": continuity.get("capture_epoch"),
        "restore_epoch": restore_epoch,
        "workload_identity": event.get("workload_identity"),
        "policy_epoch": event.get("policy_epoch"),
        "authority_epoch": event.get("authority_epoch"),
        "attachment_id": event.get("attachment_id"),
        "occurred_at_utc": event.get("occurred_at_utc"),
        "monotonic_ns": event.get("monotonic_ns"),
        "backend_instance": backend.get("effective_backend_instance"),
        "environment_fingerprint": environment_fingerprint,
        "key_id": attestation.get("key_id"),
        "algorithm": attestation.get("algorithm"),
    }
    for field, expected in payload.items():
        if attestation.get(field) != expected:
            return False

    if event.get("source_id") != attester_id:
        return False
    if payload["backend_instance"] != trust.get("backend_instance"):
        return False
    if environment_fingerprint != trust.get("environment_fingerprint"):
        return False

    return _rsa_pkcs1v15_sha256_verify(_canonical_bytes(payload), attestation.get("signature_b64"), trust)
