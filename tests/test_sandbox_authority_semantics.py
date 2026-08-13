import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_sandbox_authority.py"


def _digest(char):
    return "sha256:" + char * 64


def _bundle():
    return {
        "apiVersion": "agentci.dev/sandbox/v0alpha1",
        "kind": "AuthorityBundle",
        "trust_roots": [
            {
                "trust_root_id": "root-1",
                "tenant_id": "tenant-1",
                "root_identity": "owner-key-1",
                "baseline_digest": _digest("1"),
                "authority_epoch": 7,
            }
        ],
        "principal_attestations": [
            {
                "attestation_id": "att-1",
                "principal_type": "workload",
                "principal_id": "workload-1",
                "tenant_id": "tenant-1",
                "workload_id": "workload-1",
                "session_id": "session-1",
                "run_id": "run-1",
                "attestation_digest": _digest("2"),
                "not_before": "2026-08-13T00:00:00Z",
                "expires_at": "2026-08-13T01:00:00Z",
            }
        ],
        "grants": [
            {
                "grant_id": "grant-1",
                "issuer_principal_id": "owner-1",
                "subject_principal_id": "workload-1",
                "action": "read",
                "resource": "/workspace",
                "context_digest": _digest("3"),
                "audience": "sandbox-pep",
                "pep": "sandbox-pep",
                "delegation_allowed": False,
                "not_before": "2026-08-13T00:00:00Z",
                "expires_at": "2026-08-13T01:00:00Z",
                "revocation_epoch": 0,
                "policy_digest": _digest("4"),
                "authority_epoch": 7,
            }
        ],
        "decisions": [
            {
                "decision_id": "decision-1",
                "principal_id": "workload-1",
                "action": "read",
                "resource": "/workspace",
                "context_digest": _digest("3"),
                "grant_ids": ["grant-1"],
                "policy_digest": _digest("4"),
                "policy_epoch": 3,
                "authority_epoch": 7,
                "effect": "PERMIT",
                "obligations": [],
            }
        ],
        "enforcement_receipts": [
            {
                "receipt_id": "receipt-1",
                "decision_id": "decision-1",
                "environment_fingerprint": _digest("5"),
                "backend_instance_id": "backend-1",
                "policy_digest": _digest("4"),
                "policy_epoch": 3,
                "authority_epoch": 7,
                "enforced_at_utc": "2026-08-13T00:00:02Z",
                "enforced_at_monotonic_ns": 2000,
                "result": "enforced",
                "audit_digest": _digest("6"),
            }
        ],
        "privilege_deltas": [
            {
                "old_authority_digest": _digest("7"),
                "new_authority_digest": _digest("8"),
                "classification": "contraction",
                "obligations_not_weaker": True,
                "evidence_digest": _digest("9"),
                "automatic_application_eligible": True,
            }
        ],
    }


def _run(tmp_path, bundle):
    assert VALIDATOR.is_file(), "authority semantic validator must exist"
    path = tmp_path / "authority.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True)


def test_valid_authority_graph_is_accepted(tmp_path):
    result = _run(tmp_path, _bundle())
    assert result.returncode == 0, result.stdout + result.stderr


def test_duplicate_typed_ids_are_rejected(tmp_path):
    bundle = _bundle()
    duplicate = dict(bundle["decisions"][0])
    duplicate["effect"] = "DENY"
    bundle["decisions"].append(duplicate)
    assert _run(tmp_path, bundle).returncode != 0


def test_dangling_receipt_decision_is_rejected(tmp_path):
    bundle = _bundle()
    bundle["enforcement_receipts"][0]["decision_id"] = "missing-decision"
    assert _run(tmp_path, bundle).returncode != 0


def test_grant_and_decision_semantics_must_match(tmp_path):
    bundle = _bundle()
    bundle["decisions"][0]["resource"] = "/secret"
    assert _run(tmp_path, bundle).returncode != 0


def test_unknown_or_expanding_delta_cannot_be_auto_applied(tmp_path):
    for classification in ("unknown", "lateral", "expansion"):
        bundle = _bundle()
        bundle["privilege_deltas"][0]["classification"] = classification
        bundle["privilege_deltas"][0]["automatic_application_eligible"] = True
        assert _run(tmp_path, bundle).returncode != 0


def test_raw_duplicate_authority_key_is_rejected(tmp_path):
    assert VALIDATOR.is_file(), "authority semantic validator must exist"
    raw = json.dumps(_bundle()).replace('"effect": "PERMIT"', '"effect": "DENY", "effect": "PERMIT"', 1)
    path = tmp_path / "authority-duplicate.json"
    path.write_text(raw, encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True)
    assert result.returncode != 0
