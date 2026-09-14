from __future__ import annotations

from dataclasses import asdict
import html
import json
from pathlib import Path
import re

from .scoring import SuiteResult

_MARKDOWN_ESCAPE_RE = re.compile(r'([\\`*_{}\[\]()#+\-.!|>])')


def _markdown_text(value: str) -> str:
    single_line = value.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    escaped_html = html.escape(single_line, quote=False)
    return _MARKDOWN_ESCAPE_RE.sub(r'\\\1', escaped_html)


def write_reports(result: SuiteResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'agentci-results.json'
    md_path = output_dir / 'agentci-report.md'
    json_path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    lines = [
        f'# AgentCI Report: {_markdown_text(result.suite)}',
        '',
        f'- Total: {result.total_cases}',
        f'- Passed: {result.passed_cases}',
        f'- Failed: {result.failed_cases}',
        f'- Success rate: {result.success_rate:.1%}',
        f'- Average latency: {result.average_latency_ms if result.average_latency_ms is not None else "n/a"} ms',
        f'- Total cost: {result.total_cost_usd if result.total_cost_usd is not None else "n/a"} USD',
        '',
        '| Case | Status | Latency ms | Cost USD | Failure reasons |',
        '|---|---|---:|---:|---|',
    ]
    for case in result.cases:
        reasons = _markdown_text('; '.join(case.failure_reasons)) if case.failure_reasons else '—'
        latency = '—' if case.latency_ms is None else f'{case.latency_ms:g}'
        cost = '—' if case.cost_usd is None else f'{case.cost_usd:g}'
        lines.append(
            f'| {_markdown_text(case.id)} | {"PASS" if case.passed else "FAIL"} | {latency} | {cost} | {reasons} |'
        )
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return json_path, md_path
