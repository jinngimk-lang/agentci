from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PASS_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-pass-evidence.json"
FAIL_EVIDENCE = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"
CANONICAL_BUNDLES = ROOT / "examples" / "sandbox" / "receipt-bundles"
BUNDLE_FILES = {
    "observer-fixture-file-observer.json",
    "observer-fixture-policy-observer.json",
    "cleanup.json",
}


def run_cli(*args: str, cwd: Path = ROOT):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    return subprocess.run(
        [sys.executable, "-m", "agentci.cli", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def _copy_bundle(run_id: str, target: Path) -> Path:
    source = CANONICAL_BUNDLES / run_id
    assert source.is_dir(), "GREEN must package canonical signed observer/cleanup bundle resources"
    assert {entry.name for entry in source.iterdir()} == BUNDLE_FILES
    assert all(entry.is_file() for entry in source.iterdir()), "bundle discovery must not recurse"
    shutil.copytree(source, target)
    return target


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("missing", "E_RECEIPT_BUNDLE_REQUIRED_FILE_MISSING"),
        ("unexpected", "E_RECEIPT_BUNDLE_UNEXPECTED_ENTRY"),
        ("nested", "E_RECEIPT_BUNDLE_UNEXPECTED_ENTRY"),
    ],
)
def test_bundle_loader_requires_exact_non_recursive_safe_file_set(
    tmp_path: Path,
    mutation: str,
    code: str,
):
    from agentci.sandbox.receipt import ReceiptBundleError, load_receipt_bundle

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for filename in BUNDLE_FILES:
        (bundle / filename).write_text("{}", encoding="utf-8")
    if mutation == "missing":
        (bundle / "cleanup.json").unlink()
    elif mutation == "unexpected":
        (bundle / "attacker-controlled.json").write_text("{}", encoding="utf-8")
    else:
        (bundle / "nested").mkdir()

    with pytest.raises(ReceiptBundleError) as caught:
        load_receipt_bundle(
            bundle,
            mandatory_sources=("fixture-file-observer", "fixture-policy-observer"),
        )

    assert caught.value.code == code


@pytest.mark.parametrize(
    ("evidence", "run_id", "verdict"),
    [
        (PASS_EVIDENCE, "pass-sensitive-read-denied-001", "PASS"),
        (FAIL_EVIDENCE, "red-control-sensitive-read-001", "FAIL"),
    ],
)
def test_cli_explicit_bundle_writes_portable_replayable_receipt(
    tmp_path: Path,
    evidence: Path,
    run_id: str,
    verdict: str,
):
    from agentci.sandbox.receipt import validate_receipt_manifest

    bundle = _copy_bundle(run_id, tmp_path / "bundle")
    output = tmp_path / "receipt.json"
    external_cwd = tmp_path / "outside-repository"
    external_cwd.mkdir()
    result = run_cli(
        "sandbox",
        "verify",
        str(evidence),
        "--receipt",
        str(output),
        "--receipt-bundle",
        str(bundle),
        "--json",
        cwd=external_cwd,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["evidence_valid"] is True
    assert payload["receipt_valid"] is True
    assert payload["receipt_written"] is True
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["recorded_verdict"] == verdict
    assert manifest["expected_verdict"] == verdict
    assert manifest["certification_claim"] is False
    assert validate_receipt_manifest(manifest).valid is True


def test_cli_receipt_bundle_is_only_accepted_with_receipt_output(tmp_path: Path):
    result = run_cli(
        "sandbox",
        "verify",
        str(PASS_EVIDENCE),
        "--receipt-bundle",
        str(tmp_path / "bundle"),
        "--json",
    )

    assert result.returncode == 2
    assert "--receipt-bundle requires --receipt" in result.stderr


def test_cli_missing_explicit_bundle_fails_closed_without_output(tmp_path: Path):
    output = tmp_path / "receipt.json"
    result = run_cli(
        "sandbox",
        "verify",
        str(PASS_EVIDENCE),
        "--receipt",
        str(output),
        "--receipt-bundle",
        str(tmp_path / "missing-bundle"),
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["evidence_valid"] is True
    assert payload["receipt_valid"] is False
    assert payload["receipt_written"] is False
    assert payload["receipt_errors"] == ["E_RECEIPT_BUNDLE_UNAVAILABLE"]
    assert not output.exists()


def test_atomic_writer_late_replace_failure_preserves_sentinel_and_leaves_no_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from agentci.sandbox.receipt import write_receipt_atomic

    output = tmp_path / "receipt.json"
    sentinel = b"preexisting-user-content\n"
    output.write_bytes(sentinel)

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("injected late replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected late replace failure"):
        write_receipt_atomic(output, {"kind": "EvidenceVerificationReceiptManifest"})

    assert output.read_bytes() == sentinel
    assert sorted(tmp_path.iterdir()) == [output]


def test_atomic_writer_successfully_replaces_with_parseable_receipt(tmp_path: Path):
    from agentci.sandbox.receipt import write_receipt_atomic
    from tests.test_sandbox_receipt_contract_red import PASS_EVIDENCE as CONTRACT_PASS
    from tests.test_sandbox_receipt_contract_red import _complete_bundle, _replay, _success

    document, bundle = _complete_bundle(CONTRACT_PASS)
    manifest = _success(document, bundle).manifest
    output = tmp_path / "receipt.json"
    output.write_text("sentinel", encoding="utf-8")

    write_receipt_atomic(output, manifest)

    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed == manifest
    assert _replay(parsed, bundle).valid is True
    assert sorted(tmp_path.iterdir()) == [output]
