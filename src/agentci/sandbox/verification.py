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
from scripts import lifecycle_attestation as lifecycle_attestation_module
from scripts import runtime_environment_attestation as runtime_environment_attestation_module
from scripts import validate_sandbox_evidence as validator

from .receipt import (
    ReceiptBundleError,
    assemble_receipt,
    load_receipt_bundle,
    write_receipt_atomic,
)
from .resource_loader import INSTALLED_ROOT, SOURCE_ROOT, canonical_resource_json


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    run_id: str | None
    recorded_verdict: str | None
    expected_verdict: str
    errors: tuple[str, ...]
    artifact_digest: str | None
    certification_claim: bool = False
    receipt_written: bool | None = None
    receipt_path: str | None = None
    receipt_errors: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.receipt_written is None:
            payload.pop('receipt_written')
            payload.pop('receipt_path')
            payload.pop('receipt_errors')
        else:
            payload['evidence_valid'] = self.valid
            payload['receipt_valid'] = self.receipt_written and not self.receipt_errors
        return payload


def _configure_canonical_resources() -> None:
    """Point the unchanged canonical validator at wheel data when needed."""
    source_schema = SOURCE_ROOT / 'schemas' / 'sandbox-certification-v0alpha1.schema.json'
    if source_schema.is_file():
        return

    validator.SCHEMA_PATH = INSTALLED_ROOT / 'schema' / 'sandbox-certification-v0alpha1.schema.json'
    validator.TEST_CASE_DIR = INSTALLED_ROOT / 'testcases'
    execution_attestation_module.ATTESTATION_DIR = INSTALLED_ROOT / 'execution-attestations'
    lifecycle_attestation_module.ATTESTATION_DIR = INSTALLED_ROOT / 'lifecycle-attestations'
    runtime_environment_attestation_module.ATTESTATION_DIR = INSTALLED_ROOT / 'runtime-environment-attestations'
    validator._schema_validator.cache_clear()
    validator._test_case_validator.cache_clear()
    validator._load_test_case.cache_clear()


def _unavailable_receipt_binding_errors(document: dict[str, object]) -> tuple[str, ...]:
    """Describe the strict receipt bindings that Stage A cannot yet verify."""
    telemetry = document.get('telemetry')
    errors = []
    if isinstance(telemetry, list):
        for source in telemetry:
            if isinstance(source, dict) and source.get('coverage') == 'mandatory':
                source_id = source.get('source_id')
                errors.append(f'signed observer binding unavailable for mandatory telemetry source {source_id}')
    errors.append('signed cleanup binding unavailable for typed post-conditions')
    return tuple(errors)


def verify_evidence_file(
    path: Path,
    *,
    include_digest: bool = False,
    receipt_path: Path | None = None,
    receipt_bundle_path: Path | None = None,
) -> VerificationResult:
    """Validate one EvidenceEnvelope without treating verdict FAIL as tool failure.

    ``valid`` means the envelope faithfully satisfies the canonical contract,
    including its recorded verdict. It does not mean the sandbox verdict is
    PASS and it is never a certification claim.
    """
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
    receipt_written = False if receipt_path is not None else None
    receipt_errors: tuple[str, ...] | None = None
    if receipt_path is not None:
        if receipt_bundle_path is None:
            receipt_errors = _unavailable_receipt_binding_errors(document)
        elif errors:
            receipt_errors = ('E_RECEIPT_EVIDENCE_INVALID',)
        else:
            mandatory_sources = tuple(
                source['source_id']
                for source in document.get('telemetry', [])
                if isinstance(source, dict)
                and source.get('coverage') == 'mandatory'
                and isinstance(source.get('source_id'), str)
            )
            try:
                bundle = load_receipt_bundle(receipt_bundle_path, mandatory_sources=mandatory_sources)
                case_id = document['case_id']
                run_id = document['run_id']
                assembled = assemble_receipt(
                    document,
                    test_case=canonical_resource_json(
                        f'examples/sandbox/testcases/{case_id}.json',
                        f'testcases/{case_id}.json',
                    ),
                    schema_document=canonical_resource_json(
                        'schemas/sandbox-certification-v0alpha1.schema.json',
                        'schema/sandbox-certification-v0alpha1.schema.json',
                    ),
                    runtime_attestation=canonical_resource_json(
                        f'examples/sandbox/runtime-environment-attestations/{run_id}.json',
                        f'runtime-environment-attestations/{run_id}.json',
                    ),
                    execution_attestation=canonical_resource_json(
                        f'examples/sandbox/execution-attestations/{run_id}.json',
                        f'execution-attestations/{run_id}.json',
                    ),
                    observer_attestations=bundle['observer_attestations'],
                    cleanup_attestation=bundle['cleanup_attestation'],
                )
                receipt_errors = assembled.error_codes
                if assembled.receipt_valid and assembled.manifest is not None:
                    write_receipt_atomic(receipt_path, assembled.manifest)
                    receipt_written = True
            except ReceiptBundleError as exc:
                receipt_errors = (exc.code,)
            except (json.JSONDecodeError, ValueError):
                receipt_errors = ('E_RECEIPT_BUNDLE_INVALID',)
    return VerificationResult(
        valid=not errors,
        run_id=document.get('run_id') if isinstance(document.get('run_id'), str) else None,
        recorded_verdict=document.get('verdict') if isinstance(document.get('verdict'), str) else None,
        expected_verdict=expected,
        errors=errors,
        artifact_digest=validator.artifact_digest(document) if include_digest else None,
        receipt_written=receipt_written,
        receipt_path=str(receipt_path) if receipt_path is not None else None,
        receipt_errors=receipt_errors,
    )
