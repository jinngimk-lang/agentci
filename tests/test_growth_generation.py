import json
from pathlib import Path
import re

import pytest

from scripts.generate_growth_pack import GrowthGenerationError, generate_growth_pack

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / '.company/growth/rules.yaml'
FIXTURES = ROOT / 'tests/fixtures/growth'


def test_valid_artifact_generates_complete_draft_pack(tmp_path: Path):
    out = generate_growth_pack(FIXTURES / 'valid-benchmark', tmp_path, RULES)
    expected = {
        'facts.json', 'evidence.md', 'x.md', 'reddit.md',
        'hackernews.md', 'blog.md', 'publish-checklist.md',
    }
    assert {p.name for p in out.iterdir()} == expected
    assert 'NO AUTO-PUBLISH IN V0' in (out / 'publish-checklist.md').read_text()
    assert '- [ ] Human approval' in (out / 'publish-checklist.md').read_text()


def test_ineligible_artifact_generates_nothing(tmp_path: Path):
    with pytest.raises(GrowthGenerationError, match='not eligible'):
        generate_growth_pack(FIXTURES / 'invalid-benchmark', tmp_path, RULES)
    assert list(tmp_path.iterdir()) == []


def test_security_not_ready_generates_nothing(tmp_path: Path):
    with pytest.raises(GrowthGenerationError, match='not eligible'):
        generate_growth_pack(FIXTURES / 'security-not-ready', tmp_path, RULES)
    assert list(tmp_path.iterdir()) == []


def test_public_numeric_claim_must_match_structured_numeric_fact(tmp_path: Path):
    with pytest.raises(GrowthGenerationError, match='999'):
        generate_growth_pack(FIXTURES / 'invalid-claims', tmp_path, RULES)


def test_all_generated_public_numbers_exist_as_structured_facts(tmp_path: Path):
    out = generate_growth_pack(FIXTURES / 'valid-benchmark', tmp_path, RULES)
    facts = json.loads((out / 'facts.json').read_text())
    structured_numbers = {
        str(v) for k, v in facts.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    for name in ['x.md', 'reddit.md', 'hackernews.md', 'blog.md']:
        numbers = set(re.findall(r'(?<![\w.])\d+(?:\.\d+)?', (out / name).read_text()))
        assert numbers <= structured_numbers, (name, numbers, structured_numbers)


def test_hn_benchmark_title_is_research_style(tmp_path: Path):
    out = generate_growth_pack(FIXTURES / 'valid-benchmark', tmp_path, RULES)
    first = (out / 'hackernews.md').read_text().splitlines()[0]
    assert not first.startswith('Show HN:')
