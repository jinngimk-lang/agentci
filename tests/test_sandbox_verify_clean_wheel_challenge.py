from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RED_CONTROL = ROOT / "examples" / "sandbox" / "v0alpha1-red-control-evidence.json"


def test_sandbox_verify_works_from_wheel_outside_repository(tmp_path: Path):
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    built = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheelhouse)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels = list(wheelhouse.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv"
    created = subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert created.returncode == 0, created.stdout + created.stderr

    python = venv_dir / "bin" / "python"
    agentci = venv_dir / "bin" / "agentci"
    installed = subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr

    evidence = tmp_path / "red-control.json"
    shutil.copy2(RED_CONTROL, evidence)
    outside = tmp_path / "outside"
    outside.mkdir()

    verified = subprocess.run(
        [str(agentci), "sandbox", "verify", str(evidence), "--json", "--print-digest"],
        cwd=outside,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    payload = json.loads(verified.stdout)
    assert payload["valid"] is True
    assert payload["recorded_verdict"] == "FAIL"
    assert payload["expected_verdict"] == "FAIL"
    assert payload["certification_claim"] is False
    assert payload["artifact_digest"].startswith("sha256:")
