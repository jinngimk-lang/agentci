"""S0 stand-in for runtime/environment provenance outside EvidenceEnvelope.

This deliberately models only one fixture trust boundary. The pinned digest and
scope are validator-side trust configuration, not provider-native attestation or
a backend security verdict.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_DIR = ROOT / "examples" / "sandbox" / "runtime-environment-attestations"

TRUSTED_ATTESTERS = {
    "fixture-runtime-observer": {
        "trust_epoch": 1,
        "attestation_digest": "sha256:4114f627c04bdf12b7914c6e3c2fdfd521ba78184bd52e0aea6d1a292f94f420",
        "backend_instance": "red-control-1",
        "environment_fingerprint": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe_token(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "/" in value or "\\" in value or value in {".", ".."}:
        return None
    return value


def runtime_environment_attestation_valid(document: dict[str, Any]) -> bool:
    """Bind one run to exact backend/environment through a pinned fixture trust root."""
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
    if _digest(attestation) != trust.get("attestation_digest"):
        return False

    backend = document.get("backend")
    if not isinstance(backend, dict) or attestation.get("backend") != {
        "provider": backend.get("provider"),
        "isolation_class": backend.get("isolation_class"),
        "version": backend.get("version"),
        "build_or_image_digest": backend.get("build_or_image_digest"),
        "effective_backend_instance": backend.get("effective_backend_instance"),
    }:
        return False

    environment_fingerprint = document.get("environment_fingerprint")
    expected = {
        "run_id": run_id,
        "case_id": case_id,
        "attempt": document.get("attempt"),
        "environment_fingerprint": environment_fingerprint,
    }
    for field, value in expected.items():
        if attestation.get(field) != value:
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
    return True
