"""Provider-neutral execution-route binding for the first S1 claim.

The gate proves only that one completed execution was externally observed on
the exact route requested by its bound contract and attempt.  Eligibility is
not a sandbox verdict, containment result, or certification.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from .resource_loader import canonical_resource_json


API_VERSION = "agentci.dev/sandbox-execution/v0alpha1"
CONTRACT_KIND = "ExecutionContract"
OBSERVATION_KIND = "ExecutionRouteObservation"
AUTHENTICATION_API_VERSION = "agentci.dev/sandbox-route-authentication/v0alpha1"
AUTHENTICATION_KIND = "ObservationAuthentication"
ALGORITHM = "rsa-pkcs1v15-sha256"
_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")

# Trust roots are verifier-owned policy, never workload or observation data.
# AgentCI intentionally ships no real S1 route authority in this first slice.
TRUSTED_ROUTE_AUTHORITIES: Mapping[str, Mapping[str, object]] = MappingProxyType({})


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
    subject_digest: str
    authority_id: str
    key_id: str
    trust_epoch: int
    valid_from_utc: datetime
    valid_until_utc: datetime
    signature_b64: str
    algorithm: str = ALGORITHM

    @property
    def signed_payload(self) -> dict[str, object]:
        return {
            "apiVersion": AUTHENTICATION_API_VERSION,
            "kind": AUTHENTICATION_KIND,
            "algorithm": self.algorithm,
            "subject_digest": self.subject_digest,
            "authority_id": self.authority_id,
            "key_id": self.key_id,
            "trust_epoch": self.trust_epoch,
            "valid_from_utc": self.valid_from_utc,
            "valid_until_utc": self.valid_until_utc,
        }


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
    requested_route: RouteIdentity | None
    observed_route: RouteIdentity | None


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


def _route_complete(route: object) -> bool:
    if not isinstance(route, RouteIdentity):
        return False
    return (
        all(_nonempty(value) for value in asdict(route).values())
        and _digest_string(route.route_build_digest)
        and _digest_string(route.mode_digest)
    )


def _route_mismatch_reasons(requested: object, observed: object) -> tuple[str, ...]:
    if not isinstance(requested, RouteIdentity) or not isinstance(observed, RouteIdentity):
        return ()
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


def _safe_contract_digest(contract: object) -> str:
    if not isinstance(contract, ExecutionContract):
        return ""
    try:
        return contract.digest
    except (AttributeError, TypeError, ValueError):
        return ""


def _safe_observation_digest(observation: object) -> str:
    if not isinstance(observation, ExecutionRouteObservation):
        return ""
    try:
        return observation.digest
    except (AttributeError, TypeError, ValueError):
        return ""


def _verify_payload_signature(
    payload: Mapping[str, object],
    signature_b64: object,
    trust: object,
) -> bool:
    if not isinstance(trust, Mapping):
        return False
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        modulus = int(trust["modulus_hex"], 16)
        exponent = int(trust["exponent"])
        encoded_payload = _canonical_bytes(dict(payload))
    except (KeyError, TypeError, ValueError):
        return False
    if modulus <= 0 or exponent <= 1:
        return False
    size = (modulus.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    encoded = pow(int.from_bytes(signature, "big"), exponent, modulus).to_bytes(size, "big")
    digest_info = _DIGEST_INFO_PREFIX + hashlib.sha256(encoded_payload).digest()
    padding = size - len(digest_info) - 3
    if padding < 8:
        return False
    return encoded == b"\x00\x01" + b"\xff" * padding + b"\x00" + digest_info


def _authentication_signature_valid(
    authentication: object,
    trusted_authorities: Mapping[str, Mapping[str, object]],
) -> bool:
    if not isinstance(authentication, ObservationAuthentication):
        return False
    if (
        authentication.algorithm != ALGORITHM
        or not _nonempty(authentication.authority_id)
        or not _nonempty(authentication.key_id)
        or not _natural_number(authentication.trust_epoch, minimum=1)
    ):
        return False
    trust = trusted_authorities.get(authentication.authority_id)
    if not isinstance(trust, Mapping):
        return False
    if (
        trust.get("algorithm") != authentication.algorithm
        or trust.get("key_id") != authentication.key_id
        or trust.get("trust_epoch") != authentication.trust_epoch
    ):
        return False
    return _verify_payload_signature(
        authentication.signed_payload,
        authentication.signature_b64,
        trust,
    )


def evaluate_execution_route(
    contract: ExecutionContract,
    attempt: ExecutionAttemptBinding,
    observations: Sequence[ExecutionRouteObservation],
    authentications: Mapping[str, ObservationAuthentication],
    *,
    readiness: ReadinessState = ReadinessState.UNVERIFIED,
    evaluated_at_utc: datetime,
    trusted_authorities: Mapping[str, Mapping[str, object]] | None = None,
) -> RouteGateResult:
    """Evaluate exact route binding and fail closed to ``UNVERIFIED``.

    Authentication signatures are checked here against verifier-supplied trust
    policy.  The default policy is empty: neither an observation nor an
    authentication object can declare its own authority.
    """
    effective_readiness = readiness if isinstance(readiness, ReadinessState) else ReadinessState.UNVERIFIED
    trust_policy = (
        trusted_authorities
        if isinstance(trusted_authorities, Mapping)
        else TRUSTED_ROUTE_AUTHORITIES
    )
    contract_digest = _safe_contract_digest(contract)
    requested_route = (
        contract.requested_route
        if isinstance(contract, ExecutionContract) and isinstance(contract.requested_route, RouteIdentity)
        else None
    )

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
            requested_route=requested_route,
            observed_route=None,
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
            requested_route=requested_route,
            observed_route=None,
        )

    observation = observations[0]
    if not isinstance(observation, ExecutionRouteObservation):
        return RouteGateResult(
            gate_state=RouteGateState.UNVERIFIED,
            route_binding_state=RouteBindingState.MISMATCH,
            execution_state=ExecutionState.UNVERIFIED,
            readiness_state=effective_readiness,
            reason_codes=("route-observation-incomplete",),
            contract_digest=contract_digest,
            observation_id=None,
            authority_id=None,
            requested_route=requested_route,
            observed_route=None,
        )
    observed_route = (
        observation.effective_route
        if isinstance(observation.effective_route, RouteIdentity)
        else None
    )
    if not isinstance(contract, ExecutionContract) or not isinstance(attempt, ExecutionAttemptBinding):
        reason = (
            "execution-contract-invalid"
            if not isinstance(contract, ExecutionContract)
            else "attempt-binding-invalid"
        )
        return RouteGateResult(
            gate_state=RouteGateState.UNVERIFIED,
            route_binding_state=RouteBindingState.STALE,
            execution_state=(
                observation.execution_state
                if isinstance(observation.execution_state, (ExecutionState, str))
                else ExecutionState.UNVERIFIED
            ),
            readiness_state=effective_readiness,
            reason_codes=(reason,),
            contract_digest=contract_digest,
            observation_id=(
                observation.observation_id if _nonempty(observation.observation_id) else None
            ),
            authority_id=None,
            requested_route=requested_route,
            observed_route=observed_route,
        )
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

    authentication = (
        authentications.get(observation.observation_id)
        if isinstance(authentications, Mapping)
        else None
    )
    if authentication is None:
        authentication_reasons.append("observation-not-authenticated")
    elif not isinstance(authentication, ObservationAuthentication):
        authentication_reasons.append("observation-authentication-invalid")
    else:
        if not _authentication_signature_valid(authentication, trust_policy):
            authentication_reasons.append("observation-authentication-invalid")
        if authentication.subject_digest != _safe_observation_digest(observation):
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
    if (
        _natural_number(attempt.window_started_monotonic_ns)
        and _natural_number(attempt.window_finished_monotonic_ns)
        and _natural_number(observation.monotonic_ns)
        and not attempt.window_started_monotonic_ns
        <= observation.monotonic_ns
        <= attempt.window_finished_monotonic_ns
    ):
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
            requested_route=requested_route,
            observed_route=observed_route,
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
        requested_route=requested_route,
        observed_route=observed_route,
    )
