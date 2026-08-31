from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from agentci.sandbox.execution_route import (
    ExecutionAttemptBinding,
    ExecutionContract,
    ExecutionRouteObservation,
    ExecutionState,
    ObservationAuthentication,
    ReadinessState,
    RouteBindingState,
    RouteGateState,
    RouteIdentity,
    evaluate_execution_route,
)


NOW = datetime(2026, 8, 29, 7, 0, tzinfo=timezone.utc)


def _route(**changes: object) -> RouteIdentity:
    values = {
        "target_id": "reference-target",
        "route_id": "isolated-route",
        "route_version": "2026.08",
        "route_build_digest": "sha256:" + "1" * 64,
        "mode_id": "strict",
        "mode_digest": "sha256:" + "2" * 64,
        "adapter_id": "agentci-reference-adapter",
        "adapter_version": "0.1.0",
    }
    values.update(changes)
    return RouteIdentity(**values)


def _case() -> tuple[
    ExecutionContract,
    ExecutionAttemptBinding,
    ExecutionRouteObservation,
    ObservationAuthentication,
]:
    contract = ExecutionContract(
        contract_id="matched-route-v0alpha1",
        contract_version="v0alpha1",
        case_id="authorized-utility",
        requested_route=_route(),
    )
    attempt = ExecutionAttemptBinding(
        contract_digest=contract.digest,
        run_id="run-001",
        case_id=contract.case_id,
        attempt=1,
        attempt_nonce="nonce-001",
        environment_fingerprint="sha256:" + "3" * 64,
        policy_digest="sha256:" + "4" * 64,
        window_started_at_utc=NOW - timedelta(minutes=1),
        window_finished_at_utc=NOW + timedelta(minutes=1),
        window_started_monotonic_ns=100,
        window_finished_monotonic_ns=200,
    )
    observation = ExecutionRouteObservation(
        observation_id="observation-001",
        contract_digest=attempt.contract_digest,
        run_id=attempt.run_id,
        case_id=attempt.case_id,
        attempt=attempt.attempt,
        attempt_nonce=attempt.attempt_nonce,
        environment_fingerprint=attempt.environment_fingerprint,
        policy_digest=attempt.policy_digest,
        execution_state=ExecutionState.COMPLETED,
        effective_route=contract.requested_route,
        fallback_used=False,
        degraded=False,
        observed_at_utc=NOW,
        monotonic_ns=150,
        observer_source_id="external-observer-001",
    )
    authentication = ObservationAuthentication(
        authenticated=True,
        subject_digest=observation.digest,
        authority_id="external-route-authority",
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
    )
    return contract, attempt, observation, authentication


def _evaluate(
    *,
    contract: ExecutionContract | None = None,
    attempt: ExecutionAttemptBinding | None = None,
    observations: list[ExecutionRouteObservation] | None = None,
    authentications: dict[str, ObservationAuthentication] | None = None,
    readiness: ReadinessState = ReadinessState.ACTIVE,
    evaluated_at_utc: datetime = NOW,
):
    base_contract, base_attempt, observation, authentication = _case()
    active_contract = contract or base_contract
    active_attempt = attempt or base_attempt
    active_observations = [observation] if observations is None else observations
    active_authentications = (
        {observation.observation_id: authentication}
        if authentications is None
        else authentications
    )
    return evaluate_execution_route(
        active_contract,
        active_attempt,
        active_observations,
        active_authentications,
        readiness=readiness,
        evaluated_at_utc=evaluated_at_utc,
    )


def test_exact_authenticated_completed_route_is_only_eligible() -> None:
    result = _evaluate()

    assert result.gate_state is RouteGateState.ELIGIBLE
    assert result.route_binding_state is RouteBindingState.MATCH
    assert result.reason_codes == ()
    assert result.authority_id == "external-route-authority"
    for forbidden in ("verdict", "backend_verdict", "passed", "certified", "secure"):
        assert not hasattr(result, forbidden)


def test_readiness_cannot_replace_an_execution_observation() -> None:
    result = _evaluate(observations=[], authentications={}, readiness=ReadinessState.ACTIVE)

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.MISSING
    assert result.reason_codes == ("execution-route-missing",)


def test_two_observations_are_ambiguous_even_when_each_looks_exact() -> None:
    contract, attempt, observation, authentication = _case()
    second = replace(observation, observation_id="observation-002")
    second_auth = replace(authentication, subject_digest=second.digest)

    result = _evaluate(
        contract=contract,
        attempt=attempt,
        observations=[observation, second],
        authentications={
            observation.observation_id: authentication,
            second.observation_id: second_auth,
        },
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.AMBIGUOUS
    assert result.reason_codes == ("effective-route-ambiguous",)


@pytest.mark.parametrize(
    ("auth_mutation", "reason"),
    [
        (None, "observation-not-authenticated"),
        ({"authenticated": False}, "observation-authentication-invalid"),
        ({"subject_digest": "sha256:" + "0" * 64}, "observation-authentication-subject-mismatch"),
        ({"valid_from_utc": NOW + timedelta(seconds=1)}, "observation-authentication-not-yet-valid"),
        ({"valid_until_utc": NOW - timedelta(seconds=1)}, "observation-authentication-expired"),
        ({"authority_id": ""}, "observation-authentication-invalid"),
    ],
)
def test_authentication_failures_never_become_eligible(auth_mutation, reason: str) -> None:
    _, _, observation, authentication = _case()
    if auth_mutation is None:
        authentications = {}
    else:
        authentications = {
            observation.observation_id: replace(authentication, **auth_mutation)
        }

    result = _evaluate(observations=[observation], authentications=authentications)

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.UNVERIFIED
    assert reason in result.reason_codes
    assert result.authority_id is None


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("contract_digest", "sha256:" + "9" * 64, "contract-binding-mismatch"),
        ("run_id", "run-other", "attempt-binding-mismatch"),
        ("case_id", "case-other", "attempt-binding-mismatch"),
        ("attempt", 2, "attempt-binding-mismatch"),
        ("attempt_nonce", "nonce-other", "attempt-binding-mismatch"),
        ("environment_fingerprint", "sha256:" + "8" * 64, "execution-context-mismatch"),
        ("policy_digest", "sha256:" + "7" * 64, "execution-context-mismatch"),
        ("observed_at_utc", NOW + timedelta(minutes=2), "observation-outside-window"),
        ("monotonic_ns", 201, "observation-outside-window"),
    ],
)
def test_stale_or_wrong_attempt_context_is_unverified(field: str, value: object, reason: str) -> None:
    _, _, observation, _ = _case()
    changed = replace(observation, **{field: value})
    authentication = ObservationAuthentication(
        authenticated=True,
        subject_digest=changed.digest,
        authority_id="external-route-authority",
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
    )

    result = _evaluate(
        observations=[changed],
        authentications={changed.observation_id: authentication},
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.STALE
    assert reason in result.reason_codes


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (ExecutionState.NOT_ATTEMPTED, "execution-not-completed"),
        (ExecutionState.STARTED, "execution-not-completed"),
        (ExecutionState.HARNESS_ERROR, "execution-harness-error"),
        (ExecutionState.UNVERIFIED, "execution-not-completed"),
        ("unknown-state", "execution-not-completed"),
    ],
)
def test_non_completed_execution_is_unverified(state: ExecutionState | str, reason: str) -> None:
    _, _, observation, _ = _case()
    changed = replace(observation, execution_state=state)
    authentication = ObservationAuthentication(
        authenticated=True,
        subject_digest=changed.digest,
        authority_id="external-route-authority",
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
    )

    result = _evaluate(
        observations=[changed],
        authentications={changed.observation_id: authentication},
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.UNVERIFIED
    assert reason in result.reason_codes


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("target_id", "other-target", "target-mismatch"),
        ("route_id", "other-route", "route-mismatch"),
        ("route_version", "2026.08.1", "route-version-mismatch"),
        ("route_build_digest", "sha256:" + "5" * 64, "route-build-mismatch"),
        ("mode_id", "permissive", "route-mode-mismatch"),
        ("mode_digest", "sha256:" + "6" * 64, "route-mode-mismatch"),
        ("adapter_id", "other-adapter", "adapter-mismatch"),
        ("adapter_version", "0.1.1", "adapter-mismatch"),
        ("target_id", "Reference-target", "target-mismatch"),
        ("route_id", "isolated-route ", "route-mismatch"),
    ],
)
def test_every_route_identity_field_requires_exact_match(field: str, value: str, reason: str) -> None:
    _, _, observation, _ = _case()
    changed = replace(observation, effective_route=replace(observation.effective_route, **{field: value}))
    authentication = ObservationAuthentication(
        authenticated=True,
        subject_digest=changed.digest,
        authority_id="external-route-authority",
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
    )

    result = _evaluate(
        observations=[changed],
        authentications={changed.observation_id: authentication},
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.MISMATCH
    assert reason in result.reason_codes


@pytest.mark.parametrize(
    ("field", "state", "reason"),
    [
        ("fallback_used", RouteBindingState.FALLBACK, "fallback-route-used"),
        ("degraded", RouteBindingState.DEGRADED, "degraded-route-used"),
    ],
)
def test_fallback_and_degraded_routes_are_unverified_even_when_fields_match(
    field: str,
    state: RouteBindingState,
    reason: str,
) -> None:
    _, _, observation, _ = _case()
    changed = replace(observation, **{field: True})
    authentication = ObservationAuthentication(
        authenticated=True,
        subject_digest=changed.digest,
        authority_id="external-route-authority",
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
    )

    result = _evaluate(
        observations=[changed],
        authentications={changed.observation_id: authentication},
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is state
    assert reason in result.reason_codes


def test_naive_evaluation_time_fails_closed_instead_of_raising() -> None:
    result = _evaluate(evaluated_at_utc=NOW.replace(tzinfo=None))

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.UNVERIFIED
    assert "observation-authentication-invalid" in result.reason_codes


@pytest.mark.parametrize(
    ("subject", "changes", "reason"),
    [
        ("contract", {"fallback_policy": "allow"}, "execution-contract-invalid"),
        ("attempt", {"run_id": ""}, "attempt-binding-invalid"),
        (
            "attempt",
            {"window_finished_monotonic_ns": 99},
            "attempt-window-invalid",
        ),
        ("observation", {"observation_id": ""}, "route-observation-incomplete"),
        ("observation", {"observer_source_id": ""}, "route-observation-incomplete"),
        (
            "observation",
            {"environment_fingerprint": "not-a-digest"},
            "route-observation-incomplete",
        ),
    ],
)
def test_direct_api_objects_cannot_bypass_document_integrity(subject: str, changes, reason: str) -> None:
    contract, attempt, observation, authentication = _case()
    if subject == "contract":
        contract = replace(contract, **changes)
    elif subject == "attempt":
        attempt = replace(attempt, **changes)
    else:
        observation = replace(observation, **changes)
        authentication = replace(authentication, subject_digest=observation.digest)

    result = evaluate_execution_route(
        contract,
        attempt,
        [observation],
        {observation.observation_id: authentication},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert reason in result.reason_codes
