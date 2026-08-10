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
