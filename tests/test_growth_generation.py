import json
from pathlib import Path
import re

import pytest

from scripts.generate_growth_pack import GrowthGenerationError, generate_growth_pack

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / '.company/growth/rules.yaml'
FIXTURES = ROOT / 'tests/fixtures/growth'


def release_artifact(tmp_path: Path, artifact_id: str, claim: str, **extra_facts) -> Path:
    d = tmp_path / artifact_id
    d.mkdir()
    facts = {
        'artifact_id': artifact_id,
        'category': 'release',
        'title': 'Numeric claim test',
        'public_claims': [claim],
        'meaningful_changes': 1,
        'major_capability': True,
        **extra_facts,
    }
    (d / 'facts.json').write_text(json.dumps(facts), encoding='utf-8')
    (d / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')
    (d / 'sources.json').write_text('{"sources": []}', encoding='utf-8')
    return d


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


def test_grouped_number_cannot_be_backed_by_separate_one_and_zero_facts(tmp_path: Path):
    artifact = release_artifact(
        tmp_path,
        'grouped-mismatch',
        'We reached 1,000 users',
        unrelated_zero=0,
    )
    with pytest.raises(GrowthGenerationError, match='1,000'):
        generate_growth_pack(artifact, tmp_path / 'out', RULES)


def test_grouped_number_matches_single_structured_value(tmp_path: Path):
    artifact = release_artifact(tmp_path, 'grouped-match', 'We reached 1,000 users', users=1000)
    out = generate_growth_pack(artifact, tmp_path / 'out', RULES)
    assert (out / 'x.md').exists()


@pytest.mark.parametrize('claim', ['We reached 1,000, then grew', 'We reached 1000, then grew'])
def test_punctuation_comma_after_number_is_not_part_of_numeric_claim(tmp_path: Path, claim: str):
    artifact = release_artifact(tmp_path, 'punctuation-comma', claim, users=1000)
    out = generate_growth_pack(artifact, tmp_path / 'out', RULES)
    assert (out / 'x.md').exists()


@pytest.mark.parametrize(
    ('claim', 'facts'),
    [
        ('Latency changed by -20%', {'delta_percent': -20}),
        ('Processed 1e3 events', {'events': 1000}),
        ('Processed +1.5e3 events', {'events': 1500}),
        ('Rate reached 20%', {'rate_percent': 20}),
    ],
)
def test_signed_scientific_and_percentage_claims_use_numeric_value(tmp_path: Path, claim: str, facts: dict):
    artifact = release_artifact(tmp_path, 'normalized-number', claim, **facts)
    out = generate_growth_pack(artifact, tmp_path / 'out', RULES)
    assert (out / 'x.md').exists()


def test_malformed_thousands_grouping_is_rejected(tmp_path: Path):
    artifact = release_artifact(
        tmp_path,
        'bad-grouping',
        'We reached 1,00 users',
        unrelated_zero=0,
    )
    with pytest.raises(GrowthGenerationError, match='1,00'):
        generate_growth_pack(artifact, tmp_path / 'out', RULES)


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
