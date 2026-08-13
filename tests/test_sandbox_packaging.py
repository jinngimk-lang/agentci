from __future__ import annotations

from pathlib import Path

import pytest

from agentci.sandbox.resource_loader import canonical_resource_text


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ('repository_path', 'resource_name'),
    [
        ('schemas/sandbox-certification-v0alpha1.schema.json', 'schema/sandbox-certification-v0alpha1.schema.json'),
        ('examples/sandbox/testcases/sandbox-sensitive-canary-v0alpha1.json', 'testcases/sandbox-sensitive-canary-v0alpha1.json'),
        ('examples/sandbox/execution-attestations/red-control-sensitive-read-001.json', 'execution-attestations/red-control-sensitive-read-001.json'),
        ('examples/sandbox/runtime-environment-attestations/red-control-sensitive-read-001.json', 'runtime-environment-attestations/red-control-sensitive-read-001.json'),
    ],
)
def test_packaged_canonical_resource_is_byte_identical(repository_path: str, resource_name: str):
    repository_text = (ROOT / repository_path).read_text(encoding='utf-8')
    assert canonical_resource_text(repository_path, resource_name) == repository_text
