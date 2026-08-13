"""Installed adapter for the canonical AgentCI S0 EvidenceEnvelope validator.

This module intentionally does not implement verdict semantics. It delegates to
the repository's canonical ``scripts.validate_sandbox_evidence`` implementation
and only supplies wheel-safe locations for the exact same canonical resources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from scripts import execution_attestation as execution_attestation_module
from scripts import runtime_environment_attestation as runtime_environment_attestation_module
from scripts import validate_sandbox_evidence as validator

from .resource_loader import INSTALLED_ROOT, SOURCE_ROOT


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    run_id: str | None
    recorded_verdict: str | None
    expected_verdict: str
    errors: tuple[str, ...]
    artifact_digest: str | None
    certification_claim: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _configure_canonical_resources() -> None:
    """Point the unchanged canonical validator at wheel data when needed."""
    source_schema = SOURCE_ROOT / 'schemas' / 'sandbox-certification-v0alpha1.schema.json'
    if source_schema.is_file():
        return

    validator.SCHEMA_PATH = INSTALLED_ROOT / 'schema' / 'sandbox-certification-v0alpha1.schema.json'
    validator.TEST_CASE_DIR = INSTALLED_ROOT / 'testcases'
    execution_attestation_module.ATTESTATION_DIR = INSTALLED_ROOT / 'execution-attestations'
    runtime_environment_attestation_module.ATTESTATION_DIR = INSTALLED_ROOT / 'runtime-environment-attestations'
    validator._schema_validator.cache_clear()
    validator._test_case_validator.cache_clear()
    validator._load_test_case.cache_clear()


def verify_evidence_file(path: Path, *, include_digest: bool = False) -> VerificationResult:
    """Validate one EvidenceEnvelope without treating verdict FAIL as tool failure."""
    _configure_canonical_resources()
    raw = path.read_text(encoding='utf-8')
    try:
        document = validator.load_evidence_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return VerificationResult(
            valid=False,
            run_id=None,
            recorded_verdict=None,
            expected_verdict='UNVERIFIED',
            errors=(f'invalid raw evidence JSON: {exc}',),
            artifact_digest=None,
        )

    expected = validator.expected_verdict(document)
    errors = tuple(validator.validate(document))
    return VerificationResult(
        valid=not errors,
        run_id=document.get('run_id') if isinstance(document.get('run_id'), str) else None,
        recorded_verdict=document.get('verdict') if isinstance(document.get('verdict'), str) else None,
        expected_verdict=expected,
        errors=errors,
        artifact_digest=validator.artifact_digest(document) if include_digest else None,
    )
