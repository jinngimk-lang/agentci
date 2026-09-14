import json
from pathlib import Path

import pytest

from agentci.config import ConfigError, load_suite


def write(path: Path, content: str) -> Path:
    path.write_text(content, encoding='utf-8')
    return path


def test_load_valid_yaml(tmp_path: Path):
    path = write(tmp_path / 'suite.yaml', '''
suite: demo
cases:
  - id: a
    input: hello
    actual:
      success: true
      latency_ms: 100
      cost_usd: 0.01
    expected:
      success: true
      max_latency_ms: 100
      max_cost_usd: 0.02
''')
    suite = load_suite(path)
    assert suite.name == 'demo'
    assert suite.cases[0].id == 'a'
    assert suite.cases[0].actual.latency_ms == 100


def test_load_valid_json(tmp_path: Path):
    path = tmp_path / 'suite.json'
    path.write_text(json.dumps({
        'suite': 'demo',
        'cases': [{
            'id': 'a', 'input': 'hello',
            'actual': {'success': True},
            'expected': {'success': True},
        }],
    }), encoding='utf-8')
    assert load_suite(path).cases[0].actual.cost_usd is None


def test_rejects_missing_suite(tmp_path: Path):
    path = write(tmp_path / 'bad.yaml', 'cases: []\n')
    with pytest.raises(ConfigError, match='suite'):
        load_suite(path)


def test_rejects_empty_cases(tmp_path: Path):
    path = write(tmp_path / 'bad.yaml', 'suite: empty\ncases: []\n')
    with pytest.raises(ConfigError, match='cases.*at least one'):
        load_suite(path)


def test_rejects_duplicate_ids(tmp_path: Path):
    path = write(tmp_path / 'bad.yaml', '''
suite: demo
cases:
  - id: a
    actual: {success: true}
    expected: {success: true}
  - id: a
    actual: {success: true}
    expected: {success: true}
''')
    with pytest.raises(ConfigError, match='duplicate'):
        load_suite(path)


@pytest.mark.parametrize('section', ['actual', 'expected'])
def test_rejects_missing_success(tmp_path: Path, section: str):
    actual = '{}' if section == 'actual' else '{success: true}'
    expected = '{}' if section == 'expected' else '{success: true}'
    path = write(tmp_path / 'bad.yaml', f'''
suite: demo
cases:
  - id: a
    actual: {actual}
    expected: {expected}
''')
    with pytest.raises(ConfigError, match=f'{section}.*success'):
        load_suite(path)


@pytest.mark.parametrize(
    ('section', 'key', 'value'),
    [
        ('actual', 'latency_ms', '.nan'),
        ('actual', 'cost_usd', '.inf'),
        ('expected', 'max_latency_ms', '.nan'),
        ('expected', 'max_cost_usd', '.inf'),
    ],
)
def test_rejects_non_finite_yaml_numbers(tmp_path: Path, section: str, key: str, value: str):
    actual_extra = f'      {key}: {value}\n' if section == 'actual' else ''
    expected_extra = f'      {key}: {value}\n' if section == 'expected' else ''
    path = write(tmp_path / 'bad.yaml', f'''
suite: finite-only
cases:
  - id: a
    actual:
      success: true
{actual_extra}    expected:
      success: true
{expected_extra}''')
    with pytest.raises(ConfigError, match=f'{key}.*finite'):
        load_suite(path)


@pytest.mark.parametrize(
    'raw',
    [
        '{"suite":"x","cases":[{"id":"a","actual":{"success":true,"latency_ms":NaN},"expected":{"success":true}}]}',
        '{"suite":"x","cases":[{"id":"a","actual":{"success":true},"expected":{"success":true,"max_cost_usd":Infinity}}]}',
    ],
)
def test_rejects_non_finite_json_numbers(tmp_path: Path, raw: str):
    path = write(tmp_path / 'bad.json', raw)
    with pytest.raises(ConfigError, match='finite'):
        load_suite(path)


def test_rejects_unsupported_extension(tmp_path: Path):
    path = write(tmp_path / 'suite.txt', 'suite: demo\ncases: []\n')
    with pytest.raises(ConfigError, match='extension'):
        load_suite(path)
