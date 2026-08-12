"""S0 stand-in for authenticated runner/collector execution provenance.

The EvidenceEnvelope is intentionally not the trust root. A signed sidecar is
loaded from a separate channel and verified against a validator-pinned public
key. This models the minimum authenticity property required by the S0 contract
without claiming a released provider attestation service.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_DIR = ROOT / "examples" / "sandbox" / "execution-attestations"
ALGORITHM = "rsa-pkcs1v15-sha256"

# Public verification material only. The private signing key is not stored in
# this repository and is not derivable from EvidenceEnvelope fields.
TRUSTED_RSA_KEYS = {
    "fixture-runner-key-v1": {
        "modulus_hex": "9f5ce794d6b9b06f49e064ef42fc3c0ae032a913e34c76233160804e5bd3878654208c4937423df7e9d2ab277c4818c830f215d971cc3a256ed09fe86416a476f1b3d3e75fe26f895812080585c17fd260027da604b1bbe116df7f3921db6e657736271cb5fac2a94ec7ea443956101701f380c87abf6535b1082df9b956ce2b6254e987f2a5dfb37df63e2cdf0d5c3dd6066f54f644de6f1e3b989a6ecd3b0c1f73dab29241a09231175459613f34df869db2236023a2e68a03975381d14bf722704917c2c78167a63bbbfb8fbbb1a702d08abbb679ce8cf07d0ff8dfa8d581f03421bfbd68927ea101929d27ef7cbf8ed07ac98dfa8a748d47a4fcb1cbbdff",
        "exponent": 65537,
    }
}

_SHA256_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _safe_token(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "/" in value or "\\" in value or value in {".", ".."}:
        return None
    return value


def _rsa_pkcs1v15_sha256_verify(message: bytes, signature_b64: Any, key: dict[str, Any]) -> bool:
    if not isinstance(signature_b64, str):
        return False
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        modulus = int(key["modulus_hex"], 16)
        exponent = int(key["exponent"])
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


def execution_attestation_valid(document: dict[str, Any], binding_id: str, source_id: Any) -> bool:
    """Verify one execution binding against provenance outside the envelope."""
    run_id = _safe_token(document.get("run_id"))
    case_id = _safe_token(document.get("case_id"))
    if run_id is None or case_id is None or not isinstance(source_id, str):
        return False
    path = ATTESTATION_DIR / f"{run_id}.json"
    if not path.is_file():
        return False
    try:
        attestation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(attestation, dict):
        return False
    payload = {
        "run_id": run_id,
        "case_id": case_id,
        "attempt": document.get("attempt"),
        "execution_binding": binding_id,
        "source_id": source_id,
        "key_id": attestation.get("key_id"),
        "algorithm": attestation.get("algorithm"),
    }
    for field, expected in payload.items():
        if attestation.get(field) != expected:
            return False
    if attestation.get("algorithm") != ALGORITHM:
        return False
    key = TRUSTED_RSA_KEYS.get(attestation.get("key_id"))
    if key is None:
        return False
    return _rsa_pkcs1v15_sha256_verify(_canonical_bytes(payload), attestation.get("signature_b64"), key)
