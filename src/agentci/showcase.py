from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = SOURCE_ROOT / 'showcase' / 'catalog-v1.json'


def load_showcase_catalog() -> dict[str, Any]:
    value = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('showcase catalog must be a JSON object')
    return value
