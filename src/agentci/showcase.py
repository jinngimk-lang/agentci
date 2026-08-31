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
