from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PASS_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"
RED_CONTROL = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def run_cli(*args: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "agentci.cli", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_verify_receipt_option_is_a_public_cli_surface(tmp_path: Path):
    """Breaks if the opt-in receipt path is absent from the public parser."""
    output = tmp_path / "verification-receipt.json"

    result = run_cli(
        "sandbox",
        "verify",
        str(PASS_EVIDENCE),
        "--receipt",
        str(output),
        "--json",
    )

    assert result.returncode != 2, result.stderr


def test_pass_without_signed_observer_and_cleanup_bindings_cannot_emit_receipt(tmp_path: Path):
    """Breaks if a legacy-valid PASS can create a receipt before strict bindings exist."""
    output = tmp_path / "verification-receipt.json"

    result = run_cli(
        "sandbox",
        "verify",
        str(PASS_EVIDENCE),
        "--receipt",
        str(output),
        "--json",
    )

    assert result.returncode == 1, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["recorded_verdict"] == "PASS"
    assert payload["expected_verdict"] == "PASS"
    assert payload["receipt_written"] is False
    assert payload["receipt_path"] == str(output)
    assert payload["receipt_errors"] == [
        "signed observer binding unavailable for mandatory telemetry source fixture-file-observer",
        "signed observer binding unavailable for mandatory telemetry source fixture-policy-observer",
        "signed cleanup binding unavailable for typed post-conditions",
    ]
    assert not output.exists(), "receipt creation must be atomic on strict-profile failure"


def test_verify_without_receipt_preserves_legacy_json_and_exit_snapshot():
    """Breaks if the opt-in receipt profile changes existing verify behavior."""
    result = run_cli("sandbox", "verify", str(RED_CONTROL), "--json", "--print-digest")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout) == {
        "artifact_digest": "sha256:63d7566ab80cc22d0beebba97ad21f7a85ef0d767d5d34ab4a55c96f799d890c",
        "certification_claim": False,
        "errors": [],
        "expected_verdict": "FAIL",
        "recorded_verdict": "FAIL",
        "run_id": "red-control-sensitive-read-001",
        "valid": True,
    }
