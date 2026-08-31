import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str, cwd: Path | None = None):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')
    return subprocess.run(
        [sys.executable, '-m', 'agentci.cli', *args],
        cwd=cwd or ROOT,
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


def test_showcase_list_human_output_is_truth_bounded():
    result = run_cli('showcase', 'list')

    assert result.returncode == 0, result.stderr
    assert 'sandbox-doctor [released-capability]' in result.stdout
    assert 'sandbox-sensitive-read-red-control [fixture]' in result.stdout
    assert 'Truth boundary:' in result.stdout
    assert 'does not certify' in result.stdout


def test_showcase_show_json_returns_exact_entry():
    result = run_cli('showcase', 'show', 'sandbox-doctor', '--json')

    assert result.returncode == 0, result.stderr
    item = json.loads(result.stdout)
    assert item['id'] == 'sandbox-doctor'
    assert item['evidence_maturity'] == 'released-capability'
    assert item['released_command'] == ['agentci', 'sandbox', 'doctor', '--json']
    assert item['certification_claim'] is False


def test_showcase_show_human_output_exposes_command_and_boundary():
    result = run_cli('showcase', 'show', 'sandbox-sensitive-read-red-control')

    assert result.returncode == 0, result.stderr
    assert 'sandbox-sensitive-read-red-control [fixture]' in result.stdout
    assert 'Command: agentci sandbox verify examples/sandbox/v0alpha1-red-control-evidence.json --json --print-digest' in result.stdout
    assert 'Claim boundary:' in result.stdout
    assert 'does not certify a sandbox backend' in result.stdout


def test_showcase_show_unknown_id_fails_clearly():
    result = run_cli('showcase', 'show', 'missing-case', '--json')

    assert result.returncode == 2
    assert 'unknown showcase id: missing-case' in result.stderr.lower()


def test_cli_init_creates_runnable_starter_config(tmp_path: Path):
    target = tmp_path / 'agentci.yaml'
    result = run_cli('init', str(target))

    assert result.returncode == 0, result.stderr
    assert target.exists()
    assert f'Created: {target}' in result.stdout
    assert f'Next: agentci test {target}' in result.stdout

    output_dir = tmp_path / 'artifacts'
    test_result = run_cli('test', str(target), '--output-dir', str(output_dir))
    assert test_result.returncode == 0, test_result.stderr
    assert '1/1 passed' in test_result.stdout
    assert (output_dir / 'agentci-results.json').exists()
    assert (output_dir / 'agentci-report.md').exists()


def test_cli_init_defaults_to_agentci_yaml(tmp_path: Path):
    result = run_cli('init', cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'agentci.yaml').exists()
    assert 'Created: agentci.yaml' in result.stdout
    assert 'Next: agentci test agentci.yaml' in result.stdout


def test_cli_init_refuses_to_overwrite_existing_file(tmp_path: Path):
    target = tmp_path / 'agentci.yaml'
    target.write_text('sentinel\n')

    result = run_cli('init', str(target))

    assert result.returncode == 2
    assert target.read_text() == 'sentinel\n'
    assert 'error:' in result.stderr.lower()
