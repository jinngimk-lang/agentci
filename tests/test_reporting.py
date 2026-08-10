import json
from pathlib import Path

from agentci.config import Actual, EvalCase, EvalSuite, Expected
from agentci.reporting import write_reports
from agentci.scoring import score_case, summarize_results


def rendered_report(tmp_path: Path, suite_name: str, case_id: str = 'case') -> str:
    case = EvalCase(case_id, 'x', Actual(True), Expected(True))
    result = summarize_results(EvalSuite(suite_name, [case]), [score_case(case)])
    _, md_path = write_reports(result, tmp_path)
    return md_path.read_text(encoding='utf-8')


def test_write_reports_emits_json_and_markdown(tmp_path: Path):
    case = EvalCase('bad', 'x', Actual(False, 200, 0.2), Expected(True, 100, 0.1))
    result = summarize_results(EvalSuite('demo', [case]), [score_case(case)])
    json_path, md_path = write_reports(result, tmp_path)
    payload = json.loads(json_path.read_text())
    assert payload['suite'] == 'demo'
    assert payload['total_cases'] == 1
    assert payload['failed_cases'] == 1
    assert payload['cases'][0]['failure_reasons']
    report = md_path.read_text()
    assert '# AgentCI Report: demo' in report
    assert '| bad | FAIL |' in report
    assert 'success expected True but got False' in report


def test_markdown_report_flattens_and_escapes_suite_name(tmp_path: Path):
    report = rendered_report(tmp_path, 'ok\n- Failed: 0\n# FORGED')
    assert report.startswith('# AgentCI Report: ok \\- Failed: 0 \\# FORGED\n')
    assert '\n# FORGED\n' not in report
    assert '\n- Failed: 0\n' not in report


def test_markdown_report_escapes_table_delimiters_and_backslashes(tmp_path: Path):
    report = rendered_report(tmp_path, 'demo', r'legit | FAIL \ path *bold*')
    assert r'| legit \| FAIL \\ path \*bold\* | PASS |' in report
    assert '| legit | FAIL | 0 | 0 | forged |' not in report


def test_markdown_report_escapes_link_and_emphasis_markup(tmp_path: Path):
    report = rendered_report(tmp_path, '[link](https://example.test) _em_')
    assert r'# AgentCI Report: \[link\]\(https://example\.test\) \_em\_' in report
