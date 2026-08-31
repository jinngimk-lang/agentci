from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[2]
INSTALLED_ROOT = Path(sys.prefix) / 'share' / 'agentci' / 'showcase'


def load_showcase_catalog(
    *,
    repository_root: Path = SOURCE_ROOT,
    install_root: Path = INSTALLED_ROOT,
) -> dict[str, Any]:
    source = repository_root / 'showcase' / 'catalog-v1.json'
    installed = install_root / 'catalog-v1.json'

    if source.is_file():
        text = source.read_text(encoding='utf-8')
    elif installed.is_file():
        text = installed.read_text(encoding='utf-8')
    else:
        raise FileNotFoundError(
            'canonical showcase catalog unavailable: '
            f'source={source} installed={installed}'
        )

    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('showcase catalog must be a JSON object')
    return value


def validate_showcase_catalog(
    catalog: dict[str, Any],
    *,
    repository_root: Path = SOURCE_ROOT,
) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for item in catalog.get('items', []):
        item_id = item.get('id', '<unknown>')
        if item_id in seen_ids:
            errors.append(f'{item_id}: duplicate showcase id')
        else:
            seen_ids.add(item_id)

        repository_path = item.get('repository_path')
        if repository_path and not (repository_root / repository_path).is_file():
            errors.append(
                f'{item_id}: repository_path does not exist: {repository_path}'
            )
    return errors
