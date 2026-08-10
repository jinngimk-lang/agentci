import json
import os
from pathlib import Path
import signal
import sys

import pytest

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
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 5)
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


@pytest.mark.skipif(sys.platform != 'linux', reason='process-state assertion uses Linux /proc')
def test_timeout_terminates_descendant_processes(tmp_path: Path):
    pid_file = tmp_path / 'descendant.pid'
    child_code = 'import time; time.sleep(20)'
    script = write_script(tmp_path / 'target.py', f'''
from pathlib import Path
import subprocess, sys, time
child = subprocess.Popen(
    [sys.executable, '-c', {child_code!r}],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
Path({str(pid_file)!r}).write_text(str(child.pid), encoding='utf-8')
time.sleep(20)
''')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 2.5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert pid_file.exists(), 'reproduction did not spawn the descendant before timeout'
    pid = int(pid_file.read_text(encoding='utf-8'))

    def running() -> bool:
        stat = Path(f'/proc/{pid}/stat')
        if stat.exists():
            fields = stat.read_text(encoding='utf-8').split()
            if len(fields) > 2 and fields[2] == 'Z':
                return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    try:
        assert running() is False, 'descendant survived AgentCI timeout cleanup'
    finally:
        if running():
            os.kill(pid, signal.SIGKILL)


def test_nonzero_exit_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'raise SystemExit(7)\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('exited with code 7' in reason for reason in result.cases[0].failure_reasons)


def test_malformed_stdout_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'print("not-json")\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('invalid JSON' in reason for reason in result.cases[0].failure_reasons)


def test_missing_executable_is_a_normal_failed_case(tmp_path: Path):
    suite = write_suite(tmp_path / 'suite.yaml', [str(tmp_path / 'does-not-exist')], 5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('executable not found' in reason for reason in result.cases[0].failure_reasons)


def test_non_utf8_stdout_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'import sys\nsys.stdout.buffer.write(b"\\xff")\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('UTF-8' in reason for reason in result.cases[0].failure_reasons)


def test_non_finite_cost_is_a_normal_failed_case(tmp_path: Path):
    script = write_script(tmp_path / 'target.py', 'print(\'{"success": true, "cost_usd": NaN}\')\n')
    suite = write_suite(tmp_path / 'suite.yaml', [sys.executable, str(script)], 5, expected_success=False)
    result = run_suite(suite, tmp_path / 'out')
    assert result.cases[0].passed is False
    assert any('cost_usd' in reason for reason in result.cases[0].failure_reasons)
