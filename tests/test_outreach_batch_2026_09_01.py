from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / '.company' / 'growth' / 'outreach-2026-09-01-50-touchpoint-batch-001.json'


def test_first_50_touchpoint_cohort_is_five_confirmed_public_writes():
    result = subprocess.run(
        [sys.executable, 'scripts/validate_outreach_batch.py', str(BATCH), '--json'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    assert summary['successful_placements'] == 5
    assert summary['by_downstream_state'] == {'posted': 5}
    assert sum(summary['by_semantic_class'].values()) == 5


def test_blocked_attempt_is_not_promoted_to_placement():
    payload = json.loads(BATCH.read_text(encoding='utf-8'))

    assert len(payload['placements']) == 5
    assert len(payload['attempts']) == 1
    attempt = payload['attempts'][0]
    assert attempt['repository'] == 'ringier-data/nannos'
    assert attempt['item_number'] == 182
    assert attempt['publication_result'] == 'blocked'
    assert attempt['http_status'] == 403
    assert attempt['counted'] is False
    assert all(placement['publication_result'] == 'posted' for placement in payload['placements'])
    assert all(placement['downstream_state'] == 'posted' for placement in payload['placements'])
