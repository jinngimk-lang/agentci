from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PASS_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"


def run_cli(*args: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    return subprocess.run(
        [sys.executable, "-m", "agentci.cli", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_receipt_failure_preserves_preexisting_output_sentinel_atomically(tmp_path: Path):
    output = tmp_path / "receipt.json"
    sentinel = b"preexisting-user-content\n"
    output.write_bytes(sentinel)

    result = run_cli("sandbox", "verify", str(PASS_EVIDENCE), "--receipt", str(output), "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["evidence_valid"] is True
    assert payload["receipt_valid"] is False
    assert payload["receipt_written"] is False
    assert output.read_bytes() == sentinel


def test_legacy_pass_json_snapshot_is_unchanged_without_receipt():
    result = run_cli("sandbox", "verify", str(PASS_EVIDENCE), "--json")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "artifact_digest": None,
        "certification_claim": False,
        "errors": [],
        "expected_verdict": "PASS",
        "recorded_verdict": "PASS",
        "run_id": "pass-sensitive-read-denied-001",
        "valid": True,
    }


def test_legacy_pass_text_snapshot_is_unchanged_without_receipt():
    result = run_cli("sandbox", "verify", str(PASS_EVIDENCE))

    assert result.returncode == 0
    assert result.stdout == (
        "Evidence envelope: valid\n"
        "Run: pass-sensitive-read-denied-001\n"
        "Recorded verdict: PASS\n"
        "Expected verdict: PASS\n"
        "Truth boundary: valid evidence is not a security certification; inspect the recorded verdict and limitations.\n"
    )


def test_legacy_missing_file_snapshot_is_unchanged_without_receipt():
    result = run_cli("sandbox", "verify", "does-not-exist.json", "--json")

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "error: [Errno 2] No such file or directory: 'does-not-exist.json'\n"
