import json
from pathlib import Path

from agentci.config import Actual, EvalCase, EvalSuite, Expected
from agentci.reporting import write_reports
from agentci.scoring import score_case, summarize_results


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
