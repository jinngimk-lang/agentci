"""Provider-neutral execution-route binding for the first S1 claim.

The gate proves only that one completed execution was externally observed on
the exact route requested by its bound contract and attempt.  Eligibility is
not a sandbox verdict, containment result, or certification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from .resource_loader import canonical_resource_json


API_VERSION = "agentci.dev/sandbox-execution/v0alpha1"
CONTRACT_KIND = "ExecutionContract"
OBSERVATION_KIND = "ExecutionRouteObservation"


class ReadinessState(str, Enum):
    DECLARED = "declared"
    INSTALLED = "installed"
    CONFIGURED = "configured"
    PROBED = "probed"
    ACTIVE = "active"
    FAILED = "failed"
    UNVERIFIED = "unverified"


class ExecutionState(str, Enum):
    NOT_ATTEMPTED = "not-attempted"
    STARTED = "started"
    COMPLETED = "completed"
    HARNESS_ERROR = "harness-error"
    UNVERIFIED = "unverified"


class RouteBindingState(str, Enum):
    MATCH = "match"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    STALE = "stale"
    FALLBACK = "fallback"
    DEGRADED = "degraded"
    MISMATCH = "mismatch"
    UNVERIFIED = "unverified"


class RouteGateState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    UNVERIFIED = "UNVERIFIED"


class ExecutionRouteDocumentError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class RouteIdentity:
    target_id: str
    route_id: str
    route_version: str
    route_build_digest: str
    mode_id: str
    mode_digest: str
    adapter_id: str
    adapter_version: str


@dataclass(frozen=True)
class ExecutionContract:
    contract_id: str
    contract_version: str
    case_id: str
    requested_route: RouteIdentity
    fallback_policy: str = "forbid"

    @property
    def digest(self) -> str:
        return _digest(
            {
                "apiVersion": API_VERSION,
                "kind": CONTRACT_KIND,
                "contract_id": self.contract_id,
                "contract_version": self.contract_version,
                "case_id": self.case_id,
                "requested_route": asdict(self.requested_route),
                "fallback_policy": self.fallback_policy,
            }
        )


@dataclass(frozen=True)
class ExecutionAttemptBinding:
    contract_digest: str
    run_id: str
    case_id: str
    attempt: int
    attempt_nonce: str
    environment_fingerprint: str
    policy_digest: str
    window_started_at_utc: datetime
    window_finished_at_utc: datetime
    window_started_monotonic_ns: int
    window_finished_monotonic_ns: int


@dataclass(frozen=True)
class ExecutionRouteObservation:
    observation_id: str
    contract_digest: str
    run_id: str
    case_id: str
    attempt: int
    attempt_nonce: str
    environment_fingerprint: str
    policy_digest: str
    execution_state: ExecutionState | str
    effective_route: RouteIdentity
    fallback_used: bool
    degraded: bool
    observed_at_utc: datetime
    monotonic_ns: int
    observer_source_id: str

    @property
    def digest(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class ObservationAuthentication:
    authenticated: bool
    subject_digest: str
    authority_id: str
    valid_from_utc: datetime
    valid_until_utc: datetime


@dataclass(frozen=True)
class RouteGateResult:
    gate_state: RouteGateState
    route_binding_state: RouteBindingState
    execution_state: ExecutionState | str
    readiness_state: ReadinessState
    reason_codes: tuple[str, ...]
    contract_digest: str
    observation_id: str | None
    authority_id: str | None


def _canonical_bytes(value: object) -> bytes:
    def default(item: object) -> object:
        if isinstance(item, datetime):
            return item.isoformat()
        if isinstance(item, Enum):
            return item.value
        raise TypeError(f"unsupported canonical value: {type(item)!r}")

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=default,
    ).encode()


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _schema_document(repository_name: str, installed_directory: str) -> dict[str, object]:
    return canonical_resource_json(
        f"schemas/{repository_name}",
        f"{installed_directory}/{repository_name}",
    )


def _valid_document(document: object, repository_name: str, installed_directory: str) -> bool:
    schema = _schema_document(repository_name, installed_directory)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return not list(validator.iter_errors(document))


def _parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_route(value: Mapping[str, object]) -> RouteIdentity:
    return RouteIdentity(
        target_id=str(value["target_id"]),
        route_id=str(value["route_id"]),
        route_version=str(value["route_version"]),
        route_build_digest=str(value["route_build_digest"]),
        mode_id=str(value["mode_id"]),
        mode_digest=str(value["mode_digest"]),
        adapter_id=str(value["adapter_id"]),
        adapter_version=str(value["adapter_version"]),
    )


def parse_execution_contract(raw: Mapping[str, object]) -> ExecutionContract:
    """Parse the strict public contract and recompute its canonical digest."""
    if not _valid_document(
        raw,
        "sandbox-execution-contract-v0alpha1.schema.json",
        "contract-schema",
    ):
        raise ExecutionRouteDocumentError("execution-contract-invalid")
    requested = raw["requested_route"]
    canonicalization = raw["canonicalization"]
    assert isinstance(requested, Mapping) and isinstance(canonicalization, Mapping)
    contract = ExecutionContract(
        contract_id=str(raw["contract_id"]),
        contract_version=str(raw["contract_version"]),
        case_id=str(raw["case_id"]),
        requested_route=_parse_route(requested),
        fallback_policy=str(raw["fallback_policy"]),
    )
    if canonicalization.get("contract_digest") != contract.digest:
        raise ExecutionRouteDocumentError("execution-contract-digest-mismatch")
    return contract


def parse_execution_route_observation(raw: Mapping[str, object]) -> ExecutionRouteObservation:
    """Parse one raw external observation without treating it as authenticated."""
    if not _valid_document(
        raw,
        "sandbox-execution-route-observation-v0alpha1.schema.json",
        "route-schema",
    ):
        raise ExecutionRouteDocumentError("route-observation-invalid")
    effective_route = raw["effective_route"]
    assert isinstance(effective_route, Mapping)
    return ExecutionRouteObservation(
        observation_id=str(raw["observation_id"]),
        contract_digest=str(raw["contract_digest"]),
        run_id=str(raw["run_id"]),
        case_id=str(raw["case_id"]),
        attempt=int(raw["attempt"]),
        attempt_nonce=str(raw["attempt_nonce"]),
        environment_fingerprint=str(raw["environment_fingerprint"]),
        policy_digest=str(raw["policy_digest"]),
        execution_state=ExecutionState(str(raw["execution_state"])),
        effective_route=_parse_route(effective_route),
        fallback_used=bool(raw["fallback_used"]),
        degraded=bool(raw["degraded"]),
        observed_at_utc=_parse_instant(str(raw["observed_at_utc"])),
        monotonic_ns=int(raw["monotonic_ns"]),
        observer_source_id=str(raw["observer_source_id"]),
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _digest_string(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        return False
    return all(character in "0123456789abcdef" for character in value[7:])


def _natural_number(value: object, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _route_complete(route: RouteIdentity) -> bool:
    return (
        all(_nonempty(value) for value in asdict(route).values())
        and _digest_string(route.route_build_digest)
        and _digest_string(route.mode_digest)
    )


def _route_mismatch_reasons(requested: RouteIdentity, observed: RouteIdentity) -> tuple[str, ...]:
    reasons: list[str] = []
    if observed.target_id != requested.target_id:
        reasons.append("target-mismatch")
    if observed.route_id != requested.route_id:
        reasons.append("route-mismatch")
    if observed.route_version != requested.route_version:
        reasons.append("route-version-mismatch")
    if observed.route_build_digest != requested.route_build_digest:
        reasons.append("route-build-mismatch")
    if observed.mode_id != requested.mode_id or observed.mode_digest != requested.mode_digest:
        reasons.append("route-mode-mismatch")
    if observed.adapter_id != requested.adapter_id or observed.adapter_version != requested.adapter_version:
        reasons.append("adapter-mismatch")
    return tuple(reasons)


def evaluate_execution_route(
    contract: ExecutionContract,
    attempt: ExecutionAttemptBinding,
    observations: Sequence[ExecutionRouteObservation],
    authentications: Mapping[str, ObservationAuthentication],
    *,
    readiness: ReadinessState = ReadinessState.UNVERIFIED,
    evaluated_at_utc: datetime,
) -> RouteGateResult:
    """Evaluate exact route binding and fail closed to ``UNVERIFIED``.

    ``authentications`` is produced by an external trust-verification boundary;
    no field inside an observation is allowed to authenticate that observation.
    """
    effective_readiness = readiness if isinstance(readiness, ReadinessState) else ReadinessState.UNVERIFIED
    contract_digest = contract.digest

    if not observations:
        return RouteGateResult(
            gate_state=RouteGateState.UNVERIFIED,
            route_binding_state=RouteBindingState.MISSING,
            execution_state=ExecutionState.NOT_ATTEMPTED,
            readiness_state=effective_readiness,
            reason_codes=("execution-route-missing",),
            contract_digest=contract_digest,
            observation_id=None,
            authority_id=None,
        )

    if len(observations) != 1:
        return RouteGateResult(
            gate_state=RouteGateState.UNVERIFIED,
            route_binding_state=RouteBindingState.AMBIGUOUS,
            execution_state=ExecutionState.UNVERIFIED,
            readiness_state=effective_readiness,
            reason_codes=("effective-route-ambiguous",),
            contract_digest=contract_digest,
            observation_id=None,
            authority_id=None,
        )

    observation = observations[0]
    reasons: list[str] = []
    authentication_reasons: list[str] = []
    stale_reasons: list[str] = []
    execution_reasons: list[str] = []
    resolution_reasons: list[str] = []
    route_reasons: list[str] = []

    if (
        not _nonempty(contract.contract_id)
        or not _nonempty(contract.contract_version)
        or not _nonempty(contract.case_id)
        or not _route_complete(contract.requested_route)
        or contract.fallback_policy != "forbid"
    ):
        stale_reasons.append("execution-contract-invalid")
    if (
        not _digest_string(attempt.contract_digest)
        or not _nonempty(attempt.run_id)
        or not _nonempty(attempt.case_id)
        or not _natural_number(attempt.attempt, minimum=1)
        or not _nonempty(attempt.attempt_nonce)
        or not _digest_string(attempt.environment_fingerprint)
        or not _digest_string(attempt.policy_digest)
        or not _natural_number(attempt.window_started_monotonic_ns)
        or not _natural_number(attempt.window_finished_monotonic_ns)
    ):
        stale_reasons.append("attempt-binding-invalid")
    if attempt.contract_digest != contract_digest or attempt.case_id != contract.case_id:
        stale_reasons.append("contract-binding-mismatch")
    if (
        not _aware(attempt.window_started_at_utc)
        or not _aware(attempt.window_finished_at_utc)
        or attempt.window_started_at_utc > attempt.window_finished_at_utc
        or attempt.window_started_monotonic_ns > attempt.window_finished_monotonic_ns
    ):
        stale_reasons.append("attempt-window-invalid")

    authentication = authentications.get(observation.observation_id)
    if authentication is None:
        authentication_reasons.append("observation-not-authenticated")
    else:
        if authentication.authenticated is not True or not _nonempty(authentication.authority_id):
            authentication_reasons.append("observation-authentication-invalid")
        if authentication.subject_digest != observation.digest:
            authentication_reasons.append("observation-authentication-subject-mismatch")
        if (
            not _aware(evaluated_at_utc)
            or not _aware(authentication.valid_from_utc)
            or not _aware(authentication.valid_until_utc)
            or authentication.valid_from_utc > authentication.valid_until_utc
        ):
            authentication_reasons.append("observation-authentication-invalid")
        else:
            if evaluated_at_utc < authentication.valid_from_utc:
                authentication_reasons.append("observation-authentication-not-yet-valid")
            if evaluated_at_utc > authentication.valid_until_utc:
                authentication_reasons.append("observation-authentication-expired")

    if (
        not _nonempty(observation.observation_id)
        or not _nonempty(observation.run_id)
        or not _nonempty(observation.case_id)
        or not _natural_number(observation.attempt, minimum=1)
        or not _nonempty(observation.attempt_nonce)
        or not _digest_string(observation.contract_digest)
        or not _digest_string(observation.environment_fingerprint)
        or not _digest_string(observation.policy_digest)
        or not _natural_number(observation.monotonic_ns)
        or not _nonempty(observation.observer_source_id)
    ):
        route_reasons.append("route-observation-incomplete")
    if observation.contract_digest != contract_digest or observation.contract_digest != attempt.contract_digest:
        stale_reasons.append("contract-binding-mismatch")
    if (
        observation.run_id != attempt.run_id
        or observation.case_id != attempt.case_id
        or observation.attempt != attempt.attempt
        or observation.attempt_nonce != attempt.attempt_nonce
    ):
        stale_reasons.append("attempt-binding-mismatch")
    if (
        observation.environment_fingerprint != attempt.environment_fingerprint
        or observation.policy_digest != attempt.policy_digest
    ):
        stale_reasons.append("execution-context-mismatch")
    if not _aware(observation.observed_at_utc):
        stale_reasons.append("observation-outside-window")
    elif _aware(attempt.window_started_at_utc) and _aware(attempt.window_finished_at_utc):
        if not attempt.window_started_at_utc <= observation.observed_at_utc <= attempt.window_finished_at_utc:
            stale_reasons.append("observation-outside-window")
    if not attempt.window_started_monotonic_ns <= observation.monotonic_ns <= attempt.window_finished_monotonic_ns:
        stale_reasons.append("observation-outside-window")

    if observation.execution_state != ExecutionState.COMPLETED:
        if observation.execution_state == ExecutionState.HARNESS_ERROR:
            execution_reasons.append("execution-harness-error")
        else:
            execution_reasons.append("execution-not-completed")

    if observation.fallback_used is True:
        resolution_reasons.append("fallback-route-used")
    elif observation.fallback_used is not False:
        resolution_reasons.append("route-observation-invalid")
    if observation.degraded is True:
        resolution_reasons.append("degraded-route-used")
    elif observation.degraded is not False:
        resolution_reasons.append("route-observation-invalid")

    if not _route_complete(observation.effective_route):
        route_reasons.append("route-observation-incomplete")
    route_reasons.extend(_route_mismatch_reasons(contract.requested_route, observation.effective_route))

    for group in (
        authentication_reasons,
        stale_reasons,
        execution_reasons,
        resolution_reasons,
        route_reasons,
    ):
        for reason in group:
            if reason not in reasons:
                reasons.append(reason)

    if not reasons:
        return RouteGateResult(
            gate_state=RouteGateState.ELIGIBLE,
            route_binding_state=RouteBindingState.MATCH,
            execution_state=observation.execution_state,
            readiness_state=effective_readiness,
            reason_codes=(),
            contract_digest=contract_digest,
            observation_id=observation.observation_id,
            authority_id=authentication.authority_id if authentication else None,
        )

    if authentication_reasons:
        binding_state = RouteBindingState.UNVERIFIED
    elif stale_reasons:
        binding_state = RouteBindingState.STALE
    elif "fallback-route-used" in resolution_reasons:
        binding_state = RouteBindingState.FALLBACK
    elif "degraded-route-used" in resolution_reasons:
        binding_state = RouteBindingState.DEGRADED
    elif route_reasons:
        binding_state = RouteBindingState.MISMATCH
    else:
        binding_state = RouteBindingState.UNVERIFIED

    return RouteGateResult(
        gate_state=RouteGateState.UNVERIFIED,
        route_binding_state=binding_state,
        execution_state=observation.execution_state,
        readiness_state=effective_readiness,
        reason_codes=tuple(reasons),
        contract_digest=contract_digest,
        observation_id=observation.observation_id,
        authority_id=None,
    )
