import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "sandbox-authority-v0alpha1.schema.json"


def _defs():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]


def test_five_authority_objects_are_explicit():
    defs = _defs()
    assert {"TrustRoot", "PrincipalAttestation", "CapabilityGrant", "Decision", "EnforcementReceipt"}.issubset(defs)


def test_decision_binds_principal_action_resource_context_and_epochs():
    required = set(_defs()["Decision"]["required"])
    assert {"principal_id", "action", "resource", "context_digest", "policy_digest", "policy_epoch", "authority_epoch", "effect"}.issubset(required)


def test_enforcement_receipt_binds_decision_and_effective_runtime_context():
    required = set(_defs()["EnforcementReceipt"]["required"])
    assert {"decision_id", "environment_fingerprint", "backend_instance_id", "policy_digest", "policy_epoch", "authority_epoch", "audit_digest"}.issubset(required)


def test_privilege_delta_has_non_boolean_classification():
    enum = _defs()["PrivilegeDelta"]["properties"]["classification"]["enum"]
    assert enum == ["contraction", "expansion", "lateral", "no-op", "unknown"]


def test_unknown_delta_is_not_implicitly_contraction():
    enum = _defs()["PrivilegeDelta"]["properties"]["classification"]["enum"]
    assert "unknown" in enum
    assert "contraction" in enum
    assert "unknown" != "contraction"
