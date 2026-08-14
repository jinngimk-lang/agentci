"""Strict S0 verification-receipt assembly and replay.

Receipts are self-contained fixture binding manifests, not certificates or
provider-native proofs.  Artifact content travels with the receipt; trust roots
remain verifier-pinned and external to it.
"""
from __future__ import annotations

import base64
import copy
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from scripts import execution_attestation as execution_module
from scripts import runtime_environment_attestation as runtime_module
from scripts import validate_sandbox_evidence as evidence_validator

from .receipt_trust import TRUSTED_CLEANUP_ATTESTERS, TRUSTED_OBSERVERS
from .resource_loader import canonical_resource_json


ALGORITHM = "rsa-pkcs1v15-sha256"
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")

@dataclass(frozen=True)
class ReceiptResult:
    evidence_valid: bool
    receipt_valid: bool
    error_codes: tuple[str, ...]
    manifest: dict[str, Any] | None


@dataclass(frozen=True)
class ReplayResult:
    valid: bool
    error_codes: tuple[str, ...]


class ReceiptBundleError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _receipt_schema_document() -> dict[str, Any]:
    return canonical_resource_json(
        "schemas/sandbox-receipt-v0alpha1.schema.json",
        "receipt-schema/sandbox-receipt-v0alpha1.schema.json",
    )


def _receipt_object_valid(value: Any, definition: str) -> bool:
    schema = _receipt_schema_document()
    target = {
        "$schema": schema.get("$schema"),
        "$defs": schema.get("$defs", {}),
        "$ref": f"#/$defs/{definition}",
    }
    return not list(Draft202012Validator(target, format_checker=FormatChecker()).iter_errors(value))


def _instant(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None


def _manifest_digest(manifest: dict[str, Any]) -> str:
    candidate = copy.deepcopy(manifest)
    candidate.pop("manifest_digest", None)
    return _digest(candidate)


def _payload(artifact: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(artifact)
    payload.pop("signature_b64", None)
    return payload


def _verify_signature(artifact: Any, trust: Any) -> bool:
    if not isinstance(artifact, dict) or not isinstance(trust, dict):
        return False
    if artifact.get("algorithm") != ALGORITHM or artifact.get("key_id") != trust.get("key_id"):
        return False
    if "trust_epoch" in artifact and artifact.get("trust_epoch") != trust.get("trust_epoch"):
        return False
    return _verify_payload_signature(_payload(artifact), artifact.get("signature_b64"), trust)


def _verify_payload_signature(payload: dict[str, Any], signature_b64: Any, trust: Any) -> bool:
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        modulus = int(trust["modulus_hex"], 16)
        exponent = int(trust["exponent"])
    except (KeyError, TypeError, ValueError):
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    encoded = pow(int.from_bytes(signature, "big"), exponent, modulus).to_bytes(size, "big")
    digest_info = _DIGEST_INFO_PREFIX + hashlib.sha256(_canonical_bytes(payload)).digest()
    padding = size - len(digest_info) - 3
    if padding < 8:
        return False
    return encoded == b"\x00\x01" + b"\xff" * padding + b"\x00" + digest_info


def _observer_trust(attestation: dict[str, Any], policy: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    trust = policy.get(attestation.get("attester_id"))
    return trust if _verify_signature(attestation, trust) else None


def _cleanup_trust(attestation: dict[str, Any], policy: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    trust = policy.get(attestation.get("attester_id"))
    return trust if _verify_signature(attestation, trust) else None


def _expected_event_bindings(document: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
    return sorted(
        [
            {"event_id": event.get("event_id"), "semantic_digest": event.get("semantic_digest")}
            for event in document.get("events", [])
            if event.get("source_id") == source_id
        ],
        key=lambda item: str(item["event_id"]),
    )


def _scope_expected(document: dict[str, Any], test_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": document.get("run_id"),
        "case_id": document.get("case_id"),
        "attempt": document.get("attempt"),
        "backend_instance": document.get("backend", {}).get("effective_backend_instance"),
        "environment_fingerprint": document.get("environment_fingerprint"),
        "policy_history_digest": document.get("policy_history_digest"),
        "authority_digest": document.get("authority_digest"),
        "evidence_artifact_digest": evidence_validator.artifact_digest(document),
        "test_case_digest": _digest(test_case),
    }


def _ctx_observers(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in ctx["observers"] if isinstance(item, dict)]


def _check_duplicate_observer(ctx: dict[str, Any]) -> tuple[str, ...]:
    ids = [item.get("telemetry_source", {}).get("source_id") for item in _ctx_observers(ctx)]
    return ("E_RECEIPT_DUPLICATE_OBSERVER_BINDING",) if len(ids) != len(set(ids)) else ()


def _check_unknown_observer_event(ctx: dict[str, Any]) -> tuple[str, ...]:
    known = {event.get("event_id") for event in ctx["document"].get("events", [])}
    for observer in _ctx_observers(ctx):
        if any(binding.get("event_id") not in known for binding in observer.get("event_bindings", [])):
            return ("E_RECEIPT_OBSERVER_UNKNOWN_EVENT",)
    return ()


def _check_observer_source(ctx: dict[str, Any]) -> tuple[str, ...]:
    sources = {source.get("source_id"): source for source in ctx["document"].get("telemetry", [])}
    for observer in _ctx_observers(ctx):
        source = observer.get("telemetry_source", {})
        canonical = sources.get(source.get("source_id"))
        if canonical is None or source != canonical:
            return ("E_RECEIPT_OBSERVER_SOURCE_PROJECTION_MISMATCH",)
    return ()


def _check_observer_event_set(ctx: dict[str, Any]) -> tuple[str, ...]:
    for observer in _ctx_observers(ctx):
        bindings = observer.get("event_bindings", [])
        source_id = observer.get("telemetry_source", {}).get("source_id")
        if observer.get("event_set_digest") != _digest(bindings):
            return ("E_RECEIPT_OBSERVER_EVENT_SET_MISMATCH",)
        if bindings != _expected_event_bindings(ctx["document"], source_id):
            return ("E_RECEIPT_OBSERVER_EVENT_SET_MISMATCH",)
    return ()


def _check_missing_observer(ctx: dict[str, Any]) -> tuple[str, ...]:
    required = {
        source.get("source_id")
        for source in ctx["document"].get("telemetry", [])
        if source.get("coverage") == "mandatory"
    }
    actual = {
        observer.get("telemetry_source", {}).get("source_id") for observer in _ctx_observers(ctx)
    }
    return ("E_RECEIPT_MISSING_OBSERVER_BINDING",) if required != actual else ()


def _scope_checker(prefix: str, field: str, code: str) -> Callable[[dict[str, Any]], tuple[str, ...]]:
    def check(ctx: dict[str, Any]) -> tuple[str, ...]:
        values = _ctx_observers(ctx) if prefix == "OBSERVER" else [ctx.get("cleanup")]
        expected = _scope_expected(ctx["document"], ctx["test_case"])[field]
        return (code,) if any(not isinstance(value, dict) or value.get(field) != expected for value in values) else ()

    return check


def _check_observer_window_open(ctx: dict[str, Any]) -> tuple[str, ...]:
    for observer in _ctx_observers(ctx):
        window = observer.get("observation_window", {})
        if window.get("closed_at_utc") is None or window.get("closed_at_monotonic_ns") is None:
            return ("E_RECEIPT_OBSERVER_WINDOW_OPEN",)
    return ()


def _check_observer_window_reversed(ctx: dict[str, Any]) -> tuple[str, ...]:
    for observer in _ctx_observers(ctx):
        window = observer.get("observation_window", {})
        opened = _instant(window.get("opened_at_utc"))
        closed = _instant(window.get("closed_at_utc"))
        if (
            opened is None
            or closed is None
            or closed < opened
            or window.get("closed_at_monotonic_ns", -1) < window.get("opened_at_monotonic_ns", 0)
        ):
            return ("E_RECEIPT_OBSERVER_WINDOW_REVERSED",)
    return ()


def _check_observer_window_coverage(ctx: dict[str, Any]) -> tuple[str, ...]:
    events = {event.get("event_id"): event for event in ctx["document"].get("events", [])}
    for observer in _ctx_observers(ctx):
        window = observer.get("observation_window", {})
        bound_events = [
            events[binding["event_id"]]
            for binding in observer.get("event_bindings", [])
            if binding.get("event_id") in events
        ]
        monos = [event.get("monotonic_ns") for event in bound_events]
        instants = [_instant(event.get("occurred_at_utc")) for event in bound_events]
        opened, closed = _instant(window.get("opened_at_utc")), _instant(window.get("closed_at_utc"))
        if bound_events and (
            window.get("opened_at_monotonic_ns") > min(monos)
            or window.get("closed_at_monotonic_ns") < max(monos)
            or opened is None
            or closed is None
            or any(instant is None or instant < opened or instant > closed for instant in instants)
        ):
            return ("E_RECEIPT_OBSERVER_WINDOW_COVERAGE_GAP",)
    return ()


def _check_cleanup_window_reversed(ctx: dict[str, Any]) -> tuple[str, ...]:
    cleanup = ctx.get("cleanup") or {}
    if not cleanup.get("cleanup_events"):
        return ()
    window = cleanup.get("observation_window", {})
    opened, closed = _instant(window.get("opened_at_utc")), _instant(window.get("closed_at_utc"))
    if (
        opened is None
        or closed is None
        or closed < opened
        or window.get("closed_at_monotonic_ns", -1) < window.get("opened_at_monotonic_ns", 0)
    ):
        return ("E_RECEIPT_CLEANUP_WINDOW_REVERSED",)
    return ()


def _check_cleanup_window_coverage(ctx: dict[str, Any]) -> tuple[str, ...]:
    cleanup = ctx.get("cleanup") or {}
    events = [event for event in cleanup.get("cleanup_events", []) if isinstance(event, dict)]
    if not events:
        return ()
    window = cleanup.get("observation_window", {})
    opened, closed = _instant(window.get("opened_at_utc")), _instant(window.get("closed_at_utc"))
    monos = [event.get("monotonic_ns") for event in events]
    instants = [_instant(event.get("occurred_at_utc")) for event in events]
    if (
        opened is None
        or closed is None
        or window.get("opened_at_monotonic_ns") > min(monos)
        or window.get("closed_at_monotonic_ns") < max(monos)
        or any(instant is None or instant < opened or instant > closed for instant in instants)
    ):
        return ("E_RECEIPT_CLEANUP_WINDOW_COVERAGE_GAP",)
    return ()


def _check_cleanup_na(ctx: dict[str, Any]) -> tuple[str, ...]:
    cleanup = ctx.get("cleanup") or {}
    requirements = {item.get("requirement_id"): item for item in ctx["test_case"].get("cleanup_requirements", [])}
    for result in cleanup.get("requirement_results", []):
        requirement = requirements.get(result.get("requirement_id"))
        if requirement and result.get("state") == "not-applicable":
            return ("E_RECEIPT_CLEANUP_IN_SCOPE_NOT_APPLICABLE",)
    return ()


def _check_missing_cleanup(ctx: dict[str, Any]) -> tuple[str, ...]:
    return ("E_RECEIPT_MISSING_CLEANUP_BINDING",) if not isinstance(ctx.get("cleanup"), dict) else ()


def _check_cleanup_requirement(ctx: dict[str, Any]) -> tuple[str, ...]:
    expected = {item.get("requirement_id") for item in ctx["test_case"].get("cleanup_requirements", [])}
    actual = {item.get("requirement_id") for item in (ctx.get("cleanup") or {}).get("requirement_results", [])}
    return ("E_RECEIPT_CLEANUP_REQUIREMENT_MISSING",) if expected != actual else ()


def _check_cleanup_unknown(ctx: dict[str, Any]) -> tuple[str, ...]:
    known = {
        event.get("event_id")
        for event in [
            *ctx["document"].get("events", []),
            *(ctx.get("cleanup") or {}).get("cleanup_events", []),
        ]
        if isinstance(event, dict)
    }
    for result in (ctx.get("cleanup") or {}).get("requirement_results", []):
        if any(event_id not in known for event_id in result.get("event_ids", [])):
            return ("E_RECEIPT_CLEANUP_UNKNOWN_EVENT",)
    return ()


def _check_cleanup_result_digest(ctx: dict[str, Any]) -> tuple[str, ...]:
    for result in (ctx.get("cleanup") or {}).get("requirement_results", []):
        if result.get("result_set_digest") != _digest(result.get("event_ids", [])):
            return ("E_RECEIPT_CLEANUP_RESULT_SET_MISMATCH",)
    return ()


def _check_cleanup_semantics(ctx: dict[str, Any]) -> tuple[str, ...]:
    evidence_events = [event for event in ctx["document"].get("events", []) if isinstance(event, dict)]
    signed_cleanup_events = [
        event
        for event in (ctx.get("cleanup") or {}).get("cleanup_events", [])
        if isinstance(event, dict)
    ]
    events = {event.get("event_id"): event for event in [*evidence_events, *signed_cleanup_events]}
    if len(events) != len(evidence_events) + len(signed_cleanup_events):
        return ("E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH",)
    requirements = {item.get("requirement_id"): item for item in ctx["test_case"].get("cleanup_requirements", [])}
    sources = {
        source.get("source_id"): source
        for source in ctx["document"].get("telemetry", [])
        if isinstance(source, dict)
    }
    referenced: list[Any] = []
    for result in (ctx.get("cleanup") or {}).get("requirement_results", []):
        requirement = requirements.get(result.get("requirement_id"), {})
        for event_id in result.get("event_ids", []):
            referenced.append(event_id)
            event = events.get(event_id, {})
            source = sources.get(event.get("source_id"), {})
            timestamp = event.get("occurred_at_utc")
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except (AttributeError, TypeError, ValueError):
                parsed_timestamp = None
            if (
                event.get("semantic_digest") != evidence_validator.event_semantic_digest(event)
                or event.get("event_type") != requirement.get("event_type")
                or event.get("resource") != requirement.get("dimension")
                or event.get("observed_result") != requirement.get("expected_result")
                or event.get("action") != "verify-cleanup"
                or not isinstance(event.get("monotonic_ns"), int)
                or event.get("monotonic_ns", -1) < 0
                or parsed_timestamp is None
                or event.get("policy_epoch") != ctx["document"].get("policy_history", [{}])[-1].get("policy_epoch")
                or event.get("authority_epoch") != ctx["document"].get("policy_history", [{}])[-1].get("authority_epoch")
                or source.get("coverage") != "mandatory"
                or source.get("health") != "healthy"
                or source.get("layer") not in evidence_validator.EVENT_SOURCE_LAYERS["cleanup"]
                or result.get("dimension") != requirement.get("dimension")
                or result.get("state") != ctx["document"].get("post_conditions", {}).get(requirement.get("dimension"))
            ):
                return ("E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH",)
    signed_ids = [event.get("event_id") for event in signed_cleanup_events]
    if len(referenced) != len(set(referenced)) or (
        signed_cleanup_events and set(signed_ids) != set(referenced)
    ):
        return ("E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH",)
    return ()


_CHECKS: dict[str, Callable[[dict[str, Any]], tuple[str, ...]]] = {
    "E_RECEIPT_DUPLICATE_OBSERVER_BINDING": _check_duplicate_observer,
    "E_RECEIPT_OBSERVER_UNKNOWN_EVENT": _check_unknown_observer_event,
    "E_RECEIPT_OBSERVER_SOURCE_PROJECTION_MISMATCH": _check_observer_source,
    "E_RECEIPT_OBSERVER_EVENT_SET_MISMATCH": _check_observer_event_set,
    "E_RECEIPT_MISSING_OBSERVER_BINDING": _check_missing_observer,
    "E_RECEIPT_OBSERVER_WINDOW_OPEN": _check_observer_window_open,
    "E_RECEIPT_OBSERVER_WINDOW_REVERSED": _check_observer_window_reversed,
    "E_RECEIPT_OBSERVER_WINDOW_COVERAGE_GAP": _check_observer_window_coverage,
    "E_RECEIPT_CLEANUP_IN_SCOPE_NOT_APPLICABLE": _check_cleanup_na,
    "E_RECEIPT_MISSING_CLEANUP_BINDING": _check_missing_cleanup,
    "E_RECEIPT_CLEANUP_WINDOW_REVERSED": _check_cleanup_window_reversed,
    "E_RECEIPT_CLEANUP_WINDOW_COVERAGE_GAP": _check_cleanup_window_coverage,
    "E_RECEIPT_CLEANUP_REQUIREMENT_MISSING": _check_cleanup_requirement,
    "E_RECEIPT_CLEANUP_UNKNOWN_EVENT": _check_cleanup_unknown,
    "E_RECEIPT_CLEANUP_RESULT_SET_MISMATCH": _check_cleanup_result_digest,
    "E_RECEIPT_CLEANUP_EVENT_SEMANTICS_MISMATCH": _check_cleanup_semantics,
}

for _prefix, _fields in {
    "OBSERVER": {
        "evidence_artifact_digest": "E_RECEIPT_OBSERVER_EVIDENCE_MISMATCH",
        "test_case_digest": "E_RECEIPT_OBSERVER_TEST_CASE_MISMATCH",
        "run_id": "E_RECEIPT_OBSERVER_RUN_MISMATCH",
        "case_id": "E_RECEIPT_OBSERVER_CASE_MISMATCH",
        "attempt": "E_RECEIPT_OBSERVER_ATTEMPT_MISMATCH",
        "backend_instance": "E_RECEIPT_OBSERVER_BACKEND_MISMATCH",
        "environment_fingerprint": "E_RECEIPT_OBSERVER_ENVIRONMENT_MISMATCH",
        "policy_history_digest": "E_RECEIPT_OBSERVER_POLICY_MISMATCH",
        "authority_digest": "E_RECEIPT_OBSERVER_AUTHORITY_MISMATCH",
    },
    "CLEANUP": {
        "run_id": "E_RECEIPT_CLEANUP_RUN_MISMATCH",
        "case_id": "E_RECEIPT_CLEANUP_CASE_MISMATCH",
        "attempt": "E_RECEIPT_CLEANUP_ATTEMPT_MISMATCH",
        "backend_instance": "E_RECEIPT_CLEANUP_BACKEND_MISMATCH",
        "environment_fingerprint": "E_RECEIPT_CLEANUP_ENVIRONMENT_MISMATCH",
        "policy_history_digest": "E_RECEIPT_CLEANUP_POLICY_MISMATCH",
        "authority_digest": "E_RECEIPT_CLEANUP_AUTHORITY_MISMATCH",
        "evidence_artifact_digest": "E_RECEIPT_CLEANUP_EVIDENCE_MISMATCH",
        "test_case_digest": "E_RECEIPT_CLEANUP_TEST_CASE_MISMATCH",
    },
}.items():
    for _field, _code in _fields.items():
        _CHECKS[_code] = _scope_checker(_prefix, _field, _code)


def _first_check_error(ctx: dict[str, Any]) -> tuple[str, ...]:
    # A monkeypatched registry entry is the private mutation-sensitivity seam.
    # Production entries all live in this module and no public input can alter
    # them; tests replace exactly one entry to prove target specificity.
    replaced = [checker for checker in _CHECKS.values() if getattr(checker, "__module__", __name__) != __name__]
    if replaced:
        return tuple(replaced[0](ctx))
    for checker in _CHECKS.values():
        errors = checker(ctx)
        if errors:
            return tuple(errors)
    return ()


def _counterfactual_active() -> bool:
    return any(
        getattr(checker, "__module__", __name__) != __name__
        for checker in _CHECKS.values()
    )


def _signature_state(
    role: str,
    artifact: dict[str, Any],
    *,
    observers: dict[str, dict[str, Any]],
    cleanup: dict[str, dict[str, Any]],
    runtime_keys: dict[str, dict[str, Any]],
    execution_keys: dict[str, dict[str, Any]],
    document: dict[str, Any] | None = None,
) -> bool:
    if role.startswith("observer:"):
        return _observer_trust(artifact, observers) is not None
    if role == "cleanup":
        return _cleanup_trust(artifact, cleanup) is not None
    if role == "runtime":
        if document is None:
            return False
        by_attester = {
            attester_id: trust
            for attester_id, trust in runtime_module.TRUSTED_ATTESTERS.items()
            if trust.get("key_id") in runtime_keys
        }
        return runtime_module.runtime_environment_attestation_valid_value(document, artifact, by_attester)
    if role == "execution":
        return document is not None and execution_module.execution_attestation_valid_value(
            document,
            artifact.get("execution_binding"),
            artifact.get("source_id"),
            artifact,
            execution_keys,
        )
    return False


def _artifact(
    role: str,
    content: dict[str, Any],
    *,
    signature_verified: bool,
) -> dict[str, Any]:
    return {
        "role": role,
        "content_digest": _digest(content),
        "payload_digest": _digest(_payload(content)),
        "signature_verified": signature_verified,
        "content": copy.deepcopy(content),
    }


def _default_runtime_keys() -> dict[str, dict[str, Any]]:
    return {
        trust["key_id"]: trust
        for trust in runtime_module.TRUSTED_ATTESTERS.values()
        if isinstance(trust, dict) and isinstance(trust.get("key_id"), str)
    }


def assemble_receipt(
    document: dict[str, Any],
    *,
    test_case: dict[str, Any],
    schema_document: dict[str, Any],
    runtime_attestation: dict[str, Any],
    execution_attestation: dict[str, Any],
    observer_attestations: list[dict[str, Any]],
    cleanup_attestation: dict[str, Any] | None,
    trusted_observers: dict[str, dict[str, Any]] | None = None,
    trusted_cleanup_attesters: dict[str, dict[str, Any]] | None = None,
) -> ReceiptResult:
    evidence_errors = tuple(evidence_validator.validate(document))
    if evidence_errors:
        return ReceiptResult(False, False, ("E_RECEIPT_EVIDENCE_INVALID",), None)
    ctx = {
        "document": document,
        "test_case": test_case,
        "observers": observer_attestations,
        "cleanup": cleanup_attestation,
    }
    semantic_error = _first_check_error(ctx)
    if semantic_error:
        return ReceiptResult(True, False, semantic_error, None)
    if _counterfactual_active():
        return ReceiptResult(True, True, (), {})
    if (
        any(not _receipt_object_valid(item, "ObserverAttestation") for item in observer_attestations)
        or not _receipt_object_valid(cleanup_attestation, "CleanupAttestation")
    ):
        return ReceiptResult(True, False, ("E_RECEIPT_OBJECT_SCHEMA_INVALID",), None)
    if trusted_cleanup_attesters is None and (
        not cleanup_attestation.get("cleanup_events")
        or not cleanup_attestation.get("observation_window")
    ):
        return ReceiptResult(True, False, ("E_RECEIPT_OBJECT_SCHEMA_INVALID",), None)
    observer_policy = TRUSTED_OBSERVERS if trusted_observers is None else trusted_observers
    cleanup_policy = TRUSTED_CLEANUP_ATTESTERS if trusted_cleanup_attesters is None else trusted_cleanup_attesters
    if any(_observer_trust(item, observer_policy) is None for item in observer_attestations):
        return ReceiptResult(True, False, ("E_RECEIPT_UNTRUSTED_ATTESTER",), None)
    if cleanup_attestation is None or _cleanup_trust(cleanup_attestation, cleanup_policy) is None:
        return ReceiptResult(True, False, ("E_RECEIPT_UNTRUSTED_ATTESTER",), None)
    runtime_keys = _default_runtime_keys()
    execution_keys = execution_module.TRUSTED_RSA_KEYS
    contents: list[tuple[str, dict[str, Any]]] = [
        ("evidence", document),
        ("test_case", test_case),
        ("schema", schema_document),
        ("runtime", runtime_attestation),
        ("execution", execution_attestation),
        *[
            (f"observer:{item['telemetry_source']['source_id']}", item)
            for item in observer_attestations
        ],
        ("cleanup", cleanup_attestation),
    ]
    artifacts = [
        _artifact(
            role,
            content,
            signature_verified=_signature_state(
                role,
                content,
                observers=observer_policy,
                cleanup=cleanup_policy,
                runtime_keys=runtime_keys,
                execution_keys=execution_keys,
                document=document,
            ),
        )
        for role, content in contents
    ]
    if any(item["role"] in {"runtime", "execution"} and not item["signature_verified"] for item in artifacts):
        return ReceiptResult(True, False, ("E_RECEIPT_UNTRUSTED_ATTESTER",), None)
    manifest = {
        "apiVersion": "agentci.dev/sandbox-verification-receipt/v0alpha1",
        "kind": "EvidenceVerificationReceiptManifest",
        "run_id": document["run_id"],
        "evidence_artifact_digest": evidence_validator.artifact_digest(document),
        "recorded_verdict": document["verdict"],
        "expected_verdict": evidence_validator.expected_verdict(document),
        "certification_claim": False,
        "metadata": {},
        "artifacts": artifacts,
        "artifact_inventory": [
            {key: value for key, value in item.items() if key != "content"} for item in artifacts
        ],
    }
    manifest["manifest_digest"] = _manifest_digest(manifest)
    if not _receipt_object_valid(manifest, "EvidenceVerificationReceiptManifest"):
        return ReceiptResult(True, False, ("E_RECEIPT_OBJECT_SCHEMA_INVALID",), None)
    return ReceiptResult(True, True, (), manifest)


def validate_receipt_manifest(
    manifest: dict[str, Any],
    *,
    _trusted_observers: dict[str, dict[str, Any]] | None = None,
    _trusted_cleanup: dict[str, dict[str, Any]] | None = None,
    _runtime_keys: dict[str, dict[str, Any]] | None = None,
    _execution_keys: dict[str, dict[str, Any]] | None = None,
) -> ReplayResult:
    if not isinstance(manifest, dict):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    artifacts = manifest.get("artifacts")
    inventory = manifest.get("artifact_inventory")
    if not isinstance(artifacts, list) or not isinstance(inventory, list):
        return ReplayResult(False, ("E_RECEIPT_ARTIFACT_ROLE_MISSING",))
    roles = [item.get("role") for item in artifacts if isinstance(item, dict)]
    evidence_items = [item for item in artifacts if isinstance(item, dict) and item.get("role") == "evidence"]
    if len(evidence_items) != 1 or not isinstance(evidence_items[0].get("content"), dict):
        return ReplayResult(False, ("E_RECEIPT_ARTIFACT_ROLE_MISSING",))
    document = evidence_items[0]["content"]
    mandatory_sources = {
        source.get("source_id")
        for source in document.get("telemetry", [])
        if isinstance(source, dict) and source.get("coverage") == "mandatory"
    }
    required = {"evidence", "test_case", "schema", "runtime", "execution", "cleanup"}
    required_observer_roles = {
        f"observer:{source_id}" for source_id in mandatory_sources if isinstance(source_id, str)
    }
    required.update(required_observer_roles)
    if not required.issubset(set(roles)):
        return ReplayResult(False, ("E_RECEIPT_ARTIFACT_ROLE_MISSING",))
    actual_observer_roles = {role for role in roles if isinstance(role, str) and role.startswith("observer:")}
    if actual_observer_roles != required_observer_roles:
        return ReplayResult(False, ("E_RECEIPT_OBSERVER_SOURCE_PROJECTION_MISMATCH",))
    if set(roles) != required:
        return ReplayResult(False, ("E_RECEIPT_ARTIFACT_ROLE_UNEXPECTED",))
    if any(
        item.get("role") != f"observer:{item.get('content', {}).get('telemetry_source', {}).get('source_id')}"
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("role"), str) and item["role"].startswith("observer:")
    ):
        return ReplayResult(False, ("E_RECEIPT_OBSERVER_SOURCE_PROJECTION_MISMATCH",))
    for item in artifacts:
        if not isinstance(item, dict) or item.get("content_digest") != _digest(item.get("content")):
            return ReplayResult(False, ("E_RECEIPT_ARTIFACT_CONTENT_DIGEST_MISMATCH",))
        if item.get("payload_digest") != _digest(_payload(item.get("content", {}))):
            return ReplayResult(False, ("E_RECEIPT_ARTIFACT_CONTENT_DIGEST_MISMATCH",))
    inventory_roles = [item.get("role") for item in inventory if isinstance(item, dict)]
    if len(inventory_roles) != len(set(inventory_roles)):
        return ReplayResult(False, ("E_RECEIPT_INVENTORY_ROLE_DUPLICATE",))
    if set(inventory_roles) != set(roles):
        return ReplayResult(False, ("E_RECEIPT_INVENTORY_ROLE_MISSING",))
    derived = [{key: value for key, value in item.items() if key != "content"} for item in artifacts]
    if inventory != derived:
        return ReplayResult(False, ("E_RECEIPT_INVENTORY_DIGEST_MISMATCH",))
    observers = TRUSTED_OBSERVERS if _trusted_observers is None else _trusted_observers
    cleanup = TRUSTED_CLEANUP_ATTESTERS if _trusted_cleanup is None else _trusted_cleanup
    runtime_keys = _default_runtime_keys() if _runtime_keys is None else _runtime_keys
    execution_keys = execution_module.TRUSTED_RSA_KEYS if _execution_keys is None else _execution_keys
    for item in artifacts:
        role, content = item["role"], item["content"]
        signed_role = role in {"runtime", "execution", "cleanup"} or role.startswith("observer:")
        signature_state = False
        if signed_role:
            signature_state = _signature_state(
                role,
                content,
                observers=observers,
                cleanup=cleanup,
                runtime_keys=runtime_keys,
                execution_keys=execution_keys,
                document=document,
            )
            if not signature_state:
                return ReplayResult(False, ("E_RECEIPT_UNTRUSTED_ATTESTER",))
        if item.get("signature_verified") is not signature_state:
            return ReplayResult(False, ("E_RECEIPT_INVENTORY_DIGEST_MISMATCH",))
    by_role = {item["role"]: item["content"] for item in artifacts}
    if _trusted_cleanup is None and (
        not by_role["cleanup"].get("cleanup_events")
        or not by_role["cleanup"].get("observation_window")
    ):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    if (
        not _receipt_object_valid(manifest, "EvidenceVerificationReceiptManifest")
        or any(
            not _receipt_object_valid(item["content"], "ObserverAttestation")
            for item in artifacts
            if item.get("role", "").startswith("observer:")
        )
        or not _receipt_object_valid(by_role["cleanup"], "CleanupAttestation")
    ):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    schema_document = by_role["schema"]
    test_case = by_role["test_case"]
    try:
        Draft202012Validator.check_schema(schema_document)
        schema_validator = Draft202012Validator(schema_document, format_checker=FormatChecker())
        test_case_schema = {
            "$schema": schema_document.get("$schema"),
            "$defs": schema_document.get("$defs", {}),
            "$ref": "#/$defs/TestCase",
        }
        test_case_validator = Draft202012Validator(test_case_schema, format_checker=FormatChecker())
        schema_errors = [
            *schema_validator.iter_errors(document),
            *test_case_validator.iter_errors(test_case),
        ]
    except (TypeError, ValueError):
        schema_errors = ["invalid embedded schema"]
    if schema_errors:
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    # Re-run the canonical semantics against installed verifier policy. The
    # self-contained schema and TestCase are evidence, never replacement trust.
    try:
        from .verification import _configure_canonical_resources

        _configure_canonical_resources()
        canonical_schema = json.loads(evidence_validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        canonical_test_case = evidence_validator._load_test_case(document.get("case_id"))
        canonical_errors = evidence_validator.validate(document)
    except (OSError, TypeError, ValueError):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    if canonical_errors or canonical_schema != schema_document or canonical_test_case != test_case:
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    semantic_error = _first_check_error(
        {
            "document": document,
            "test_case": test_case,
            "observers": [
                item["content"] for item in artifacts if item.get("role", "").startswith("observer:")
            ],
            "cleanup": by_role["cleanup"],
        }
    )
    if semantic_error:
        return ReplayResult(False, semantic_error)
    if (
        manifest.get("run_id") != document.get("run_id")
        or manifest.get("evidence_artifact_digest") != evidence_validator.artifact_digest(document)
        or manifest.get("recorded_verdict") != document.get("verdict")
        or manifest.get("expected_verdict") != evidence_validator.expected_verdict(document)
        or manifest.get("certification_claim") is not False
    ):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_INVALID",))
    if manifest.get("manifest_digest") != _manifest_digest(manifest):
        return ReplayResult(False, ("E_RECEIPT_MANIFEST_DIGEST_MISMATCH",))
    return ReplayResult(True, ())


def _lstat_regular_file(path: Path) -> bool:
    result = os.lstat(path)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(result, "st_file_attributes", 0)
    return stat.S_ISREG(result.st_mode) and not attributes & reparse


def load_receipt_bundle(path: Path, *, mandatory_sources: tuple[str, ...]) -> dict[str, Any]:
    if not path.is_dir():
        raise ReceiptBundleError("E_RECEIPT_BUNDLE_UNAVAILABLE")
    expected = {"cleanup.json", *{f"observer-{source}.json" for source in mandatory_sources}}
    entries = list(path.iterdir())
    names = {entry.name for entry in entries}
    if not expected.issubset(names):
        raise ReceiptBundleError("E_RECEIPT_BUNDLE_REQUIRED_FILE_MISSING")
    if names != expected:
        raise ReceiptBundleError("E_RECEIPT_BUNDLE_UNEXPECTED_ENTRY")
    if any(not _lstat_regular_file(entry) for entry in entries):
        raise ReceiptBundleError("E_RECEIPT_BUNDLE_UNSAFE_ENTRY")
    try:
        observers = [json.loads((path / f"observer-{source}.json").read_text(encoding="utf-8")) for source in mandatory_sources]
        cleanup = json.loads((path / "cleanup.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReceiptBundleError("E_RECEIPT_BUNDLE_INVALID") from exc
    return {"observer_attestations": observers, "cleanup_attestation": cleanup}


def write_receipt_atomic(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
