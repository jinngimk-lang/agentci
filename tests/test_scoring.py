from agentci.config import Actual, EvalCase, EvalSuite, Expected
from agentci.scoring import score_case, summarize_results


def case(*, success=True, expected_success=True, latency=100, max_latency=None, cost=0.01, max_cost=None):
    return EvalCase(
        id='case-1',
        input='hello',
        actual=Actual(success=success, latency_ms=latency, cost_usd=cost),
        expected=Expected(success=expected_success, max_latency_ms=max_latency, max_cost_usd=max_cost),
    )


def test_success_mismatch_fails():
    result = score_case(case(success=False, expected_success=True))
    assert result.passed is False
    assert result.failure_reasons == ['success expected True but got False']


def test_latency_threshold_is_inclusive():
    assert score_case(case(latency=100, max_latency=100)).passed is True


def test_latency_breach_is_reported():
    result = score_case(case(latency=101, max_latency=100))
    assert result.failure_reasons == ['latency_ms 101 exceeds max_latency_ms 100']


def test_cost_threshold_is_inclusive():
    assert score_case(case(cost=0.02, max_cost=0.02)).passed is True


def test_cost_breach_is_reported():
    result = score_case(case(cost=0.03, max_cost=0.02))
    assert result.failure_reasons == ['cost_usd 0.03 exceeds max_cost_usd 0.02']


def test_multiple_failures_are_preserved():
    result = score_case(case(success=False, latency=200, max_latency=100, cost=0.2, max_cost=0.1))
    assert len(result.failure_reasons) == 3


def test_summary_aggregates_metrics():
    c1 = case(latency=100, cost=0.01)
    c2 = EvalCase(
        id='case-2', input='world',
        actual=Actual(success=False, latency_ms=300, cost_usd=0.03),
        expected=Expected(success=True),
    )
    suite = EvalSuite(name='demo', cases=[c1, c2])
    summary = summarize_results(suite, [score_case(c1), score_case(c2)])
    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.success_rate == 0.5
    assert summary.average_latency_ms == 200
    assert summary.total_cost_usd == 0.04
    assert summary.average_cost_usd == 0.02
