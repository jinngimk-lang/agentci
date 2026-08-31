from __future__ import annotations

from pathlib import Path
import tomllib

import agentci


ROOT = Path(__file__).resolve().parents[1]


def test_python_version_matches_distribution_version():
    pyproject = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    assert agentci.__version__ == pyproject['project']['version'] == '0.3.0.dev0'


def test_external_verifier_documents_clean_wheel_verify_gate():
    text = (ROOT / 'docs' / 'testing' / 'external-agent-verification.md').read_text(encoding='utf-8').lower()
    assert 'clean-wheel' in text
    assert 'agentci sandbox verify' in text
    assert 'valid evidence' in text
    assert 'not a security certification' in text
