import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "tests" / "fixtures" / "sandbox" / "authority" / "vectors.json"
EXPECTED_IDS = {"D-01","D-02","D-03","D-04","D-05","D-06","D-07","D-08","D-09","D-10","D-11","D-12","D-13a","D-13b","D-14","D-15a","D-15b","D-15c","D-15d","D-16"}
ALLOWED_RESULTS = {"DENY", "PERMIT", "UNVERIFIED", "EXPANSION_GATE"}

def _load():
    return json.loads(VECTORS.read_text(encoding="utf-8"))

def _atomic_tuple(item):
    return (item["action"], item["resource"], item["context"])

def _reject_duplicate_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate object member: {key}")
        out[key] = value
    return out

def _oracle(vector):
    f, rule = vector["facts"], vector["rule"]
    if rule == "self_grant":
        return "DENY" if f["requester"] == f["beneficiary"] == f["issuer"] and not f["issuer_trusted"] else "UNVERIFIED"
    if rule == "approval_replay":
        if not f["reference_chain_resolved"]: return "UNVERIFIED"
        return "DENY" if f["grant_policy_epoch"] != f["effective_policy_epoch"] or f["grant_authority_epoch"] != f["effective_authority_epoch"] else "PERMIT"
    if rule == "multi_principal_union":
        requested = _atomic_tuple(f["requested"])
        exact = [g for g in f["atomic_grants"] if g["principal"] == f["principal"] and _atomic_tuple(g) == requested]
        return "PERMIT" if exact else "DENY"
    if rule == "alternate_channel":
        return "DENY" if f["decision"] == "DENY" and not f["separate_grant_for_attempt"] else "UNVERIFIED"
    if rule == "broker_scope":
        ok = f["grant_audience"] == f["request_audience"] and set(f["request_scope"]).issubset(set(f["grant_scope"])) and f["credential_epoch"] == f["current_credential_epoch"]
        return "PERMIT" if ok else "DENY"
    if rule == "effective_endpoint":
        return "UNVERIFIED" if not f["resolved_socket_endpoint"] or not f["final_upstream"] or not f["receipt_endpoint_bound"] else "PERMIT"
    if rule == "stale_restore_authority":
        stale = f["restore_epoch"] != f["capture_epoch"] and (f["authority_epoch_at_capture"] != f["current_authority_epoch"] or f["credential_epoch_at_capture"] != f["current_credential_epoch"])
        return "DENY" if stale and f["socket_continuity"] == "preserved" and not f["session_revalidated"] else "UNVERIFIED"
    if rule == "delta_classification":
        if not f["normalizable"] or not f["enforcement_known"]: return "EXPANSION_GATE"
        old_tuples = {_atomic_tuple(x) for x in f["old"]}; new_tuples = {_atomic_tuple(x) for x in f["new"]}
        if old_tuples == new_tuples and f["old"] == f["new"]: return "PERMIT"
        return "PERMIT" if new_tuples < old_tuples else "EXPANSION_GATE"
    if rule == "delegation_actor_loss":
        return "DENY" if f["delegation_mode"] == "delegation" and f["actor_required"] and not f["actor"] else "UNVERIFIED"
    if rule == "unknown_enforcement":
        return "UNVERIFIED" if f["enforcement_locus"] == "unknown" or not f["receipt_resolved"] else f["decision"]
    if rule == "explicit_deny":
        return "DENY" if f["same_atomic_tuple"] and "DENY" in f["matching_effects"] else "UNVERIFIED"
    if rule == "stale_policy_attachment":
        return "DENY" if f["attachment_policy_epoch"] != f["effective_policy_epoch"] and not f["attachment_revalidated"] else "UNVERIFIED"
    if rule == "authority_causation":
        required = [f["trust_root_ref"], f["principal_attestation_ref"], f["grant_ref"], f["decision_ref"], f["receipt_ref"]]
        if f["provenance_strength"] != "decision-bound-native-receipt" or not f["immutable_refs_resolved"] or not all(required): return "UNVERIFIED"
        return f["receipt_result"] if f["receipt_result"] in {"DENY", "PERMIT"} else "UNVERIFIED"
    if rule == "unique_authority_identity":
        matches = [item for item in f["objects"] if item["id"] == f["reference"]]
        return "UNVERIFIED" if len(matches) != 1 else matches[0].get("effect", "UNVERIFIED")
    if rule == "review_independence":
        if not f["reviewer_identity_ref_resolved"]: return "UNVERIFIED"
        if f["reviewer_principal_ref"] == f["author_principal_ref"]: return "UNVERIFIED"
        if f["independence_class"] != "distinct-principal-verified": return "UNVERIFIED"
        if f["reviewed_head"] != f["subject_head"]: return "UNVERIFIED"
        return "PERMIT"
    if rule == "raw_authority_duplicate_key":
        try:
            json.loads(f["raw_authority_json"], object_pairs_hook=_reject_duplicate_pairs)
        except (json.JSONDecodeError, ValueError):
            return "UNVERIFIED"
        return "UNVERIFIED"
    raise AssertionError(f"unknown rule: {rule}")

def test_vector_pack_is_complete_and_single_oracle():
    vectors = _load()["vectors"]
    assert {v["id"] for v in vectors} == EXPECTED_IDS
    assert len(vectors) == len(EXPECTED_IDS)
    assert all(isinstance(v["expected"], str) and v["expected"] in ALLOWED_RESULTS for v in vectors)

def test_vector_pack_is_deterministically_serializable():
    doc = _load(); first = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    second = json.dumps(json.loads(first), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert first == second

def test_all_vectors_match_the_deterministic_oracle():
    for vector in _load()["vectors"]: assert _oracle(vector) == vector["expected"], vector["id"]

def test_d13_has_both_required_provenance_variants():
    by_id = {v["id"]: v for v in _load()["vectors"]}
    assert by_id["D-13a"]["expected"] == "UNVERIFIED" and by_id["D-13a"]["facts"]["provenance_strength"] == "behavioral-only"
    assert by_id["D-13b"]["expected"] == "DENY" and by_id["D-13b"]["facts"]["provenance_strength"] == "decision-bound-native-receipt"
    for key in ("enforcement_locus","observer_locus","policy_epoch","authority_epoch","credential_epoch"):
        assert key in by_id["D-13a"]["facts"] and key in by_id["D-13b"]["facts"]

def test_d14_duplicate_security_identity_is_not_order_selectable():
    vector = next(v for v in _load()["vectors"] if v["id"] == "D-14")
    assert _oracle(vector) == "UNVERIFIED"
    reversed_vector = json.loads(json.dumps(vector))
    reversed_vector["facts"]["objects"].reverse()
    assert _oracle(reversed_vector) == "UNVERIFIED"

def test_d15_review_independence_requires_distinct_verified_principal_and_exact_head():
    by_id = {v["id"]: v for v in _load()["vectors"]}
    assert _oracle(by_id["D-15a"]) == "UNVERIFIED"
    assert _oracle(by_id["D-15b"]) == "PERMIT"
    assert _oracle(by_id["D-15c"]) == "UNVERIFIED"
    assert _oracle(by_id["D-15d"]) == "UNVERIFIED"
    same_principal = json.loads(json.dumps(by_id["D-15b"]))
    same_principal["facts"]["reviewer_principal_ref"] = same_principal["facts"]["author_principal_ref"]
    assert _oracle(same_principal) == "UNVERIFIED"

def test_d16_rejects_duplicate_raw_authority_member_before_semantic_resolution():
    vector = next(v for v in _load()["vectors"] if v["id"] == "D-16")
    raw = vector["facts"]["raw_authority_json"]
    assert json.loads(raw)["effect"] == "PERMIT"  # ordinary parsing silently overwrites DENY
    assert _oracle(vector) == "UNVERIFIED"
    try:
        json.loads(raw, object_pairs_hook=_reject_duplicate_pairs)
    except ValueError as exc:
        assert "duplicate object member: effect" in str(exc)
    else:
        raise AssertionError("duplicate authority member was not rejected")

def test_vectors_do_not_embed_secret_material():
    raw = VECTORS.read_text(encoding="utf-8").lower()
    assert not any(term in raw for term in ["private_key","client_secret","access_token","refresh_token","password"])
