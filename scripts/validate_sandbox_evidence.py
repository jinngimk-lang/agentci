#!/usr/bin/env python3
"""Minimal S0 semantic validator for AgentCI sandbox EvidenceEnvelope.

Design-stage only: this is not a released sandbox certification engine.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import FormatError

CANONICALIZATION = "agentci-json-c14n-v0alpha1"
VERDICT_RULE = "agentci-sandbox-atomic-v0alpha1"
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "sandbox-certification-v0alpha1.schema.json"
TEST_CASE_DIR = ROOT / "examples" / "sandbox" / "testcases"
EVENT_SOURCE_LAYERS = {
    "process": {"process"},
    "file": {"filesystem"},
    "network": {"network"},
    "credential": {"credential"},
    "control-plane": {"control-plane"},
    "policy-delta": {"control-plane"},
    "policy-attachment": {"control-plane"},
    "lifecycle": {"lifecycle"},
}

def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result

def load_evidence_json(raw: str) -> dict[str, Any]:
    document = json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    if not isinstance(document, dict): raise ValueError("evidence root must be a JSON object")
    return document

def canonical_value_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def digest_value(value: Any) -> str: return "sha256:" + hashlib.sha256(canonical_value_bytes(value)).hexdigest()

def canonical_bytes(document: dict[str, Any]) -> bytes:
    candidate = copy.deepcopy(document)
    if isinstance(candidate.get("canonicalization"), dict): candidate["canonicalization"].pop("artifact_digest", None)
    case_id = candidate.get("case_id")
    test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    return canonical_value_bytes({"evidence": candidate, "test_case_digest": digest_value(test_case) if test_case is not None else None})

def artifact_digest(document: dict[str, Any]) -> str: return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()
def policy_history_digest(document: dict[str, Any]) -> str: return digest_value(document.get("policy_history", []))

def authority_binding_projection(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_history": [{"policy_epoch": x.get("policy_epoch"), "authority_epoch": x.get("authority_epoch"), "source_principal_id": x.get("source_principal_id")} for x in document.get("policy_history", [])],
        "policy_attachments": [{"attachment_id": x.get("attachment_id"), "workload_identity": x.get("workload_identity"), "policy_epoch": x.get("policy_epoch"), "policy_digest": x.get("policy_digest"), "state": x.get("state")} for x in document.get("policy_attachments", [])],
        "events": [{"event_id": x.get("event_id"), "authority_epoch": x.get("authority_epoch"), "decision_id": x.get("decision_id"), "receipt_id": x.get("receipt_id"), "workload_identity": x.get("workload_identity"), "attachment_id": x.get("attachment_id")} for x in document.get("events", [])],
    }

def authority_binding_digest(document: dict[str, Any]) -> str: return digest_value(authority_binding_projection(document))
def event_semantic_digest(event: dict[str, Any]) -> str:
    candidate = copy.deepcopy(event); candidate.pop("semantic_digest", None); return digest_value(candidate)

@lru_cache(maxsize=1)
def _schema_validator() -> Draft202012Validator:
    schema = load_evidence_json(SCHEMA_PATH.read_text())
    envelope = {"$schema": schema["$schema"], "$id": schema.get("$id", "") + "#EvidenceEnvelopeValidation", "$defs": schema["$defs"], "$ref": "#/$defs/EvidenceEnvelope"}
    return Draft202012Validator(envelope, format_checker=FormatChecker())

@lru_cache(maxsize=1)
def _test_case_validator() -> Draft202012Validator:
    schema = load_evidence_json(SCHEMA_PATH.read_text())
    test_case = {"$schema": schema["$schema"], "$id": schema.get("$id", "") + "#TestCaseValidation", "$defs": schema["$defs"], "$ref": "#/$defs/TestCase"}
    return Draft202012Validator(test_case, format_checker=FormatChecker())

@lru_cache(maxsize=64)
def _load_test_case(case_id: str) -> dict[str, Any] | None:
    if not isinstance(case_id, str) or not case_id or "/" in case_id or "\\" in case_id or case_id in {".", ".."}: return None
    path = TEST_CASE_DIR / f"{case_id}.json"
    if not path.is_file(): return None
    try: test_case = load_evidence_json(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError): return None
    if list(_test_case_validator().iter_errors(test_case)): return None
    if test_case.get("kind") != "TestCase" or test_case.get("case_id") != case_id: return None
    utility_ids = test_case.get("authorized_utility", [])
    mandatory_ids = set(test_case.get("mandatory_assertions", []))
    if len(set(utility_ids)) != len(utility_ids) or any(x not in mandatory_ids for x in utility_ids): return None
    return test_case

def _source_suitable_for_event(test_case: dict[str, Any], source: dict[str, Any], event_type: Any) -> bool:
    source_id = source.get("source_id")
    if source_id not in set(test_case.get("mandatory_telemetry_sources", [])): return False
    required_layers = {test_case.get("capability_domain")} if event_type == "utility" else EVENT_SOURCE_LAYERS.get(event_type)
    return required_layers is None or source.get("layer") in required_layers

def _event_matches_canonical_probe(test_case: dict[str, Any], assertion_id: Any, event: dict[str, Any]) -> bool:
    expected_channel = test_case.get("probe", {}).get("network_channel")
    if test_case.get("capability_domain") != "network" or expected_channel is None:
        return True
    if assertion_id in set(test_case.get("authorized_utility", [])):
        return True
    return event.get("event_type") == "network" and event.get("channel") == expected_channel

def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str): return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None

def _format_fields_valid(document: dict[str, Any]) -> bool:
    checker = FormatChecker()
    values = [x.get("effective_at_utc") for x in document.get("policy_history", [])] + [x.get("occurred_at_utc") for x in document.get("events", [])]
    for value in values:
        try: checker.check(value, "date-time")
        except FormatError: return False
    return True

def _duplicates(values: list[Any]) -> set[Any]: return {v for v in values if v is not None and values.count(v) > 1}

def _residual_errors(document: dict[str, Any]) -> list[str]:
    post, errors = document.get("post_conditions", {}), []
    if post.get("descendants") == "residual": errors.append("residual descendants violate PASS")
    if post.get("filesystem_residue") == "residual": errors.append("residual filesystem state violate PASS")
    if post.get("sockets") == "residual": errors.append("residual sockets violate PASS")
    return errors

def _authority_expansion_errors(document: dict[str, Any]) -> list[str]:
    """Fail closed until expansion can bind to the canonical external AuthorityBundle.

    EvidenceEnvelope currently carries policy/source principal and optional
    decision/receipt reference strings, but it does not embed or uniquely bind
    the PrincipalAttestation -> CapabilityGrant -> Decision ->
    EnforcementReceipt graph from the canonical authority module. Therefore an
    expansion/lateral/unknown delta cannot be proven externally authorized from
    envelope-local self-consistency alone. Treat it as UNVERIFIED rather than
    manufacturing authority from a workload name or opaque IDs.
    """
    gated = {"expansion", "lateral", "unknown"}
    errors = []
    for policy in document.get("policy_history", []):
        delta_class = policy.get("delta_class")
        if delta_class in gated:
            errors.append(
                f"privilege {delta_class} requires external authenticated authority evidence; "
                "EvidenceEnvelope source/decision/receipt references alone are insufficient"
            )
    return errors

def _event_not_after(provenance: dict[str, Any], event: dict[str, Any]) -> bool:
    pmono, emono = provenance.get("monotonic_ns"), event.get("monotonic_ns")
    ptime, etime = _parse_datetime(provenance.get("occurred_at_utc")), _parse_datetime(event.get("occurred_at_utc"))
    return isinstance(pmono, int) and isinstance(emono, int) and pmono <= emono and ptime is not None and etime is not None and ptime <= etime

def _evidence_errors(document: dict[str, Any]) -> list[str]:
    errors = []
    if list(_schema_validator().iter_errors(document)) or not _format_fields_valid(document): errors.append("schema validation failed")
    if document.get("apiVersion") != "agentci.dev/sandbox/v0alpha1": errors.append("unexpected apiVersion")
    if document.get("kind") != "EvidenceEnvelope": errors.append("validator only accepts EvidenceEnvelope")
    if document.get("verdict_rule_version") != VERDICT_RULE: errors.append("unexpected verdict rule version")
    c = document.get("canonicalization", {})
    if c.get("algorithm") != CANONICALIZATION: errors.append("unexpected canonicalization algorithm")
    if c.get("artifact_digest") != artifact_digest(document): errors.append("artifact digest mismatch")
    if document.get("policy_history_digest") != policy_history_digest(document): errors.append("policy history digest mismatch")
    if document.get("authority_digest") != authority_binding_digest(document): errors.append("authority digest mismatch")
    errors.extend(_authority_expansion_errors(document))
    case_id = document.get("case_id"); test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    if test_case is None: errors.append(f"case_id {case_id} does not resolve to one canonical TestCase")
    history = document.get("policy_history", []); epochs = [x.get("policy_epoch") for x in history]; dup_epochs = _duplicates(epochs)
    if not epochs or any(x is None for x in epochs): errors.append("policy history must contain concrete epochs")
    for x in sorted(dup_epochs): errors.append(f"duplicate policy_epoch {x}")
    prev_epoch = prev_mono = None
    for item in history:
        epoch, mono = item.get("policy_epoch"), item.get("effective_at_monotonic_ns")
        if isinstance(epoch, int) and isinstance(prev_epoch, int) and epoch < prev_epoch: errors.append("policy history epochs must strictly increase in document order")
        if isinstance(mono, int) and isinstance(prev_mono, int) and mono <= prev_mono: errors.append("policy history monotonic time must strictly increase with epoch")
        if isinstance(epoch, int): prev_epoch = epoch
        if isinstance(mono, int): prev_mono = mono
    history_by_epoch = {x.get("policy_epoch"): x for x in history if isinstance(x.get("policy_epoch"), int) and x.get("policy_epoch") not in dup_epochs}
    telemetry = document.get("telemetry", []); sources = [x.get("source_id") for x in telemetry]; dup_sources = _duplicates(sources)
    for x in sorted(dup_sources): errors.append(f"duplicate telemetry source_id {x}")
    telemetry_by_source = {x.get("source_id"): x for x in telemetry if x.get("source_id") is not None and x.get("source_id") not in dup_sources}
    events = document.get("events", []); event_values = [x.get("event_id") for x in events]; dup_events = _duplicates(event_values)
    for x in sorted(dup_events): errors.append(f"duplicate event_id {x}")
    event_ids = {x for x in event_values if x is not None}; events_by_id = {x.get("event_id"): x for x in events if x.get("event_id") is not None and x.get("event_id") not in dup_events}
    event_sources = {x.get("source_id") for x in events}
    for source in telemetry:
        if source.get("coverage") == "mandatory" and source.get("source_id") not in event_sources: errors.append(f"mandatory telemetry source {source.get('source_id')} has no events")
    for event in events:
        eid, sid = event.get("event_id"), event.get("source_id")
        if sid not in telemetry_by_source and sid not in dup_sources: errors.append(f"event {eid} references undeclared telemetry source {sid}")
        policy = history_by_epoch.get(event.get("policy_epoch"))
        if policy is None: errors.append(f"event {eid} references unknown policy epoch")
        else:
            if event.get("authority_epoch") != policy.get("authority_epoch"): errors.append(f"event {eid} authority epoch does not match policy epoch")
            if isinstance(event.get("monotonic_ns"), int) and isinstance(policy.get("effective_at_monotonic_ns"), int) and event["monotonic_ns"] < policy["effective_at_monotonic_ns"]: errors.append(f"event {eid} monotonic time precedes effective policy epoch")
            et, pt = _parse_datetime(event.get("occurred_at_utc")), _parse_datetime(policy.get("effective_at_utc"))
            if et is not None and pt is not None and et < pt: errors.append(f"event {eid} wall-clock time precedes effective policy epoch")
        if event.get("semantic_digest") != event_semantic_digest(event): errors.append(f"event {eid} semantic digest mismatch")
    attachment_events_by_digest: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("event_type") == "policy-attachment" and event.get("semantic_digest") == event_semantic_digest(event): attachment_events_by_digest.setdefault(event.get("semantic_digest"), []).append(event)
    attachments = document.get("policy_attachments", []); attachment_ids = [x.get("attachment_id") for x in attachments]; dup_attachments = _duplicates(attachment_ids)
    for x in sorted(dup_attachments): errors.append(f"duplicate attachment_id {x}")
    for attachment in attachments:
        aid, policy = attachment.get("attachment_id"), history_by_epoch.get(attachment.get("policy_epoch"))
        if policy is None: errors.append(f"attachment {aid} references unknown policy epoch"); continue
        if attachment.get("state") == "effective":
            if attachment.get("policy_digest") != policy.get("policy_digest"): errors.append(f"effective attachment {aid} policy digest does not match policy epoch")
            if len(attachment_events_by_digest.get(attachment.get("evidence_digest"), [])) != 1: errors.append(f"effective attachment {aid} evidence digest does not bind exactly one policy-attachment event")
    assertions = document.get("assertions", []); assertion_ids = [x.get("assertion_id") for x in assertions]
    duplicate_assertions = _duplicates(assertion_ids)
    for x in sorted(duplicate_assertions): errors.append(f"duplicate assertion_id {x}")
    if test_case is not None:
        canonical_mandatory = set(test_case.get("mandatory_assertions", []))
        present_mandatory = {
            assertion.get("assertion_id")
            for assertion in assertions
            if assertion.get("mandatory") and assertion.get("assertion_id") not in duplicate_assertions
        }
        for assertion_id in sorted(canonical_mandatory - present_mandatory):
            errors.append(f"canonical mandatory assertion {assertion_id} is missing from EvidenceEnvelope")
    for assertion in assertions:
        assertion_id, evidence_ids = assertion.get("assertion_id"), assertion.get("evidence_event_ids", []); mandatory_pass = assertion.get("mandatory") and assertion.get("state") == "PASS"
        if mandatory_pass and not evidence_ids: errors.append(f"mandatory PASS assertion {assertion_id} requires event evidence")
        if mandatory_pass and test_case is not None and assertion_id not in set(test_case.get("mandatory_assertions", [])): errors.append(f"mandatory PASS assertion {assertion_id} is not bound by canonical TestCase")
        for event_id in evidence_ids:
            if event_id not in event_ids: errors.append(f"assertion {assertion_id} references missing evidence event {event_id}"); continue
            if event_id in dup_events: errors.append(f"assertion {assertion_id} evidence event {event_id} does not resolve uniquely"); continue
            if mandatory_pass:
                event = events_by_id[event_id]; source = telemetry_by_source.get(event.get("source_id"))
                if source is None: errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} references undeclared telemetry source {event.get('source_id')}")
                elif source.get("coverage") != "mandatory" or source.get("health") != "healthy": errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires a healthy mandatory telemetry source")
                elif test_case is None or not _source_suitable_for_event(test_case, source, event.get("event_type")): errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} fails canonical TestCase source suitability")
                elif not _event_matches_canonical_probe(test_case, assertion_id, event): errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} does not match canonical probe channel")
                epoch, workload, aid = event.get("policy_epoch"), event.get("workload_identity"), event.get("attachment_id")
                matching = [x for x in attachments if x.get("state") == "effective" and x.get("policy_epoch") == epoch and x.get("workload_identity") == workload and x.get("attachment_id") == aid and x.get("attachment_id") not in dup_attachments]
                if not workload or not aid or len(matching) != 1: errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires exactly one effective attachment with matching workload identity for policy epoch {epoch}")
                else:
                    attachment = matching[0]; provenance = attachment_events_by_digest.get(attachment.get("evidence_digest"), [])
                    if len(provenance) != 1: errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires exactly one attachment effectiveness provenance event")
                    else:
                        provenance_event = provenance[0]
                        if provenance_event.get("attachment_id") != attachment.get("attachment_id") or provenance_event.get("workload_identity") != attachment.get("workload_identity") or provenance_event.get("policy_epoch") != attachment.get("policy_epoch"):
                            errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires matching attachment provenance identity")
                        else:
                            provenance_source_id = provenance_event.get("source_id"); provenance_source = telemetry_by_source.get(provenance_source_id)
                            if provenance_source_id in dup_sources or provenance_source is None: errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance from exactly one declared telemetry source")
                            elif provenance_source.get("coverage") != "mandatory" or provenance_source.get("health") != "healthy": errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance from a healthy mandatory telemetry source")
                            elif test_case is None or not _source_suitable_for_event(test_case, provenance_source, provenance_event.get("event_type")): errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} attachment provenance fails canonical TestCase source suitability")
                            elif not _event_not_after(provenance_event, event): errors.append(f"mandatory PASS assertion {assertion_id} evidence event {event_id} requires attachment effectiveness provenance at or before the PASS event on both clocks")
    return errors

def _is_credible_pass(assertion: dict[str, Any]) -> bool: return assertion.get("state") == "PASS" and bool(assertion.get("evidence_event_ids"))

def _authorized_utility_complete(document: dict[str, Any]) -> bool:
    case_id = document.get("case_id"); test_case = _load_test_case(case_id) if isinstance(case_id, str) else None
    if test_case is None: return False
    assertions = document.get("assertions", []); duplicates = _duplicates([x.get("assertion_id") for x in assertions])
    by_id = {x.get("assertion_id"): x for x in assertions if x.get("assertion_id") is not None and x.get("assertion_id") not in duplicates}
    events = document.get("events", []); duplicate_event_ids = _duplicates([x.get("event_id") for x in events])
    events_by_id = {x.get("event_id"): x for x in events if x.get("event_id") is not None and x.get("event_id") not in duplicate_event_ids}
    for utility_id in test_case.get("authorized_utility", []):
        assertion = by_id.get(utility_id)
        if assertion is None or not assertion.get("mandatory") or not _is_credible_pass(assertion): return False
        utility_events = [events_by_id.get(event_id) for event_id in assertion.get("evidence_event_ids", [])]
        if not any(event is not None and event.get("event_type") == "utility" for event in utility_events): return False
    return True

def expected_verdict(document: dict[str, Any]) -> str:
    if not document.get("probe_executed", False) or document.get("execution_status") != "completed": return "UNVERIFIED"
    if _evidence_errors(document): return "UNVERIFIED"
    if _residual_errors(document): return "FAIL"
    if not any(x.get("state") == "effective" for x in document.get("policy_attachments", [])): return "UNVERIFIED"
    mandatory_telemetry = [x for x in document.get("telemetry", []) if x.get("coverage") == "mandatory"]
    if not mandatory_telemetry or any(x.get("health") != "healthy" for x in mandatory_telemetry): return "UNVERIFIED"
    assertions = document.get("assertions", [])
    if any(x.get("state") == "FAIL" for x in assertions): return "FAIL"
    if not _authorized_utility_complete(document): return "UNVERIFIED"
    mandatory = [x for x in assertions if x.get("mandatory")]
    if not mandatory: return "UNVERIFIED"
    incomplete = [x for x in mandatory if x.get("state") in {"UNVERIFIED", "NOT-APPLICABLE"} or (x.get("state") == "PASS" and not x.get("evidence_event_ids"))]
    if incomplete: return "PARTIAL" if any(_is_credible_pass(x) for x in mandatory) else "UNVERIFIED"
    return "PASS" if all(_is_credible_pass(x) for x in mandatory) else "UNVERIFIED"

def validate(document: dict[str, Any]) -> list[str]:
    errors = _evidence_errors(document); errors.extend(_residual_errors(document)); verdict = expected_verdict(document)
    if document.get("verdict") != verdict: errors.append(f"verdict mismatch: recorded={document.get('verdict')} expected={verdict}")
    if document.get("verdict") == "PASS":
        mandatory = [x for x in document.get("telemetry", []) if x.get("coverage") == "mandatory"]
        if not mandatory: errors.append("PASS requires mandatory telemetry evidence")
        elif any(x.get("health") != "healthy" for x in mandatory): errors.append("PASS requires every mandatory telemetry collector to be healthy")
        if not _authorized_utility_complete(document): errors.append("PASS requires every canonical authorized utility assertion to have credible evidence")
        if any(x.get("mandatory") and x.get("state") == "NOT-APPLICABLE" for x in document.get("assertions", [])): errors.append("PASS cannot hide a mandatory assertion as not-applicable")
        if any(x.get("state") == "FAIL" for x in document.get("assertions", [])): errors.append("PASS contains a failed assertion")
        if not any(x.get("state") == "effective" for x in document.get("policy_attachments", [])): errors.append("PASS requires effective policy attachment evidence")
        unverified = [k for k, v in document.get("post_conditions", {}).items() if v == "unverified"]
        if unverified: errors.append("PASS contains unverified post-conditions: " + ", ".join(unverified))
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("path", type=Path); parser.add_argument("--print-digest", action="store_true"); args = parser.parse_args()
    try: document = load_evidence_json(args.path.read_text())
    except (json.JSONDecodeError, ValueError) as exc: print(f"ERROR: invalid raw evidence JSON: {exc}"); return 1
    if args.print_digest: print(artifact_digest(document))
    errors = validate(document)
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    print(f"OK: {document['run_id']} verdict={document['verdict']}"); return 0
if __name__ == "__main__": raise SystemExit(main())
