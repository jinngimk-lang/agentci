#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


SCHEMA_VERSION = 'agentci.outreach.v2'
ALLOWED_DOWNSTREAM_STATES = {
    'posted',
    'replied',
    'repo_action',
    'contribution',
    'merged',
    'repeat_contributor',
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('outreach batch must be a JSON object')
    if payload.get('schema_version') != SCHEMA_VERSION:
        raise ValueError(f'schema_version must be {SCHEMA_VERSION}')
    placements = payload.get('placements')
    attempts = payload.get('attempts')
    if not isinstance(placements, list):
        raise ValueError('placements must be a list')
    if not isinstance(attempts, list):
        raise ValueError('attempts must be a list')
    return payload


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    placements = payload['placements']
    semantic = Counter()
    downstream = Counter()
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for placement in placements:
        if not isinstance(placement, dict):
            raise ValueError('each placement must be an object')
        placement_id = placement.get('id')
        if not isinstance(placement_id, str) or not placement_id:
            raise ValueError('placement id must be a non-empty string')
        if placement_id in seen_ids:
            raise ValueError(f'duplicate placement id: {placement_id}')
        seen_ids.add(placement_id)
        comment_url = placement.get('comment_url')
        if not isinstance(comment_url, str) or not comment_url.startswith('https://github.com/'):
            raise ValueError('placement comment_url must be a confirmed public GitHub comment URL')
        if '#issuecomment-' not in comment_url:
            raise ValueError('placement comment_url must identify a GitHub issue/PR comment')
        if comment_url in seen_urls:
            raise ValueError(f'duplicate placement comment_url: {comment_url}')
        seen_urls.add(comment_url)
        if placement.get('publication_result') != 'posted':
            raise ValueError('counted placement publication_result must be posted')
        semantic_class = placement.get('semantic_class')
        downstream_state = placement.get('downstream_state')
        if not isinstance(semantic_class, str) or not semantic_class:
            raise ValueError('placement semantic_class must be a non-empty string')
        if downstream_state not in ALLOWED_DOWNSTREAM_STATES:
            raise ValueError('placement downstream_state must be an observable supported state')
        downstream_urls = placement.get('downstream_urls')
        if not isinstance(downstream_urls, list):
            raise ValueError('placement downstream_urls must be a list')
        if downstream_state != 'posted':
            if not downstream_urls:
                raise ValueError('advanced downstream_state requires public downstream_urls evidence')
            if any(
                not isinstance(url, str) or not url.startswith('https://github.com/')
                for url in downstream_urls
            ):
                raise ValueError('downstream_urls evidence must use public GitHub URLs')
            if any('/graphs/traffic' in url for url in downstream_urls):
                raise ValueError('traffic/referral pages are not observable downstream evidence')
        semantic[semantic_class] += 1
        downstream[downstream_state] += 1
    return {
        'schema_version': SCHEMA_VERSION,
        'successful_placements': len(placements),
        'by_semantic_class': dict(sorted(semantic.items())),
        'by_downstream_state': dict(sorted(downstream.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate an AgentCI outreach v2 batch')
    parser.add_argument('path', type=Path)
    parser.add_argument('--json', action='store_true', help='emit the deterministic JSON summary')
    args = parser.parse_args(argv)

    try:
        summary = summarize(_load(args.path))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(f"Outreach placements: {summary['successful_placements']}")
        for name, count in summary['by_semantic_class'].items():
            print(f'- semantic {name}: {count}')
        for name, count in summary['by_downstream_state'].items():
            print(f'- downstream {name}: {count}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
