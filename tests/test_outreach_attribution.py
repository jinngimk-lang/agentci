from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CURRENT_BATCH = ROOT / '.company' / 'growth' / 'outreach-2026-09-01-50-touchpoint-batch-001.json'
SECOND_BATCH = ROOT / '.company' / 'growth' / 'outreach-2026-09-01-50-touchpoint-batch-002.json'


def _valid_payload() -> dict:
    return {
        'schema_version': 'agentci.outreach.v2',
        'batch_id': '2026-09-01-a',
        'date': '2026-09-01',
        'placements': [
            {
                'id': 'openclaw-134621',
                'repository': 'openclaw/openclaw',
                'item_type': 'issue',
                'item_number': 134621,
                'comment_url': 'https://github.com/openclaw/openclaw/issues/134621#issuecomment-5489847043',
                'semantic_class': 'post-effect-false-failure',
                'intent': 'side effect happened but tool returned an error',
                'cta': 'fixture',
                'publication_result': 'posted',
                'downstream_state': 'posted',
                'downstream_urls': [],
                'claim_boundary': 'Confirmed public write only; no hidden traffic attribution.',
            }
        ],
        'attempts': [],
    }


def _run_validator(tmp_path: Path, payload: dict):
    batch = tmp_path / 'outreach.json'
    batch.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return subprocess.run(
        [
            sys.executable,
            'scripts/validate_outreach_batch.py',
            str(batch),
            '--json',
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_valid_v2_batch_reports_one_successful_placement(tmp_path: Path):
    result = _run_validator(tmp_path, _valid_payload())

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary == {
        'schema_version': 'agentci.outreach.v2',
        'successful_placements': 1,
        'by_semantic_class': {'post-effect-false-failure': 1},
        'by_downstream_state': {'posted': 1},
    }


def test_counted_placement_requires_confirmed_public_comment_url(tmp_path: Path):
    payload = _valid_payload()
    payload['placements'][0].pop('comment_url')

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'comment_url' in result.stderr


def test_counted_placement_must_be_confirmed_posted_write(tmp_path: Path):
    payload = _valid_payload()
    payload['placements'][0]['publication_result'] = 'blocked'

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'publication_result' in result.stderr


def test_duplicate_placement_ids_are_rejected(tmp_path: Path):
    payload = _valid_payload()
    duplicate = dict(payload['placements'][0])
    duplicate['comment_url'] = 'https://github.com/openclaw/openclaw/issues/134622#issuecomment-5489847044'
    duplicate['item_number'] = 134622
    payload['placements'].append(duplicate)

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'duplicate placement id' in result.stderr.lower()


def test_duplicate_comment_urls_are_rejected(tmp_path: Path):
    payload = _valid_payload()
    duplicate = dict(payload['placements'][0])
    duplicate['id'] = 'openclaw-134622'
    duplicate['item_number'] = 134622
    payload['placements'].append(duplicate)

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'duplicate placement comment_url' in result.stderr.lower()


def test_unobservable_downstream_state_is_rejected(tmp_path: Path):
    payload = _valid_payload()
    payload['placements'][0]['downstream_state'] = 'visited'

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'downstream_state' in result.stderr


def test_advanced_downstream_state_requires_public_evidence_url(tmp_path: Path):
    payload = _valid_payload()
    payload['placements'][0]['downstream_state'] = 'replied'
    payload['placements'][0]['downstream_urls'] = []

    result = _run_validator(tmp_path, payload)

    assert result.returncode == 1
    assert 'downstream_urls' in result.stderr


def test_current_v2_campaign_batch_has_five_confirmed_placements():
    result = subprocess.run(
        [
            sys.executable,
            'scripts/validate_outreach_batch.py',
            str(CURRENT_BATCH),
            '--json',
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary == {
        'schema_version': 'agentci.outreach.v2',
        'successful_placements': 5,
        'by_semantic_class': {
            'durable-path-evidence-gap': 1,
            'observer-side-effect': 1,
            'scheduled-failure-false-success': 1,
            'split-observer-false-success': 1,
            'terminality-resource-residue': 1,
        },
        'by_downstream_state': {'posted': 5},
    }


def test_second_v2_campaign_batch_has_five_confirmed_placements():
    result = subprocess.run(
        [
            sys.executable,
            'scripts/validate_outreach_batch.py',
            str(SECOND_BATCH),
            '--json',
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary == {
        'schema_version': 'agentci.outreach.v2',
        'successful_placements': 5,
        'by_semantic_class': {
            'cross-surface-authority-preservation': 1,
            'execution-delivery-divergence': 1,
            'lease-ownership-crash-residue': 1,
            'replay-substitution-fidelity': 1,
            'subscription-evidence-completeness': 1,
        },
        'by_downstream_state': {'posted': 5},
    }
