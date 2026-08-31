from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from agentci.sandbox.execution_route import (
    ExecutionContract,
    ExecutionRouteDocumentError,
    ExecutionState,
    RouteIdentity,
    parse_execution_contract,
    parse_execution_route_observation,
)


ROOT = Path(__file__).resolve().parents[1]


def _route() -> RouteIdentity:
    return RouteIdentity(
        target_id="reference-target",
        route_id="isolated-route",
        route_version="2026.08",
        route_build_digest="sha256:" + "1" * 64,
        mode_id="strict",
        mode_digest="sha256:" + "2" * 64,
        adapter_id="agentci-reference-adapter",
        adapter_version="0.1.0",
    )


def _contract_document() -> dict[str, object]:
    contract = ExecutionContract(
        contract_id="matched-route-v0alpha1",
        contract_version="v0alpha1",
        case_id="authorized-utility",
        requested_route=_route(),
    )
    return {
        "apiVersion": "agentci.dev/sandbox-execution/v0alpha1",
        "kind": "ExecutionContract",
        "contract_id": contract.contract_id,
        "contract_version": contract.contract_version,
        "case_id": contract.case_id,
        "requested_route": {
            "target_id": contract.requested_route.target_id,
            "route_id": contract.requested_route.route_id,
            "route_version": contract.requested_route.route_version,
            "route_build_digest": contract.requested_route.route_build_digest,
            "mode_id": contract.requested_route.mode_id,
            "mode_digest": contract.requested_route.mode_digest,
            "adapter_id": contract.requested_route.adapter_id,
            "adapter_version": contract.requested_route.adapter_version,
        },
        "fallback_policy": "forbid",
        "canonicalization": {
            "algorithm": "agentci-json-c14n-v0alpha1",
            "contract_digest": contract.digest,
        },
    }


def _observation_document(contract_digest: str) -> dict[str, object]:
    return {
        "apiVersion": "agentci.dev/sandbox-execution/v0alpha1",
        "kind": "ExecutionRouteObservation",
        "observation_id": "observation-001",
        "contract_digest": contract_digest,
        "run_id": "run-001",
        "case_id": "authorized-utility",
        "attempt": 1,
        "attempt_nonce": "nonce-001",
        "environment_fingerprint": "sha256:" + "3" * 64,
        "policy_digest": "sha256:" + "4" * 64,
        "execution_state": "completed",
        "effective_route": _contract_document()["requested_route"],
        "fallback_used": False,
        "degraded": False,
        "observed_at_utc": "2026-08-29T07:00:00Z",
        "monotonic_ns": 150,
        "observer_source_id": "external-observer-001",
    }


def test_canonical_route_documents_parse_without_self_authenticating() -> None:
    contract = parse_execution_contract(_contract_document())
    observation = parse_execution_route_observation(_observation_document(contract.digest))

    assert contract.digest == _contract_document()["canonicalization"]["contract_digest"]
    assert observation.contract_digest == contract.digest
    assert observation.execution_state is ExecutionState.COMPLETED
    assert observation.observed_at_utc == datetime(2026, 8, 29, 7, 0, tzinfo=timezone.utc)
    assert not hasattr(observation, "authenticated")
    assert not hasattr(observation, "backend_verdict")


@pytest.mark.parametrize("forbidden", ["certified", "secure", "backend_verdict", "verdict"])
def test_observation_schema_rejects_forbidden_claim_fields(forbidden: str) -> None:
    contract = parse_execution_contract(_contract_document())
    document = _observation_document(contract.digest)
    document[forbidden] = True

    with pytest.raises(ExecutionRouteDocumentError) as caught:
        parse_execution_route_observation(document)

    assert caught.value.code == "route-observation-invalid"


def test_contract_digest_is_recomputed_instead_of_trusted() -> None:
    document = _contract_document()
    document["canonicalization"]["contract_digest"] = "sha256:" + "9" * 64

    with pytest.raises(ExecutionRouteDocumentError) as caught:
        parse_execution_contract(document)

    assert caught.value.code == "execution-contract-digest-mismatch"


@pytest.mark.parametrize(
    "mutation",
    [
        {"execution_state": "succeeded"},
        {"fallback_used": "false"},
        {"observer_source_id": ""},
        {"effective_route": {"target_id": "only-one-field"}},
    ],
)
def test_observation_schema_fails_closed_on_incomplete_or_unknown_values(mutation) -> None:
    contract = parse_execution_contract(_contract_document())
    document = _observation_document(contract.digest)
    document.update(deepcopy(mutation))

    with pytest.raises(ExecutionRouteDocumentError) as caught:
        parse_execution_route_observation(document)

    assert caught.value.code == "route-observation-invalid"


@pytest.mark.parametrize(
    "schema_name",
    [
        "sandbox-execution-contract-v0alpha1.schema.json",
        "sandbox-execution-route-observation-v0alpha1.schema.json",
    ],
)
def test_route_schemas_are_strict_draft_2020_12_documents(schema_name: str) -> None:
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False

    sample = _contract_document() if "contract" in schema_name else _observation_document(
        _contract_document()["canonicalization"]["contract_digest"]
    )
    assert not list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(sample))


def test_readme_marks_route_binding_as_main_only_eligibility_not_s1_completion() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()

    assert "0.3.0.dev0" in text
    assert "main-only s1 route-binding gate" in text
    assert "eligible is not pass" in text
    assert "does not execute a backend" in text
    assert "s1 remains unverified" in text


@pytest.mark.parametrize("relative_path", ["llms.txt", "skills/agentci/SKILL.md"])
def test_agent_discovery_surfaces_expose_the_truth_bounded_route_gate(relative_path: str) -> None:
    text = (ROOT / relative_path).read_text(encoding="utf-8").lower()

    assert "s1-exec-route-001" in text
    assert "0.3.0.dev0" in text
    assert "eligible is not pass" in text
    assert "does not execute a backend" in text
    assert "s1 remains unverified" in text


def test_route_design_and_plan_match_the_public_implementation_names() -> None:
    design = (ROOT / "docs/architecture/s1-execution-route-binding.md").read_text(encoding="utf-8")
    plan = (ROOT / "docs/operations/s1-execution-route-binding-plan.md").read_text(encoding="utf-8")

    assert "RouteGateStatus" not in design
    assert "all six route identity fields" not in design
    assert "requested route and the single observed route" in design
    assert "src/agentci/sandbox/execution_route.py" in plan
    assert "src/agentci/sandbox/route_binding.py" not in plan
