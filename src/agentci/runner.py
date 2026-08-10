from __future__ import annotations

from pathlib import Path

from .config import load_suite
from .reporting import write_reports
from .scoring import SuiteResult, score_case, summarize_results


def run_suite(path: Path, output_dir: Path) -> SuiteResult:
    suite = load_suite(path)
    result = summarize_results(suite, [score_case(case) for case in suite.cases])
    write_reports(result, output_dir)
    return result
