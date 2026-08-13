from __future__ import annotations

from pathlib import Path

import pytest

from agentci.sandbox.resource_loader import canonical_resource_text


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ('repository_path', 'installed_path'),
    [
        ('schemas/sandbox-certification-v0alpha1.schema.json', 'schema/sandbox-certification-v0alpha1.schema.json'),
        ('schemas/sandbox-authority-v0alpha1.schema.json', 'authority-schema/sandbox-authority-v0alpha1.schema.json'),
        ('examples/sandbox/testcases/sandbox-sensitive-canary-v0alpha1.json', 'testcases/sandbox-sensitive-canary-v0alpha1.json'),
        ('examples/sandbox/execution-attestations/red-control-sensitive-read-001.json', 'execution-attestations/red-control-sensitive-read-001.json'),
        ('examples/sandbox/lifecycle-attestations/red-control-sensitive-read-001-11.json', 'lifecycle-attestations/red-control-sensitive-read-001-11.json'),
        ('examples/sandbox/runtime-environment-attestations/red-control-sensitive-read-001.json', 'runtime-environment-attestations/red-control-sensitive-read-001.json'),
    ],
)
def test_canonical_resource_loader_preserves_exact_bytes_on_installed_fallback(
    tmp_path: Path,
    repository_path: str,
    installed_path: str,
):
    repository_text = (ROOT / repository_path).read_text(encoding='utf-8')

    assert canonical_resource_text(repository_path, installed_path) == repository_text

    install_root = tmp_path / 'share' / 'agentci' / 'sandbox'
    installed_file = install_root / installed_path
    installed_file.parent.mkdir(parents=True, exist_ok=True)
    installed_file.write_text(repository_text, encoding='utf-8')

    assert canonical_resource_text(
        repository_path,
        installed_path,
        repository_root=tmp_path / 'missing-repository',
        install_root=install_root,
    ) == repository_text
