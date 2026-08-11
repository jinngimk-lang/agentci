import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "tests" / "fixtures" / "sandbox" / "authority" / "vectors.json"
EXPECTED_IDS = {
    "D-01", "D-02", "D-03", "D-04", "D-05", "D-06", "D-07", "D-08",
    "D-09", "D-10", "D-11", "D-12", "D-13a", "D-13b",
}
ALLOWED_RESULTS = {"DENY", "PERMIT", "UNVERIFIED", "EXPANSION_GATE"}


def _load():
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def _atomic_tuple(item):
    return (item["action"], item["resource"], item["context"])


def _oracle(vector):
    f = vector["facts"]
    rule = vector["rule"]

    if rule == "self_grant":
        if f["requester"] == f["beneficiary"] == f["issuer"] and not f["issuer_trusted"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "approval_replay":
        if not f["reference_chain_resolved"]:
            return "UNVERIFIED"
        if f["grant_policy_epoch"] != f["effective_policy_epoch"] or f["grant_authority_epoch"] != f["effective_authority_epoch"]:
            return "DENY"
        return "PERMIT"

    if rule == "multi_principal_union":
        requested = _atomic_tuple(f["requested"])
        exact = [g for g in f["atomic_grants"] if g["principal"] == f["principal"] and _atomic_tuple(g) == requested]
        return "PERMIT" if exact else "DENY"

    if rule == "alternate_channel":
        if f["decision"] == "DENY" and not f["separate_grant_for_attempt"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "broker_scope":
        audience_ok = f["grant_audience"] == f["request_audience"]
        scope_ok = set(f["request_scope"]).issubset(set(f["grant_scope"]))
        epoch_ok = f["credential_epoch"] == f["current_credential_epoch"]
        return "PERMIT" if audience_ok and scope_ok and epoch_ok else "DENY"

    if rule == "effective_endpoint":
        material = [f["resolved_socket_endpoint"], f["final_upstream"]]
        if not all(material) or not f["receipt_endpoint_bound"]:
            return "UNVERIFIED"
        return "PERMIT"

    if rule == "stale_restore_authority":
        stale = (
            f["restore_epoch"] != f["capture_epoch"]
            and (f["authority_epoch_at_capture"] != f["current_authority_epoch"] or f["credential_epoch_at_capture"] != f["current_credential_epoch"])
        )
        if stale and f["socket_continuity"] == "preserved" and not f["session_revalidated"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "delta_classification":
        if not f["normalizable"] or not f["enforcement_known"]:
            return "EXPANSION_GATE"
        old = {(_atomic_tuple(x), x["ttl_seconds"]) for x in f["old"]}
        new = {(_atomic_tuple(x), x["ttl_seconds"]) for x in f["new"]}
        if old == new:
            return "PERMIT"
        old_tuples = {x[0] for x in old}
        new_tuples = {x[0] for x in new}
        if new_tuples < old_tuples:
            return "PERMIT"
        return "EXPANSION_GATE"

    if rule == "delegation_actor_loss":
        if f["delegation_mode"] == "delegation" and f["actor_required"] and not f["actor"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "unknown_enforcement":
        if f["enforcement_locus"] == "unknown" or not f["receipt_resolved"]:
            return "UNVERIFIED"
        return f["decision"]

    if rule == "explicit_deny":
        if f["same_atomic_tuple"] and "DENY" in f["matching_effects"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "stale_policy_attachment":
        if f["attachment_policy_epoch"] != f["effective_policy_epoch"] and not f["attachment_revalidated"]:
            return "DENY"
        return "UNVERIFIED"

    if rule == "authority_causation":
        required = [f["trust_root_ref"], f["principal_attestation_ref"], f["grant_ref"], f["decision_ref"], f["receipt_ref"]]
        if f["provenance_strength"] != "decision-bound-native-receipt" or not f["immutable_refs_resolved"] or not all(required):
            return "UNVERIFIED"
        return f["receipt_result"] if f["receipt_result"] in {"DENY", "PERMIT"} else "UNVERIFIED"

    raise AssertionError(f"unknown rule: {rule}")


def test_vector_pack_is_complete_and_single_oracle():
    doc = _load()
    vectors = doc["vectors"]
    assert {v["id"] for v in vectors} == EXPECTED_IDS
    assert len(vectors) == len(EXPECTED_IDS)
    assert all(v["expected"] in ALLOWED_RESULTS for v in vectors)
    assert all(isinstance(v["expected"], str) for v in vectors)


def test_vector_pack_is_deterministically_serializable():
    doc = _load()
    first = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    second = json.dumps(json.loads(first), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert first == second


def test_all_vectors_match_the_deterministic_oracle():
    for vector in _load()["vectors"]:
        assert _oracle(vector) == vector["expected"], vector["id"]


def test_d13_has_both_required_provenance_variants():
    by_id = {v["id"]: v for v in _load()["vectors"]}
    assert by_id["D-13a"]["expected"] == "UNVERIFIED"
    assert by_id["D-13a"]["facts"]["provenance_strength"] == "behavioral-only"
    assert by_id["D-13b"]["expected"] == "DENY"
    assert by_id["D-13b"]["facts"]["provenance_strength"] == "decision-bound-native-receipt"
    for key in ("enforcement_locus", "observer_locus", "policy_epoch", "authority_epoch", "credential_epoch"):
        assert key in by_id["D-13a"]["facts"]
        assert key in by_id["D-13b"]["facts"]


def test_vectors_do_not_embed_secret_material():
    raw = VECTORS.read_text(encoding="utf-8").lower()
    forbidden = ["private_key", "client_secret", "access_token", "refresh_token", "password"]
    assert not any(term in raw for term in forbidden)
