from __future__ import annotations

import json
from pathlib import Path

from agentci.showcase import load_showcase_catalog


ROOT = Path(__file__).resolve().parents[1]


def test_showcase_catalog_uses_same_canonical_bytes_for_installed_fallback(tmp_path: Path):
    repository_text = (ROOT / 'showcase/catalog-v1.json').read_text(encoding='utf-8')
    install_root = tmp_path / 'share' / 'agentci' / 'showcase'
    install_root.mkdir(parents=True)
    (install_root / 'catalog-v1.json').write_text(repository_text, encoding='utf-8')

    catalog = load_showcase_catalog(
        repository_root=tmp_path / 'missing-repository',
        install_root=install_root,
    )

    assert catalog == json.loads(repository_text)
