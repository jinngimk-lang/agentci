from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RED_CONTROL = ROOT / 'examples' / 'sandbox' / 'v0alpha1-red-control-evidence.json'


def run_cli(*args: str):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    return subprocess.run(
        [sys.executable, '-m', 'agentci.cli', *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_verify_accepts_valid_fail_envelope_without_calling_it_pass():
    result = run_cli('sandbox', 'verify', str(RED_CONTROL), '--json', '--print-digest')
    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(result.stdout)
    assert payload['valid'] is True
    assert payload['run_id'] == 'red-control-sensitive-read-001'
    assert payload['recorded_verdict'] == 'FAIL'
    assert payload['expected_verdict'] == 'FAIL'
    assert payload['errors'] == []
    assert payload['artifact_digest'].startswith('sha256:')
    assert payload['certification_claim'] is False


def test_verify_rejects_tampered_envelope(tmp_path: Path):
    document = json.loads(RED_CONTROL.read_text(encoding='utf-8'))
    document['verdict'] = 'PASS'
    tampered = tmp_path / 'tampered.json'
    tampered.write_text(json.dumps(document), encoding='utf-8')

    result = run_cli('sandbox', 'verify', str(tampered), '--json')
    assert result.returncode == 1

    payload = json.loads(result.stdout)
    assert payload['valid'] is False
    assert payload['recorded_verdict'] == 'PASS'
    assert payload['expected_verdict'] != 'PASS'
    assert payload['errors']
    assert payload['certification_claim'] is False


def test_verify_missing_file_is_usage_or_io_error():
    result = run_cli('sandbox', 'verify', 'does-not-exist.json', '--json')
    assert result.returncode == 2
    assert 'error:' in result.stderr.lower()
