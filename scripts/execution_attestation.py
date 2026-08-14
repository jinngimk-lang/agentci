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

# Public verification material only. Private signing keys are not stored in
# this repository and are not derivable from EvidenceEnvelope fields.
TRUSTED_RSA_KEYS = {
    "fixture-runner-key-v2": {
        "modulus_hex": "bfee16e846ba53691fe81c306df4faf3ef164db5d4798973336b09532d13c2bc8d1ee9337cc1fac88ad3287678b50f8b02538ab463e8ad1bd761c812b1f4664d169dbc7100c2149e45afa7d0a981f0cb6e306874cabe88129b60350f8bf14c64434c5ffb0892a395cc3f28483fe61aedf6a708007a842dc99656fb30c487e38e5a96b0a6ec806d09c8f76787768d26462545f0f2dd6461a8cb3c2f88a987f5fc3833bbaadf94e3e62796a08cd5211a56748eafc8e7b17fa898b00a302a62d9b53134ebb7f952d4851a6ee196ea55208b35615b339bd088603211fda294c0a69919e4bf5e3eb1021c7f85367ade7d82d66aedaabd4c09a631c087ba105f6766f7",
        "exponent": 65537,
    },
    "fixture-runner-key-v3": {
        "modulus_hex": "ad1c7ce3739cf370e0b685742e68e296df726923211678b2e1abed997f671cb27028d01c2a0fd818038c816ac51c3bfbec229e45b4c98d1d5bea029bdf3946a3340e66e98fe065fb7970e16ba15caf670cc343f9faa8eaaf7b3f0dd388a564ba0bf3d674e99bc85138c734205e00cda39b07bb47ad5f4f1a5dffbf226177bd87a7aa42c639baa1397c40ee7279c0913c12ab1d640c2a3d76654e45ed48254a37547e01b75845d5873bd1f22ba3f23c5e4f37743e287710062991b3c9519b7f8abb257c953ac5e0ad87a82e4d1cb87a72f0765aa3c6324933f6059ab7499cd1d4eb1de377eafe636e84307c609edd13aabacca83c9d9065589c3538039011f2ef",
        "exponent": 65537,
    },
    "fixture-runner-key-v4": {
        "modulus_hex": "ccc378bf4ad4d4ee409cb57813333f73b23a4f84789f81318c1253377a41c3142f9113805192815da01965af4407950c7090671cb63ef495be41b47974f6e50ce35195ecbdf7a2d825d63e76204d584d6065119a28ce96ecb7733bf62dd2309d7bf60cc4231fd49d2611891ab0526a382d8f980501448c5c9bbd7d7b228a96ef7069af9712713e3e821094618b2fb2c3727aed74eb64b4cb72d38f82dd52b52d6522e61aa2af9c284c6db8c6f3a8084d82736ff3da031646566c8c1dd247f36e20c4dd097f9df59dea8d723fc0b805a9da6a4df34341ef37d2545f76fcaa00352d638b904c2ca5879abe72f206a18af47ba293bd2edc560a9c3070d865335785",
        "exponent": 65537,
    },
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


def _ordering_observation(event: dict[str, Any]) -> dict[str, Any] | None:
    """Project only fields actually used to establish causal ordering.

    Deliberately excludes Decision/EnforcementReceipt and other event payload
    fields so execution provenance remains distinct from authority semantics.
    """
    event_id = event.get("event_id")
    source_id = event.get("source_id")
    occurred_at_utc = event.get("occurred_at_utc")
    monotonic_ns = event.get("monotonic_ns")
    if not all(isinstance(value, str) and value for value in (event_id, source_id, occurred_at_utc)):
        return None
    if not isinstance(monotonic_ns, int):
        return None
    return {
        "event_id": event_id,
        "source_id": source_id,
        "occurred_at_utc": occurred_at_utc,
        "monotonic_ns": monotonic_ns,
    }


def _assertion_observation(event: dict[str, Any]) -> dict[str, Any] | None:
    """Project externally authenticated assertion semantics without authority refs.

    Decision and enforcement-receipt identifiers remain exclusively in the
    authority binding.  The execution attestation covers only the typed event
    semantics the evidence validator consumes.
    """
    ordering = _ordering_observation(event)
    if ordering is None:
        return None
    return {
        **ordering,
        "event_type": event.get("event_type"),
        "channel": event.get("channel"),
        "endpoint": event.get("endpoint"),
        "action": event.get("action"),
        "resource": event.get("resource"),
        "observed_result": event.get("observed_result"),
        "workload_identity": event.get("workload_identity"),
        "attachment_id": event.get("attachment_id"),
        "policy_epoch": event.get("policy_epoch"),
        "authority_epoch": event.get("authority_epoch"),
        "restore_epoch": event.get("restore_epoch"),
        "snapshot_id": event.get("snapshot_id"),
    }


def _causal_assertion_observations(document: dict[str, Any], binding_id: str) -> list[dict[str, Any]] | None:
    """Return assertion observations whose timing participates in PASS causality."""
    events_by_id = {
        event.get("event_id"): event
        for event in document.get("events", [])
        if isinstance(event, dict) and isinstance(event.get("event_id"), str)
    }
    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for assertion in document.get("assertions", []):
        if not isinstance(assertion, dict) or not assertion.get("mandatory") or assertion.get("state") not in {"PASS", "FAIL"}:
            continue
        for event_id in assertion.get("evidence_event_ids", []):
            if not isinstance(event_id, str) or not event_id.startswith(binding_id + ":") or event_id in seen:
                continue
            event = events_by_id.get(event_id)
            if not isinstance(event, dict):
                return None
            projection = _assertion_observation(event)
            if projection is None:
                return None
            observations.append(projection)
            seen.add(event_id)
    observations.sort(key=lambda item: item["event_id"])
    return observations


def execution_attestation_valid(document: dict[str, Any], binding_id: str, source_id: Any) -> bool:
    """Verify one execution binding and all causal timing inputs externally.

    The signed fixture sidecar authenticates the execution/process ordering
    observation and every assertion-side ordering observation used by the
    validator. A signed common clock-domain label makes comparability explicit.
    This is an S0 authenticity stand-in, not provider-native runtime causation,
    authority proof, anti-replay, or production key custody.
    """
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
    execution_observation = _ordering_observation(matching_events[0])
    assertion_observations = _causal_assertion_observations(document, binding_id)
    if execution_observation is None or assertion_observations is None or not assertion_observations:
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

    return execution_attestation_valid_value(document, binding_id, source_id, attestation)


def execution_attestation_valid_value(
    document: dict[str, Any],
    binding_id: str,
    source_id: Any,
    attestation: dict[str, Any],
    trusted_keys: dict[str, dict[str, Any]] | None = None,
) -> bool:
    """Verify an embedded sidecar against exact causal observations."""
    run_id = _safe_token(document.get("run_id"))
    case_id = _safe_token(document.get("case_id"))
    if run_id is None or case_id is None or not isinstance(source_id, str) or not isinstance(attestation, dict):
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
    execution_observation = _ordering_observation(matching_events[0])
    assertion_observations = _causal_assertion_observations(document, binding_id)
    if execution_observation is None or assertion_observations is None or not assertion_observations:
        return False
    clock_domain = attestation.get("clock_domain")
    if not isinstance(clock_domain, str) or not clock_domain:
        return False

    payload = {
        "run_id": run_id,
        "case_id": case_id,
        "attempt": document.get("attempt"),
        "execution_binding": binding_id,
        "source_id": source_id,
        "execution_observation": execution_observation,
        "assertion_observations": assertion_observations,
        "clock_domain": clock_domain,
        "key_id": attestation.get("key_id"),
        "algorithm": attestation.get("algorithm"),
    }
    for field, expected in payload.items():
        if attestation.get(field) != expected:
            return False
    if attestation.get("algorithm") != ALGORITHM:
        return False
    key = (TRUSTED_RSA_KEYS if trusted_keys is None else trusted_keys).get(attestation.get("key_id"))
    if key is None:
        return False
    return _rsa_pkcs1v15_sha256_verify(_canonical_bytes(payload), attestation.get("signature_b64"), key)
