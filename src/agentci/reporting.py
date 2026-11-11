from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .scoring import SuiteResult

# The Markdown report used to print a bare `PASS` for any case whose threshold
# comparisons held. Those numbers are typed into the eval file by the suite
# author, so the label is now derived from the case verdict: `UNVERIFIED` when
# the comparisons hold, `FAIL` when one does not.
VERDICT_LABELS = {
    'UNVERIFIED': 'UNVERIFIED',
    'FAIL': 'FAIL',
}


def _case_label(case) -> str:
    verdict = getattr(case, 'verdict', 'UNVERIFIED')
    return VERDICT_LABELS.get(verdict, verdict)


def write_reports(result: SuiteResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'agentci-results.json'
    md_path = output_dir / 'agentci-report.md'
    json_path.write_text(json.dumps(asdict(result), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    lines = [
        f'# AgentCI Report: {result.suite}',
        '',
        f'- Source: {getattr(result, "source", "author-supplied")}',
        f'- Verdict: {getattr(result, "verdict", "UNVERIFIED")}',
        f'- Total: {result.total_cases}',
        f'- Comparisons held: {result.passed_cases}',
        f'- Comparisons failed: {result.failed_cases}',
        f'- Success rate: {result.success_rate:.1%}',
        f'- Average latency: {result.average_latency_ms if result.average_latency_ms is not None else "n/a"} ms',
        f'- Total cost: {result.total_cost_usd if result.total_cost_usd is not None else "n/a"} USD',
        '',
    ]
    note = getattr(result, 'verdict_note', None)
    if note:
        lines.extend([f'> {note}', ''])
    lines.extend([
        '| Case | Verdict | Source | Latency ms | Cost USD | Failure reasons |',
        '|---|---|---|---:|---:|---|',
    ])
    for case in result.cases:
        reasons = '; '.join(case.failure_reasons) if case.failure_reasons else '—'
        latency = '—' if case.latency_ms is None else f'{case.latency_ms:g}'
        cost = '—' if case.cost_usd is None else f'{case.cost_usd:g}'
        source = getattr(case, 'source', 'author-supplied')
        lines.append(f'| {case.id} | {_case_label(case)} | {source} | {latency} | {cost} | {reasons} |')
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return json_path, md_path
