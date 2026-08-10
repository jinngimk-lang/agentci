import json
from pathlib import Path

import pytest

from scripts.growth_policy import ArtifactError, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / '.company/growth/rules.yaml'


def artifact(tmp_path: Path, **facts) -> Path:
    d = tmp_path / facts.get('artifact_id', 'artifact')
    d.mkdir()
    defaults = {
        'artifact_id': d.name,
        'category': 'benchmark',
        'title': 'Artifact',
        'public_claims': [],
    }
    defaults.update(facts)
    (d / 'facts.json').write_text(json.dumps(defaults), encoding='utf-8')
    (d / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')
    (d / 'sources.json').write_text('{"sources": []}', encoding='utf-8')
    return d


def test_benchmark_at_threshold_is_eligible():
    result = validate_artifact(ROOT / 'tests/fixtures/growth/valid-benchmark', RULES)
    assert result.eligible is True
    assert result.reasons == []


def test_benchmark_below_threshold_is_ineligible():
    result = validate_artifact(ROOT / 'tests/fixtures/growth/invalid-benchmark', RULES)
    assert result.eligible is False
    assert any('300' in reason for reason in result.reasons)


@pytest.mark.parametrize('improvement,samples,eligible', [
    (20, 100, True),
    (19.99, 100, False),
    (20, 99, False),
])
def test_performance_boundaries(tmp_path: Path, improvement, samples, eligible):
    d = artifact(tmp_path, category='performance', improvement_percent=improvement, samples=samples)
    assert validate_artifact(d, RULES).eligible is eligible


def test_security_requires_disclosure_ready():
    result = validate_artifact(ROOT / 'tests/fixtures/growth/security-not-ready', RULES)
    assert result.eligible is False
    assert any('disclosure' in reason.lower() for reason in result.reasons)


def test_security_requires_allowed_severity_and_reproducibility(tmp_path: Path):
    d = artifact(tmp_path, category='security', severity='medium', reproducible=False, disclosure_ready=True)
    result = validate_artifact(d, RULES)
    assert result.eligible is False
    assert len(result.reasons) == 2


@pytest.mark.parametrize('demo,tests,docs,eligible', [
    (True, True, True, True),
    (False, True, True, False),
    (True, False, True, False),
    (True, True, False, False),
])
def test_integration_requirements(tmp_path: Path, demo, tests, docs, eligible):
    d = artifact(tmp_path, category='integration', demo=demo, tests=tests, docs=docs)
    assert validate_artifact(d, RULES).eligible is eligible


def test_release_accepts_three_changes_or_major_capability(tmp_path: Path):
    three = artifact(tmp_path, artifact_id='three', category='release', meaningful_changes=3, major_capability=False)
    major = artifact(tmp_path, artifact_id='major', category='release', meaningful_changes=1, major_capability=True)
    weak = artifact(tmp_path, artifact_id='weak', category='release', meaningful_changes=2, major_capability=False)
    assert validate_artifact(three, RULES).eligible is True
    assert validate_artifact(major, RULES).eligible is True
    assert validate_artifact(weak, RULES).eligible is False


def test_dataset_threshold_and_reproducible_notes(tmp_path: Path):
    good = artifact(tmp_path, artifact_id='good', category='dataset', examples=100, reproducible_notes=True)
    low = artifact(tmp_path, artifact_id='low', category='dataset', examples=99, reproducible_notes=True)
    no_notes = artifact(tmp_path, artifact_id='no-notes', category='dataset', examples=100, reproducible_notes=False)
    assert validate_artifact(good, RULES).eligible is True
    assert validate_artifact(low, RULES).eligible is False
    assert validate_artifact(no_notes, RULES).eligible is False


def test_missing_canonical_file_is_invalid_input(tmp_path: Path):
    d = tmp_path / 'missing'
    d.mkdir()
    (d / 'facts.json').write_text('{}')
    with pytest.raises(ArtifactError, match='evidence.md'):
        validate_artifact(d, RULES)


def test_unknown_category_is_invalid_input(tmp_path: Path):
    d = artifact(tmp_path, category='mystery')
    with pytest.raises(ArtifactError, match='category'):
        validate_artifact(d, RULES)


def test_validator_cli_direct_script_execution():
    import subprocess, sys
    good = subprocess.run(
        [sys.executable, 'scripts/validate_growth_artifact.py', 'tests/fixtures/growth/valid-benchmark'],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert good.returncode == 0, good.stderr
    assert 'ELIGIBLE: valid-benchmark' in good.stdout
    bad = subprocess.run(
        [sys.executable, 'scripts/validate_growth_artifact.py', 'tests/fixtures/growth/invalid-benchmark'],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert bad.returncode == 1
    assert 'INELIGIBLE: invalid-benchmark' in bad.stdout
