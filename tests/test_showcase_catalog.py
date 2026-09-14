from __future__ import annotations

import json
from pathlib import Path

from agentci import showcase as showcase_module
from agentci.cli import build_parser
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


def test_showcase_catalog_validator_rejects_missing_local_resource(tmp_path: Path):
    validator = getattr(showcase_module, 'validate_showcase_catalog', None)
    assert validator is not None, 'validate_showcase_catalog must exist'

    catalog = {
        'schema_version': 'agentci.showcase.v1',
        'items': [
            {
                'id': 'missing-resource',
                'repository_path': 'examples/missing.json',
            }
        ],
    }

    errors = validator(catalog, repository_root=tmp_path)

    assert errors == ['missing-resource: repository_path does not exist: examples/missing.json']


def test_showcase_catalog_validator_rejects_duplicate_ids(tmp_path: Path):
    catalog = {
        'schema_version': 'agentci.showcase.v1',
        'items': [
            {'id': 'duplicate', 'repository_path': None},
            {'id': 'duplicate', 'repository_path': None},
        ],
    }

    errors = showcase_module.validate_showcase_catalog(catalog, repository_root=tmp_path)

    assert errors == ['duplicate: duplicate showcase id']


def test_showcase_catalog_validator_rejects_fixture_certification_claim(tmp_path: Path):
    catalog = {
        'schema_version': 'agentci.showcase.v1',
        'items': [
            {
                'id': 'fixture-claim',
                'repository_path': None,
                'evidence_maturity': 'fixture',
                'certification_claim': True,
            }
        ],
    }

    errors = showcase_module.validate_showcase_catalog(catalog, repository_root=tmp_path)

    assert errors == ['fixture-claim: fixture entries cannot claim certification']


def test_canonical_showcase_catalog_satisfies_truth_contract():
    catalog = load_showcase_catalog(repository_root=ROOT)

    assert showcase_module.validate_showcase_catalog(catalog, repository_root=ROOT) == []


def test_canonical_showcase_commands_are_represented_by_current_cli():
    catalog = load_showcase_catalog(repository_root=ROOT)

    for item in catalog['items']:
        command = item['released_command']
        assert command[0] == 'agentci', item['id']
        parsed = build_parser().parse_args(command[1:])
        assert parsed.command in {'test', 'sandbox', 'showcase'}, item['id']
