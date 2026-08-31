import hashlib
import json
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "replay" / "langgraph-8582-send-untracked"


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


def _shape_digest(descriptor):
    canonical = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _by_name(descriptor):
    return {dependency["name"]: dependency for dependency in descriptor}


def test_langgraph_8582_fixture_preserves_provenance_and_unverified_boundary():
    provenance = _load_json(FIXTURE / "provenance.json")
    case = _load_json(FIXTURE / "case.json")

    assert provenance["source"] == {
        "url": "https://github.com/langchain-ai/langgraph/issues/8582",
        "repository": "langchain-ai/langgraph",
        "issue_number": 8582,
        "reporter": "Hello-world-Prakash",
        "observed_commit": "d56666f7f",
        "reported_at": "2026-08-10",
    }
    assert provenance["capture"]["upstream_contract"] == "UNCONFIRMED"
    assert provenance["agentci_reproduction_status"] == "UNVERIFIED"
    assert case["agentci_result"] == "UNVERIFIED"
    assert set(case["acceptable_outcomes"]) == {
        "faithful-reconstruction",
        "explicit-non-resumable-error",
        "UNVERIFIED",
    }


def test_input_shape_digests_expose_the_missing_untracked_dependency():
    case = _load_json(FIXTURE / "case.json")
    initial = case["initial_input_shape"]
    checkpoint = case["checkpoint"]["state_shape"]
    resumed = case["resumed_input_shape"]

    assert initial["canonical_shape_digest"] == _shape_digest(initial["descriptor"])
    assert checkpoint["canonical_shape_digest"] == _shape_digest(checkpoint["descriptor"])
    assert resumed["canonical_shape_digest"] == _shape_digest(resumed["descriptor"])
    assert initial["canonical_shape_digest"] != resumed["canonical_shape_digest"]
    assert checkpoint["canonical_shape_digest"] == resumed["canonical_shape_digest"]

    initial_dependencies = _by_name(initial["descriptor"])
    checkpoint_dependencies = _by_name(checkpoint["descriptor"])
    resumed_dependencies = _by_name(resumed["descriptor"])
    assert initial_dependencies["messages"]["tracking"] == "tracked"
    assert checkpoint_dependencies["messages"]["presence"] == "present"
    assert resumed_dependencies["messages"]["presence"] == "present"
    assert initial_dependencies["resource"] == {
        "name": "resource",
        "tracking": "untracked",
        "presence": "present",
        "type_name": "RuntimeResource",
    }
    assert checkpoint_dependencies["resource"]["presence"] == "absent"
    assert resumed_dependencies["resource"]["presence"] == "absent"


def test_trajectory_binds_one_case_local_task_without_claiming_runtime_identity():
    case = _load_json(FIXTURE / "case.json")
    events = _load_trajectory()

    assert [event["sequence"] for event in events] == [1, 2, 3, 4, 5]
    assert [event["event_type"] for event in events] == [
        "task-dispatched",
        "task-failed",
        "checkpoint-observed",
        "task-resumed",
        "replay-fidelity-result",
    ]
    task_ref = case["task_identity"]["logical_task_ref"]
    assert case["task_identity"]["logical_task_ref_scope"] == "case-local"
    assert case["task_identity"]["runtime_task_id_status"] == "unavailable"
    assert all(event["logical_task_ref"] == task_ref for event in events)
    assert all(event["runtime_task_id"] is None for event in events)
    assert events[2]["checkpoint_id"] is None
    assert events[2]["checkpoint_id_status"] == "unavailable"
    assert events[2]["pending_workers"] == ["worker"]
    assert events[4]["missing_material_dependencies"] == ["resource"]
    assert events[4]["input_shape_digest_match"] is False
    assert events[4]["classification"] == "NON_FAITHFUL"
    assert events[4]["verdict"] == "UNVERIFIED"


def test_fixture_contains_no_runtime_value_and_adds_no_langgraph_core_dependency():
    fixture_text = "\n".join(path.read_text(encoding="utf-8") for path in FIXTURE.iterdir())
    assert "runtime-secret" not in fixture_text
    assert "resource_value" not in fixture_text
    assert "secret_value" not in fixture_text

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]
    assert not any(dependency.lower().startswith("langgraph") for dependency in dependencies)
    for path in (ROOT / "src" / "agentci").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import langgraph" not in source
        assert "from langgraph" not in source
