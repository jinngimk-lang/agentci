from pathlib import Path

import pytest

from agentci.config import ConfigError, load_suite


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding='utf-8')
    return path


def test_loads_local_command_target_without_fixture_actual(tmp_path: Path):
    suite = load_suite(write(tmp_path / 'suite.yaml', '''
suite: local-demo
target:
  type: local-command
  command: [python, target.py]
  timeout_seconds: 2
cases:
  - id: a
    input: hello
    expected: {success: true}
'''))
    assert suite.target.command == ('python', 'target.py')
    assert suite.target.timeout_seconds == 2
    assert suite.cases[0].actual is None


def test_rejects_shell_string_command(tmp_path: Path):
    path = write(tmp_path / 'suite.yaml', '''
suite: local-demo
target:
  type: local-command
  command: "python target.py"
cases:
  - id: a
    expected: {success: true}
''')
    with pytest.raises(ConfigError, match='command.*list'):
        load_suite(path)


def test_rejects_fixture_actual_when_target_is_configured(tmp_path: Path):
    path = write(tmp_path / 'suite.yaml', '''
suite: local-demo
target:
  type: local-command
  command: [python, target.py]
cases:
  - id: a
    actual: {success: true}
    expected: {success: true}
''')
    with pytest.raises(ConfigError, match='actual.*target'):
        load_suite(path)
