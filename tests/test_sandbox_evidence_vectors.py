import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "sandbox" / "evidence"
CASES = FIXTURES / "e-cases-v0alpha2.json"
VECTORS = FIXTURES / "canonicalizer-golden-vectors-v0alpha2.json"
SCHEMA = ROOT / "schemas" / "sandbox-certification-v0alpha1.schema.json"


def _strict_loads(text: str):
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=reject_duplicate_keys)


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _vector_digest(domain, payload):
    framed = f"agentci:{domain}:v0alpha2\n" + _canonical_json(payload)
    return "sha256:" + hashlib.sha256(framed.encode("utf-8")).hexdigest()


def test_e_corpus_contains_exactly_fourteen_unique_concrete_testcases():
    document = _strict_loads(CASES.read_text(encoding="utf-8"))
    cases = document["cases"]
    assert [case["case_id"] for case in cases] == [f"E-{i:02d}" for i in range(1, 15)]
    assert len({case["case_id"] for case in cases}) == 14
    required = set(json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["TestCase"]["required"])
    for case in cases:
        assert case["apiVersion"] == "agentci.dev/sandbox/v0alpha1"
        assert case["kind"] == "TestCase"
        assert required.issubset(case)
        assert case["probe"]["timeout_ms"] <= 5000
        assert case["oracle"]
        assert case["cleanup"]
        assert case["mandatory_assertions"]
        assert case["authorized_utility"]


def test_golden_vectors_are_reproducible_and_domain_separated():
    document = _strict_loads(VECTORS.read_text(encoding="utf-8"))
    vectors = document["vectors"]
    for vector in vectors:
        assert _canonical_json(vector["payload"]) == vector["canonical_json"]
        assert _vector_digest(vector["domain"], vector["payload"]) == vector["expected_digest"]
    payload = vectors[0]["payload"]
    assert _vector_digest("testcase", payload) != _vector_digest("run-evidence", payload)


def test_key_order_is_irrelevant_but_policy_history_sequence_is_not():
    document = _strict_loads(VECTORS.read_text(encoding="utf-8"))
    by_id = {vector["vector_id"]: vector for vector in document["vectors"]}
    assert by_id["V-01"]["expected_digest"] == by_id["V-02"]["expected_digest"]
    assert by_id["V-03"]["expected_digest"] != by_id["V-04"]["expected_digest"]


def test_duplicate_json_keys_are_rejected_before_hashing():
    try:
        _strict_loads('{"event_id":"one","event_id":"two"}')
    except ValueError as exc:
        assert "duplicate JSON key" in str(exc)
    else:
        raise AssertionError("duplicate key was silently accepted")
