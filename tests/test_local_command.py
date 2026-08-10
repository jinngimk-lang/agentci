import json
from pathlib import Path
import sys

from agentci.runner import run_suite


def write_script(path: Path, source: str) -> Path:
    path.write_text(source, encoding='utf-8')
    return path


def write_suite(path: Path, command: list[str], timeout_seconds: float, expected_success: bool = True) -> Path:
    path.write_text(
        f'''suite: local-demo\ntarget:\n  type: local-command\n  command: {json.dumps(command)}\n  timeout_seconds: {timeout_seconds}\ncases:\n  - id: case-1\n    input: hello world\n    expected:\n      success: {str(expected_success).lower()}\n''',
        encoding='utf-8',
    )
    return path


def test_local_command_receives_json_input_and_agentci_measures_latency(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', '''
import json, sys
payload = json.load(sys.stdin)
print(json.dumps({"success": payload == {"id": "case-1", "input": "hello world"}, "cost_usd": 0.01}))
''')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 1)
    result = run_suite(suite, tmp_path / 'out')
    case = result.cases[0]
    assert case.passed is True
    assert case.actual_success is True
    assert case.latency_ms is not None and case.latency_ms >= 0
    assert case.cost_usd == 0.01


def test_timeout_is_a_normal_failed_case_even_when_false_was_expected(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'import time\ntime.sleep(1)\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 0.05, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    case = result.cases[0]
    assert case.passed is False
    assert case.actual_success is False
    assert any('timed out' in reason for reason in case.failure_reasons)


def test_nonzero_exit_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'raise SystemExit(7)\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 1, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('exited with code 7' in reason for reason in result.cases[0].failure_reasons)


def test_malformed_stdout_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'print("not-json")\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 1, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('invalid JSON' in reason for reason in result.cases[0].failure_reasons)


def test_missing_executable_is_a_normal_failed_case(tmp_path: Path):
    suite = write_suite(tmp_path / 'suite.yaml', [str(tmp_path / 'does-not-exist')], 1, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('executable not found' in reason for reason in result.cases[0].failure_reasons)
