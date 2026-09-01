import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "tests" / "fixtures" / "index.json"
REQUIRED_FIXTURE_FILES = {"provenance.json", "case.json", "trajectory.jsonl", "README.md"}


def _load_json(path: Path):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def _discover_indexed_fixture_paths():
    discovered = set()
    for category in ("replay", "recovery"):
        root = ROOT / "tests" / "fixtures" / category
        if not root.exists():
            continue
        for path in root.iterdir():
            if path.is_dir() and REQUIRED_FIXTURE_FILES <= {item.name for item in path.iterdir()}:
                discovered.add(path.relative_to(ROOT).as_posix())
    return discovered


def test_fixture_index_is_complete_and_preserves_truth_boundaries():
    index = _load_json(INDEX_PATH)
    entries = index["entries"]

    assert index["schema_version"] == "agentci.fixture-index.v0alpha1"
    assert entries

    case_ids = [entry["case_id"] for entry in entries]
    paths = [entry["path"] for entry in entries]
    assert len(case_ids) == len(set(case_ids))
    assert len(paths) == len(set(paths))
    assert set(paths) == _discover_indexed_fixture_paths()

    for entry in entries:
        fixture = ROOT / entry["path"]
        assert fixture.is_dir()
        assert REQUIRED_FIXTURE_FILES <= {item.name for item in fixture.iterdir()}

        provenance = _load_json(fixture / "provenance.json")
        case = _load_json(fixture / "case.json")

        assert provenance["case_id"] == entry["case_id"]
        assert case["case_id"] == entry["case_id"]
        assert provenance["source"]["url"] == entry["canonical_upstream"]
        assert provenance["source"]["reporter"] == entry["reporter"]
        assert provenance["agentci_reproduction_status"] == "UNVERIFIED"
        assert entry["agentci_reproduction_status"] == "UNVERIFIED"
        assert case["agentci_result"] == "UNVERIFIED"
