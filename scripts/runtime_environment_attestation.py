"""S0 stand-in for authenticated runtime/environment provenance.

The EvidenceEnvelope is not the trust root. A signed sidecar is loaded from a
separate fixture channel and checked against a validator-pinned public key and
explicit backend/environment scope. This models only the S0 authenticity and
scope property; it is not provider-native attestation or a backend verdict.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_DIR = ROOT / "examples" / "sandbox" / "runtime-environment-attestations"
ALGORITHM = "rsa-pkcs1v15-sha256"

TRUSTED_ATTESTERS = {
    "fixture-runtime-observer": {
        "trust_epoch": 1,
        "key_id": "fixture-runtime-key-v1",
        "modulus_hex": "ce44cac24b34ab221d36e7fac2c7a419b65c5174e5092c7c036558147d3a4ef339df1b071af8a0310c3d3201e3749bef97a241ce3d67b0a02b6080200c18e909400d6b434c7d6be827cd5e8de99848de67c1c8eade3308a6292f42ca473f23b7434e1daaa6363e6cb76f50dfa564d59f3c7d5641d2dea9a0333fd1498b47f0055c0f92b365761f016f3275c8db2313995e3e62651b8154dde5a7f167c92ace2a1927b00a7b1e97f138b9d63bdcf1899f6bf1af6a293a9a1e70cb331dd9c785d643203df7fe697e3e43b949b649fe3a9b8692e344a67f4653fd639eff75be85df79820d3e9f1c5750fb3da7395b67207b4b451314835d46d3e4541027154ca569",
        "exponent": 65537,
        "backend_instance": "red-control-1",
        "environment_fingerprint": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    },
    "fixture-pass-runtime-observer": {
        "trust_epoch": 1,
        "key_id": "fixture-pass-runtime-key-v2",
        "modulus_hex": "bfaca29588372bb98ec69fcee8a3cb4fcfaf9d817445785024a2037ddf56f317bbd93a15318ae953499eaf1a7969b34d3cb6b53d9c5e5c3d5314353719aa7e8759a7706b7ac323a6e2274a1da1da25f5f908d72b1029f218e9e1fd1e7264f2d59b0a53b476661e4b013adf0abce18a0468797d4eaf93d0f07f9985f34500f43106e361a268bfa0e41096bb85caea3280bb78cdc2f2f33fd6bf82aeca38c6ce84e02b53ac3865872059f4c4ad2456e5fb22e5ef58226c86467bb6515ca860dc7e7d62fbbb0e077d5c8b2686893e19de545028568c89759261b85c9d1c0edf16d0d1f247656efee605d2c52299348ac754b1bbc3f07cacbf93162e0b29350c0c8b",
        "exponent": 65537,
        "backend_instance": "pass-control-1",
        "environment_fingerprint": "sha256:6666666666666666666666666666666666666666666666666666666666666666",
    },
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


def runtime_environment_attestation_valid(document: dict[str, Any]) -> bool:
    """Verify exact run/backend/environment against scoped provenance outside the envelope."""
    run_id = _safe_token(document.get("run_id"))
    case_id = _safe_token(document.get("case_id"))
    if run_id is None or case_id is None:
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

    attester_id = attestation.get("attester_id")
    trust = TRUSTED_ATTESTERS.get(attester_id)
    if trust is None or attestation.get("trust_epoch") != trust.get("trust_epoch"):
        return False
    if attestation.get("key_id") != trust.get("key_id") or attestation.get("algorithm") != ALGORITHM:
        return False

    backend = document.get("backend")
    if not isinstance(backend, dict):
        return False
    backend_binding = {
        "provider": backend.get("provider"),
        "isolation_class": backend.get("isolation_class"),
        "version": backend.get("version"),
        "build_or_image_digest": backend.get("build_or_image_digest"),
        "effective_backend_instance": backend.get("effective_backend_instance"),
    }
    environment_fingerprint = document.get("environment_fingerprint")
    payload = {
        "attestation_id": attestation.get("attestation_id"),
        "attester_id": attester_id,
        "trust_epoch": attestation.get("trust_epoch"),
        "run_id": run_id,
        "case_id": case_id,
        "attempt": document.get("attempt"),
        "backend": backend_binding,
        "environment_fingerprint": environment_fingerprint,
        "scope": attestation.get("scope"),
        "key_id": attestation.get("key_id"),
        "algorithm": attestation.get("algorithm"),
    }
    for field, expected in payload.items():
        if attestation.get(field) != expected:
            return False

    scope = attestation.get("scope")
    if not isinstance(scope, dict):
        return False
    if scope.get("backend_instance") != backend.get("effective_backend_instance"):
        return False
    if scope.get("environment_fingerprint") != environment_fingerprint:
        return False
    if scope.get("backend_instance") != trust.get("backend_instance"):
        return False
    if scope.get("environment_fingerprint") != trust.get("environment_fingerprint"):
        return False

    return _rsa_pkcs1v15_sha256_verify(_canonical_bytes(payload), attestation.get("signature_b64"), trust)
