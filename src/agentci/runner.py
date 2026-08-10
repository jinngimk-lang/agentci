from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .config import load_suite
from .local_command import execute_local_command
from .reporting import write_reports
from .scoring import SuiteResult, score_case, summarize_results


def run_suite(path: Path, output_dir: Path) -> SuiteResult:
    suite = load_suite(path)
    cases = suite.cases
    if suite.target is not None:
        cases = [replace(case, actual=execute_local_command(suite.target, case)) for case in suite.cases]
    result = summarize_results(suite, [score_case(case) for case in cases])
    write_reports(result, output_dir)
    return result
