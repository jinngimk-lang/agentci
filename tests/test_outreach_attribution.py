from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_valid_v2_batch_reports_one_successful_placement(tmp_path: Path):
    batch = tmp_path / 'outreach.json'
    batch.write_text(
        json.dumps(
            {
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
            },
            indent=2,
        ),
        encoding='utf-8',
    )

    result = subprocess.run(
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

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary == {
        'schema_version': 'agentci.outreach.v2',
        'successful_placements': 1,
        'by_semantic_class': {'post-effect-false-failure': 1},
        'by_downstream_state': {'posted': 1},
    }
