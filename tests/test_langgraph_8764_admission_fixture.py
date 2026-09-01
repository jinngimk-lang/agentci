import copy
import json
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "recovery" / "langgraph-8764-precheckpoint-admission-gap"


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _load_trajectory():
    return [
        json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        for line in (FIXTURE / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _classify_admission(case):
    admission = case["observations"]["external_admission"]
    checkpoints = case["observations"]["durable_runtime"]["checkpoint_count"]

    if admission["status"] != "observed":
        return "UNVERIFIED"
    if admission["decision"] == "not_admitted":
        return "NOT_ADMITTED"
    if admission["decision"] == "accepted" and checkpoints == 0:
        return "ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING"
    if admission["decision"] == "accepted" and checkpoints > 0:
        return "DURABLE_ADMISSION_EVIDENCE_PRESENT"
    return "UNVERIFIED"


def test_langgraph_8764_fixture_preserves_reporter_correction_and_unverified_boundary():
    provenance = _load_json(FIXTURE / "provenance.json")
    case = _load_json(FIXTURE / "case.json")

    assert provenance["source"]["url"] == "https://github.com/langchain-ai/langgraph/issues/8764"
    assert provenance["source"]["reporter"] == "mstevens843"
    assert provenance["source"]["observed_commit"] is None
    assert provenance["source"]["observed_commit_status"] == "unavailable"
    assert provenance["clarification"]["author"] == "mstevens843"
    assert provenance["clarification"]["effect_count"] == 0
    assert provenance["clarification"]["durable_checkpoint_count"] == 0
    assert provenance["agentci_reproduction_status"] == "UNVERIFIED"
    assert case["agentci_result"] == "UNVERIFIED"


def test_runtime_observations_do_not_self_promote_into_admission_authority():
    case = _load_json(FIXTURE / "case.json")

    assert case["correlation"] == {
        "thread_id": "accepted-run",
        "thread_id_role": "correlation-only",
        "proves_admission": False,
    }
    assert case["crash_boundary"]["process_exit_code"] == -9
    assert case["crash_boundary"]["first_checkpoint_commit_observed"] is False
    assert case["observations"]["external_effect"]["effect_count"] == 0
    assert case["observations"]["durable_runtime"]["checkpoint_count"] == 0
    assert case["observations"]["recovery"]["error_class"] == "EmptyInputError"
    assert case["observations"]["external_admission"] == {
        "status": "unavailable",
        "authoritative_source": None,
        "decision": None,
    }
    assert _classify_admission(case) == "UNVERIFIED"
    assert case["observed_classification"]["admission"] == "UNVERIFIED"


def test_authoritative_admission_evidence_changes_only_the_admission_classification():
    case = _load_json(FIXTURE / "case.json")

    admitted = copy.deepcopy(case)
    admitted["observations"]["external_admission"] = {
        "status": "observed",
        "authoritative_source": "fixture-control-ledger",
        "decision": "accepted",
    }
    assert _classify_admission(admitted) == "ADMITTED_BUT_RUNTIME_EVIDENCE_MISSING"

    not_admitted = copy.deepcopy(case)
    not_admitted["observations"]["external_admission"] = {
        "status": "observed",
        "authoritative_source": "fixture-control-ledger",
        "decision": "not_admitted",
    }
    assert _classify_admission(not_admitted) == "NOT_ADMITTED"

    assert admitted["observations"]["external_effect"]["effect_count"] == 0
    assert not_admitted["observations"]["external_effect"]["effect_count"] == 0
    assert admitted["observations"]["durable_runtime"]["checkpoint_count"] == 0
    assert not_admitted["observations"]["durable_runtime"]["checkpoint_count"] == 0


def test_trajectory_preserves_event_order_without_inventing_acceptance_or_effects():
    events = _load_trajectory()

    assert [event["sequence"] for event in events] == [1, 2, 3, 4, 5]
    assert [event["event_type"] for event in events] == [
        "invocation-correlated",
        "first-checkpoint-persistence-entered",
        "post-crash-observed",
        "fresh-process-recovery-attempted",
        "admission-durability-result",
    ]
    assert all(event["thread_id"] == "accepted-run" for event in events)
    assert events[0]["proves_admission"] is False
    assert events[2]["external_effect_count"] == 0
    assert events[2]["durable_checkpoint_count"] == 0
    assert events[3]["error_class"] == "EmptyInputError"
    assert events[4]["external_admission_evidence"] == "unavailable"
    assert events[4]["admission_classification"] == "UNVERIFIED"
    assert events[4]["verdict"] == "UNVERIFIED"


def test_fixture_adds_no_langgraph_core_dependency():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    assert not any(dependency.lower().startswith("langgraph") for dependency in dependencies)

    for path in (ROOT / "src" / "agentci").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import langgraph" not in source
        assert "from langgraph" not in source
