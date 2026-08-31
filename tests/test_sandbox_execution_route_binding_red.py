import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import secrets
from typing import Any, Mapping

import pytest

from agentci.sandbox.execution_route import (
    ALGORITHM,
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
AUTHORITY_ID = "external-route-authority"
KEY_ID = "route-authority-test-key"
TRUST_EPOCH = 1
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def _canonical_bytes(value: object) -> bytes:
    def default(item: object) -> object:
        if isinstance(item, datetime):
            return item.isoformat()
        raise TypeError(type(item).__name__)

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=default,
    ).encode()


def _probable_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    for prime in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if candidate % prime == 0:
            return candidate == prime
    exponent, shifts = candidate - 1, 0
    while exponent % 2 == 0:
        exponent //= 2
        shifts += 1
    for base in (2, 3, 5, 7, 11, 13, 17):
        witness = pow(base, exponent, candidate)
        if witness in (1, candidate - 1):
            continue
        for _ in range(shifts - 1):
            witness = pow(witness, 2, candidate)
            if witness == candidate - 1:
                break
        else:
            return False
    return True


def _prime(bits: int = 384) -> int:
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if _probable_prime(candidate):
            return candidate


def _keypair() -> tuple[dict[str, object], tuple[int, int]]:
    exponent = 65537
    while True:
        p, q = _prime(), _prime()
        if p != q and math.gcd(exponent, (p - 1) * (q - 1)) == 1:
            break
    modulus = p * q
    private_exponent = pow(exponent, -1, (p - 1) * (q - 1))
    trust = {
        "algorithm": ALGORITHM,
        "key_id": KEY_ID,
        "trust_epoch": TRUST_EPOCH,
        "modulus_hex": format(modulus, "x"),
        "exponent": exponent,
    }
    return trust, (modulus, private_exponent)


_TRUST, _PRIVATE_KEY = _keypair()
TEST_TRUSTED_AUTHORITIES: Mapping[str, Mapping[str, object]] = {AUTHORITY_ID: _TRUST}


def _resign_authentication(
    authentication: ObservationAuthentication,
    private_key: tuple[int, int] = _PRIVATE_KEY,
) -> ObservationAuthentication:
    modulus, private_exponent = private_key
    size = (modulus.bit_length() + 7) // 8
    digest_info = _DIGEST_INFO_PREFIX + hashlib.sha256(
        _canonical_bytes(authentication.signed_payload)
    ).digest()
    padding = size - len(digest_info) - 3
    assert padding >= 8
    encoded = b"\x00\x01" + b"\xff" * padding + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), private_exponent, modulus).to_bytes(size, "big")
    return replace(authentication, signature_b64=base64.b64encode(signature).decode())


def _authentication_for(
    observation: ExecutionRouteObservation,
    **changes: Any,
) -> ObservationAuthentication:
    authentication = ObservationAuthentication(
        subject_digest=observation.digest,
        authority_id=AUTHORITY_ID,
        key_id=KEY_ID,
        trust_epoch=TRUST_EPOCH,
        valid_from_utc=NOW - timedelta(minutes=2),
        valid_until_utc=NOW + timedelta(minutes=2),
        signature_b64="",
    )
    return _resign_authentication(replace(authentication, **changes))


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
    authentication = _authentication_for(observation)
    return contract, attempt, observation, authentication


def _evaluate(
    *,
    contract: ExecutionContract | None = None,
    attempt: ExecutionAttemptBinding | None = None,
    observations: list[ExecutionRouteObservation] | None = None,
    authentications: dict[str, ObservationAuthentication] | None = None,
    readiness: ReadinessState = ReadinessState.ACTIVE,
    evaluated_at_utc: datetime = NOW,
    trusted_authorities: Mapping[str, Mapping[str, object]] = TEST_TRUSTED_AUTHORITIES,
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
        trusted_authorities=trusted_authorities,
    )


def test_exact_authenticated_completed_route_is_only_eligible() -> None:
    result = _evaluate()

    assert result.gate_state is RouteGateState.ELIGIBLE
    assert result.route_binding_state is RouteBindingState.MATCH
    assert result.reason_codes == ()
    assert result.authority_id == AUTHORITY_ID
    assert result.requested_route == result.observed_route == _route()
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
    second_auth = _authentication_for(second)

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
        ({"signature_b64": "AA=="}, "observation-authentication-invalid"),
        ({"subject_digest": "sha256:" + "0" * 64}, "observation-authentication-subject-mismatch"),
        ({"valid_from_utc": NOW + timedelta(seconds=1)}, "observation-authentication-not-yet-valid"),
        ({"valid_until_utc": NOW - timedelta(seconds=1)}, "observation-authentication-expired"),
        ({"authority_id": ""}, "observation-authentication-invalid"),
        ({"algorithm": "caller-defined"}, "observation-authentication-invalid"),
        ({"key_id": "untrusted-key"}, "observation-authentication-invalid"),
        ({"trust_epoch": 2}, "observation-authentication-invalid"),
    ],
)
def test_authentication_failures_never_become_eligible(auth_mutation, reason: str) -> None:
    _, _, observation, authentication = _case()
    if auth_mutation is None:
        authentications = {}
    else:
        changed = replace(authentication, **auth_mutation)
        if "signature_b64" not in auth_mutation:
            changed = _resign_authentication(changed)
        authentications = {
            observation.observation_id: changed
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
    authentication = _authentication_for(changed)

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
    authentication = _authentication_for(changed)

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
    authentication = _authentication_for(changed)

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
    authentication = _authentication_for(changed)

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
        (
            "attempt",
            {"window_started_monotonic_ns": None},
            "attempt-binding-invalid",
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
        authentication = _authentication_for(observation)

    result = evaluate_execution_route(
        contract,
        attempt,
        [observation],
        {observation.observation_id: authentication},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
        trusted_authorities=TEST_TRUSTED_AUTHORITIES,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert reason in result.reason_codes


def test_caller_forged_authentication_object_is_not_external_authority() -> None:
    contract, attempt, observation, _ = _case()
    forged = ObservationAuthentication(
        subject_digest=observation.digest,
        authority_id="caller-asserted-authority",
        key_id="caller-asserted-key",
        trust_epoch=1,
        valid_from_utc=NOW - timedelta(minutes=1),
        valid_until_utc=NOW + timedelta(minutes=1),
        signature_b64="AA==",
    )

    result = evaluate_execution_route(
        contract,
        attempt,
        [observation],
        {observation.observation_id: forged},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.UNVERIFIED
    assert "observation-authentication-invalid" in result.reason_codes


def test_even_a_valid_signature_requires_verifier_pinned_trust_policy() -> None:
    contract, attempt, observation, authentication = _case()

    result = evaluate_execution_route(
        contract,
        attempt,
        [observation],
        {observation.observation_id: authentication},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.UNVERIFIED
    assert "observation-authentication-invalid" in result.reason_codes


def test_malformed_direct_route_object_fails_closed_instead_of_raising() -> None:
    contract, attempt, observation, _ = _case()
    malformed = replace(observation, effective_route=None)
    authentication = _authentication_for(malformed)

    result = evaluate_execution_route(
        contract,
        attempt,
        [malformed],
        {malformed.observation_id: authentication},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
        trusted_authorities=TEST_TRUSTED_AUTHORITIES,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.MISMATCH
    assert "route-observation-incomplete" in result.reason_codes


def test_unhashable_direct_observation_id_fails_closed_instead_of_raising() -> None:
    contract, attempt, observation, _ = _case()
    malformed = replace(observation, observation_id=[])

    result = evaluate_execution_route(
        contract,
        attempt,
        [malformed],
        {},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
        trusted_authorities=TEST_TRUSTED_AUTHORITIES,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert "observation-not-authenticated" in result.reason_codes
    assert "route-observation-incomplete" in result.reason_codes


def test_non_sequence_observation_input_fails_closed_instead_of_raising() -> None:
    contract, attempt, _, _ = _case()

    result = evaluate_execution_route(
        contract,
        attempt,
        1,
        {},
        readiness=ReadinessState.ACTIVE,
        evaluated_at_utc=NOW,
        trusted_authorities=TEST_TRUSTED_AUTHORITIES,
    )

    assert result.gate_state is RouteGateState.UNVERIFIED
    assert result.route_binding_state is RouteBindingState.MISMATCH
    assert result.reason_codes == ("route-observation-incomplete",)
