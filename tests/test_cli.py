import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


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


def test_cli_pass_returns_zero_and_writes_artifacts(tmp_path: Path):
    result = run_cli('test', 'examples/evals.yaml', '--output-dir', str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'agentci-results.json').exists()
    assert (tmp_path / 'agentci-report.md').exists()
    assert '2/2 passed' in result.stdout


def test_cli_failure_returns_one_but_writes_artifacts(tmp_path: Path):
    result = run_cli('test', 'examples/evals-failing.yaml', '--output-dir', str(tmp_path))
    assert result.returncode == 1
    assert (tmp_path / 'agentci-results.json').exists()
    assert '0/1 passed' in result.stdout


def test_cli_invalid_input_returns_two(tmp_path: Path):
    invalid = tmp_path / 'invalid.yaml'
    invalid.write_text('suite: x\ncases: nope\n')
    result = run_cli('test', str(invalid), '--output-dir', str(tmp_path / 'out'))
    assert result.returncode == 2
    assert 'error:' in result.stderr.lower()


def test_showcase_list_json_exposes_truth_bounded_entries():
    result = run_cli('showcase', 'list', '--json')

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['schema_version'] == 'agentci.showcase.v1'

    items = payload['items']
    ids = [item['id'] for item in items]
    assert ids == sorted(ids)
    assert 'sandbox-doctor' in ids
    assert 'sandbox-sensitive-read-red-control' in ids

    by_id = {item['id']: item for item in items}
    doctor = by_id['sandbox-doctor']
    assert doctor['semantic_class'] == 'readiness-discovery'
    assert doctor['evidence_maturity'] == 'released-capability'
    assert doctor['released_command'] == ['agentci', 'sandbox', 'doctor', '--json']
    assert doctor['certification_claim'] is False

    red_control = by_id['sandbox-sensitive-read-red-control']
    assert red_control['semantic_class'] == 'false-pass-control'
    assert red_control['evidence_maturity'] == 'fixture'
    assert red_control['repository_path'] == 'examples/sandbox/v0alpha1-red-control-evidence.json'
    assert red_control['released_command'] == [
        'agentci',
        'sandbox',
        'verify',
        'examples/sandbox/v0alpha1-red-control-evidence.json',
        '--json',
        '--print-digest',
    ]
    assert red_control['certification_claim'] is False
