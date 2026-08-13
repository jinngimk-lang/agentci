"""Locate canonical sandbox resources in source checkouts and installed wheels."""
from __future__ import annotations

from pathlib import Path
import sys


SOURCE_ROOT = Path(__file__).resolve().parents[3]
INSTALLED_ROOT = Path(sys.prefix) / 'share' / 'agentci' / 'sandbox'


def canonical_resource_text(
    repository_path: str,
    installed_path: str,
    *,
    repository_root: Path = SOURCE_ROOT,
    install_root: Path = INSTALLED_ROOT,
) -> str:
    """Read one canonical resource without maintaining a second source copy."""
    source = repository_root / repository_path
    if source.is_file():
        return source.read_text(encoding='utf-8')

    installed = install_root / installed_path
    if installed.is_file():
        return installed.read_text(encoding='utf-8')

    raise FileNotFoundError(
        f'canonical sandbox resource unavailable: source={repository_path} installed={installed_path}'
    )
