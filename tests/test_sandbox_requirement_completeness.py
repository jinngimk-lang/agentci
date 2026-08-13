import copy
import json

import scripts.validate_sandbox_evidence as validator


def test_canonical_assertion_requirement_without_expected_result_is_not_loadable(tmp_path, monkeypatch):
    root = validator.ROOT
    case_path = root / "examples" / "sandbox" / "testcases" / "sandbox-sensitive-canary-v0alpha1.json"
    test_case = json.loads(case_path.read_text(encoding="utf-8"))
    broken = copy.deepcopy(test_case)
    broken["assertion_requirements"][0].pop("expected_result")

    case_dir = tmp_path / "testcases"
    case_dir.mkdir()
    (case_dir / f"{broken['case_id']}.json").write_text(json.dumps(broken), encoding="utf-8")

    monkeypatch.setattr(validator, "TEST_CASE_DIR", case_dir)
    validator._load_test_case.cache_clear()
    try:
        assert validator._load_test_case(broken["case_id"]) is None
    finally:
        validator._load_test_case.cache_clear()
