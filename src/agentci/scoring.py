from __future__ import annotations

from dataclasses import dataclass

from .config import EvalCase, EvalSuite


@dataclass(frozen=True)
class CaseResult:
    id: str
    passed: bool
    actual_success: bool
    latency_ms: float | None
    cost_usd: float | None
    failure_reasons: list[str]


@dataclass(frozen=True)
class SuiteResult:
    suite: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    success_rate: float
    average_latency_ms: float | None
    total_cost_usd: float | None
    average_cost_usd: float | None
    cases: list[CaseResult]


def score_case(case: EvalCase) -> CaseResult:
    reasons: list[str] = []
    if case.actual.success != case.expected.success:
        reasons.append(f"success expected {case.expected.success} but got {case.actual.success}")
    if case.expected.max_latency_ms is not None:
        if case.actual.latency_ms is None:
            reasons.append("latency_ms missing but max_latency_ms is required")
        elif case.actual.latency_ms > case.expected.max_latency_ms:
            reasons.append(
                f"latency_ms {case.actual.latency_ms:g} exceeds max_latency_ms {case.expected.max_latency_ms:g}"
            )
    if case.expected.max_cost_usd is not None:
        if case.actual.cost_usd is None:
            reasons.append("cost_usd missing but max_cost_usd is required")
        elif case.actual.cost_usd > case.expected.max_cost_usd:
            reasons.append(
                f"cost_usd {case.actual.cost_usd:g} exceeds max_cost_usd {case.expected.max_cost_usd:g}"
            )
    return CaseResult(
        id=case.id,
        passed=not reasons,
        actual_success=case.actual.success,
        latency_ms=case.actual.latency_ms,
        cost_usd=case.actual.cost_usd,
        failure_reasons=reasons,
    )


def summarize_results(suite: EvalSuite, results: list[CaseResult]) -> SuiteResult:
    passed = sum(result.passed for result in results)
    total = len(results)
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    costs = [r.cost_usd for r in results if r.cost_usd is not None]
    total_cost = sum(costs) if costs else None
    return SuiteResult(
        suite=suite.name,
        total_cases=total,
        passed_cases=passed,
        failed_cases=total - passed,
        success_rate=(passed / total) if total else 0.0,
        average_latency_ms=(sum(latencies) / len(latencies)) if latencies else None,
        total_cost_usd=total_cost,
        average_cost_usd=(total_cost / len(costs)) if costs else None,
        cases=results,
    )
