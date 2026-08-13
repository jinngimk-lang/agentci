"""Installed adapter for the canonical AgentCI S0 EvidenceEnvelope validator.

This module intentionally does not implement verdict semantics. It delegates to
``scripts.validate_sandbox_evidence`` so there is one S0 validator while the
Developer Preview product surface remains a thin presentation layer.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from scripts.validate_sandbox_evidence import (
    artifact_digest,
    expected_verdict,
    load_evidence_json,
    validate,
)


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


def verify_evidence_file(path: Path, *, include_digest: bool = False) -> VerificationResult:
    """Validate one EvidenceEnvelope without treating verdict FAIL as tool failure.

    ``valid`` means the envelope faithfully satisfies the canonical contract,
    including its recorded verdict. It does not mean the sandbox verdict is
    PASS and it is never a certification claim.
    """
    raw = path.read_text(encoding='utf-8')
    try:
        document = load_evidence_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return VerificationResult(
            valid=False,
            run_id=None,
            recorded_verdict=None,
            expected_verdict='UNVERIFIED',
            errors=(f'invalid raw evidence JSON: {exc}',),
            artifact_digest=None,
        )

    expected = expected_verdict(document)
    errors = tuple(validate(document))
    return VerificationResult(
        valid=not errors,
        run_id=document.get('run_id') if isinstance(document.get('run_id'), str) else None,
        recorded_verdict=document.get('verdict') if isinstance(document.get('verdict'), str) else None,
        expected_verdict=expected,
        errors=errors,
        artifact_digest=artifact_digest(document) if include_digest else None,
    )
