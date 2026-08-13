import copy
import json
import scripts.validate_sandbox_evidence as sandbox_validator


def test_pass_evidence_is_bound_to_immutable_testcase_content(tmp_path, monkeypatch):
    root=sandbox_validator.ROOT
    fixture=json.loads((root/"examples"/"sandbox"/"v0alpha1-pass-control-evidence.json").read_text(encoding="utf-8"))
    assert sandbox_validator.expected_verdict(fixture)=="PASS"
    original_case=json.loads((root/"examples"/"sandbox"/"testcases"/f"{fixture['case_id']}.json").read_text(encoding="utf-8"))
    mutated_case=copy.deepcopy(original_case); mutated_case["oracle"]=["mutated oracle that changes certification semantics"]
    case_dir=tmp_path/"testcases"; case_dir.mkdir(); (case_dir/f"{fixture['case_id']}.json").write_text(json.dumps(mutated_case),encoding="utf-8")
    monkeypatch.setattr(sandbox_validator,"TEST_CASE_DIR",case_dir); sandbox_validator._load_test_case.cache_clear()
    try: assert sandbox_validator.expected_verdict(fixture) != "PASS"
    finally: sandbox_validator._load_test_case.cache_clear()
