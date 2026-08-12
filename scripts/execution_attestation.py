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
    "fixture-runner-key-v2": {
        "modulus_hex": "bfee16e846ba53691fe81c306df4faf3ef164db5d4798973336b09532d13c2bc8d1ee9337cc1fac88ad3287678b50f8b02538ab463e8ad1bd761c812b1f4664d169dbc7100c2149e45afa7d0a981f0cb6e306874cabe88129b60350f8bf14c64434c5ffb0892a395cc3f28483fe61aedf6a708007a842dc99656fb30c487e38e5a96b0a6ec806d09c8f76787768d26462545f0f2dd6461a8cb3c2f88a987f5fc3833bbaadf94e3e62796a08cd5211a56748eafc8e7b17fa898b00a302a62d9b53134ebb7f952d4851a6ee196ea55208b35615b339bd088603211fda294c0a69919e4bf5e3eb1021c7f85367ade7d82d66aedaabd4c09a631c087ba105f6766f7",
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

    matching_events = [
        event
        for event in document.get("events", [])
        if isinstance(event, dict)
        and event.get("event_id") == binding_id
        and event.get("source_id") == source_id
    ]
    if len(matching_events) != 1:
        return False
    binding_event = matching_events[0]
    occurred_at_utc = binding_event.get("occurred_at_utc")
    monotonic_ns = binding_event.get("monotonic_ns")
    if not isinstance(occurred_at_utc, str) or not isinstance(monotonic_ns, int):
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
        "occurred_at_utc": occurred_at_utc,
        "monotonic_ns": monotonic_ns,
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
