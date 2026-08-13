#!/usr/bin/env python3
"""Fail-closed semantic validator for the S0 Sandbox AuthorityBundle.

This validates authority provenance and reference integrity only. It is not a
policy engine and does not grant authority. Unknown or ambiguous authority is
rejected rather than inferred.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "sandbox-authority-v0alpha1.schema.json"


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_authority_json(raw: str) -> dict[str, Any]:
    document = json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    if not isinstance(document, dict):
        raise ValueError("authority root must be a JSON object")
    return document


def _duplicates(values: list[Any]) -> set[Any]:
    return {value for value in values if value is not None and values.count(value) > 1}


def _schema_validator() -> Draft202012Validator:
    schema = load_authority_json(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _unique_index(items: list[dict[str, Any]], field: str, errors: list[str], label: str) -> dict[str, dict[str, Any]]:
    values = [item.get(field) for item in items]
    duplicates = _duplicates(values)
    for value in sorted(duplicates, key=str):
        errors.append(f"duplicate {label} {value}")
    return {
        item[field]: item
        for item in items
        if isinstance(item.get(field), str) and item.get(field) not in duplicates
    }


def _validate_delegation_subset(grant: dict[str, Any], parent: dict[str, Any], errors: list[str]) -> None:
    """Require a delegated child to be provably non-expanding.

    v0alpha1 intentionally has no provider-specific resource hierarchy or
    action lattice. Therefore equality is the only portable subset relation we
    can prove for those dimensions. Time and revocation may narrow/freshen.
    """
    grant_id = grant.get("grant_id")
    parent_id = parent.get("grant_id")
    for field in ("action", "resource", "context_digest", "audience", "pep", "policy_digest", "authority_epoch"):
        if grant.get(field) != parent.get(field):
            errors.append(f"grant {grant_id} expands or changes parent {parent_id} {field}")
    if grant.get("not_before") < parent.get("not_before"):
        errors.append(f"grant {grant_id} starts before delegated parent {parent_id}")
    if grant.get("expires_at") > parent.get("expires_at"):
        errors.append(f"grant {grant_id} expires after delegated parent {parent_id}")
    if grant.get("revocation_epoch") < parent.get("revocation_epoch"):
        errors.append(f"grant {grant_id} weakens delegated parent {parent_id} revocation epoch")


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema_errors = sorted(_schema_validator().iter_errors(document), key=lambda error: list(error.path))
    if schema_errors:
        errors.extend(f"schema validation failed at {'/'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in schema_errors)
        return errors

    roots = document.get("trust_roots", [])
    attestations = document.get("principal_attestations", [])
    grants = document.get("grants", [])
    decisions = document.get("decisions", [])
    receipts = document.get("enforcement_receipts", [])

    roots_by_id = _unique_index(roots, "trust_root_id", errors, "trust_root_id")
    attestations_by_id = _unique_index(attestations, "attestation_id", errors, "attestation_id")
    grants_by_id = _unique_index(grants, "grant_id", errors, "grant_id")
    decisions_by_id = _unique_index(decisions, "decision_id", errors, "decision_id")
    _unique_index(receipts, "receipt_id", errors, "receipt_id")

    principal_ids = [item.get("principal_id") for item in attestations]
    duplicate_principals = _duplicates(principal_ids)
    for value in sorted(duplicate_principals, key=str):
        errors.append(f"principal_id {value} does not resolve uniquely")
    attestations_by_principal = {
        item["principal_id"]: item
        for item in attestations
        if isinstance(item.get("principal_id"), str) and item.get("principal_id") not in duplicate_principals
    }

    root_identities = {item.get("root_identity") for item in roots if isinstance(item.get("root_identity"), str)}
    root_tenants = {item.get("tenant_id") for item in roots}

    for attestation in attestations:
        if attestation.get("tenant_id") not in root_tenants:
            errors.append(f"attestation {attestation.get('attestation_id')} has no tenant TrustRoot")
        if attestation.get("not_before") >= attestation.get("expires_at"):
            errors.append(f"attestation {attestation.get('attestation_id')} validity interval is invalid")

    for grant in grants:
        grant_id = grant.get("grant_id")
        issuer = grant.get("issuer_principal_id")
        subject = grant.get("subject_principal_id")
        parent_id = grant.get("parent_grant_id")

        if issuer not in root_identities and issuer not in attestations_by_principal:
            errors.append(f"grant {grant_id} issuer {issuer} is not a trusted root or uniquely attested principal")
        if subject not in attestations_by_principal:
            errors.append(f"grant {grant_id} subject {subject} does not resolve to one PrincipalAttestation")
        if grant.get("not_before") >= grant.get("expires_at"):
            errors.append(f"grant {grant_id} validity interval is invalid")

        parent = None
        if parent_id is not None:
            parent = grants_by_id.get(parent_id)
            if parent is None:
                errors.append(f"grant {grant_id} references missing parent grant {parent_id}")
            elif not parent.get("delegation_allowed"):
                errors.append(f"grant {grant_id} parent {parent_id} does not permit delegation")
            elif parent.get("subject_principal_id") != issuer:
                errors.append(f"grant {grant_id} issuer is not the delegated parent subject")
            else:
                _validate_delegation_subset(grant, parent, errors)

        # Identity attestation establishes who the issuer is, not that the
        # issuer has authority to mint a new grant. Non-root issuers must trace
        # to an explicit delegating parent grant; missing provenance fails closed.
        if issuer not in root_identities and parent_id is None:
            errors.append(f"grant {grant_id} non-root issuer {issuer} requires delegated parent authority")

    decision_keys: dict[tuple[Any, ...], str] = {}
    for decision in decisions:
        decision_id = decision.get("decision_id")
        principal = decision.get("principal_id")
        if principal not in attestations_by_principal:
            errors.append(f"decision {decision_id} principal {principal} does not resolve uniquely")
        grant_ids = decision.get("grant_ids", [])
        if decision.get("effect") == "PERMIT" and not grant_ids:
            errors.append(f"PERMIT decision {decision_id} requires at least one CapabilityGrant")
        for grant_id in grant_ids:
            grant = grants_by_id.get(grant_id)
            if grant is None:
                errors.append(f"decision {decision_id} references missing grant {grant_id}")
                continue
            expected = {
                "subject_principal_id": principal,
                "action": decision.get("action"),
                "resource": decision.get("resource"),
                "context_digest": decision.get("context_digest"),
                "policy_digest": decision.get("policy_digest"),
                "authority_epoch": decision.get("authority_epoch"),
            }
            for field, expected_value in expected.items():
                if grant.get(field) != expected_value:
                    errors.append(f"decision {decision_id} grant {grant_id} {field} mismatch")
        key = (
            principal,
            decision.get("action"),
            decision.get("resource"),
            decision.get("context_digest"),
            decision.get("policy_digest"),
            decision.get("policy_epoch"),
            decision.get("authority_epoch"),
        )
        prior_effect = decision_keys.get(key)
        if prior_effect is not None and prior_effect != decision.get("effect"):
            errors.append(f"conflicting PERMIT/DENY decisions for one principal/action/resource/context authority state")
        decision_keys[key] = decision.get("effect")

    for receipt in receipts:
        receipt_id = receipt.get("receipt_id")
        decision = decisions_by_id.get(receipt.get("decision_id"))
        if decision is None:
            errors.append(f"receipt {receipt_id} references missing decision {receipt.get('decision_id')}")
            continue
        for field in ("policy_digest", "policy_epoch", "authority_epoch"):
            if receipt.get(field) != decision.get(field):
                errors.append(f"receipt {receipt_id} {field} does not match decision")
        if decision.get("effect") == "DENY" and receipt.get("result") == "enforced":
            errors.append(f"receipt {receipt_id} cannot report enforced for a DENY decision")

    for delta in document.get("privilege_deltas", []):
        eligible = delta.get("automatic_application_eligible", False)
        if eligible and (delta.get("classification") != "contraction" or not delta.get("obligations_not_weaker")):
            errors.append("automatic privilege application is allowed only for proven contraction with non-weaker obligations")

    # Explicitly use the indexes so schema-only duplicate arrays cannot masquerade
    # as a resolvable authority graph even if no downstream reference happens to touch them.
    if len(roots_by_id) != len(roots):
        pass
    if len(attestations_by_id) != len(attestations):
        pass

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        document = load_authority_json(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid raw AuthorityBundle JSON: {exc}")
        return 1
    errors = validate(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: AuthorityBundle semantic graph is internally consistent and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
