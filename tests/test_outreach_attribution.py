from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


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
