"""Locate canonical sandbox resources in source checkouts and installed wheels."""
from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[3]
INSTALLED_ROOT = Path(sys.prefix) / 'share' / 'agentci' / 'sandbox'


def canonical_resource_text(
    repository_path: str,
    installed_path: str,
    *,
    repository_root: Path = SOURCE_ROOT,
    install_root: Path = INSTALLED_ROOT,
) -> str:
    """Read one canonical resource without maintaining a second source copy.

    Source checkouts read the repository-owned canonical file directly. Wheels
    install those same files as data-files under ``share/agentci/sandbox`` and
    use that location only when a repository checkout is not present.
    """
    source = repository_root / repository_path
    if source.is_file():
        return source.read_text(encoding='utf-8')

    installed = install_root / installed_path
    if installed.is_file():
        return installed.read_text(encoding='utf-8')

    raise FileNotFoundError(
        f'canonical sandbox resource unavailable: source={repository_path} installed={installed_path}'
    )


def canonical_resource_json(repository_path: str, installed_path: str) -> dict[str, Any]:
    value = json.loads(canonical_resource_text(repository_path, installed_path))
    if not isinstance(value, dict):
        raise ValueError(f'canonical sandbox resource is not an object: {repository_path}')
    return value
