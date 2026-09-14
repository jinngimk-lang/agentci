from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import yaml


class ArtifactError(ValueError):
    """Raised when canonical growth artifact inputs are malformed."""


@dataclass(frozen=True)
class ValidationResult:
    eligible: bool
    reasons: list[str]
    facts: dict[str, Any]


def _number(facts: dict[str, Any], key: str) -> float:
    value = facts.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ArtifactError(f"facts.{key} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ArtifactError(f"facts.{key} must be finite")
    return number


def _integer(facts: dict[str, Any], key: str) -> int:
    value = facts.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArtifactError(f"facts.{key} must be an integer")
    return value


def _boolean(facts: dict[str, Any], key: str) -> bool:
    value = facts.get(key)
    if not isinstance(value, bool):
        raise ArtifactError(f"facts.{key} must be a boolean")
    return value


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactError(f"cannot read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"invalid JSON in {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise ArtifactError(f"{label} must contain a JSON object")
    return data


def load_rules(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactError(f"cannot read growth rules: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ArtifactError(f"invalid growth rules: {exc}") from exc
    if not isinstance(data, dict):
        raise ArtifactError("growth rules must be an object")
    return data


def _load_canonical_artifact(artifact_dir: Path) -> dict[str, Any]:
    if not artifact_dir.is_dir():
        raise ArtifactError(f"artifact directory does not exist: {artifact_dir}")
    for name in ("facts.json", "evidence.md", "sources.json"):
        if not (artifact_dir / name).is_file():
            raise ArtifactError(f"missing canonical file: {name}")
    facts = _load_json_object(artifact_dir / "facts.json", "facts.json")
    _load_json_object(artifact_dir / "sources.json", "sources.json")
    for key in ("artifact_id", "category", "title", "public_claims"):
        if key not in facts:
            raise ArtifactError(f"facts.{key} is required")
    if not isinstance(facts["artifact_id"], str) or not facts["artifact_id"].strip():
        raise ArtifactError("facts.artifact_id must be a non-empty string")
    if facts["artifact_id"] != artifact_dir.name:
        raise ArtifactError("facts.artifact_id must match artifact directory name")
    if not isinstance(facts["title"], str) or not facts["title"].strip():
        raise ArtifactError("facts.title must be a non-empty string")
    if not isinstance(facts["public_claims"], list) or not all(isinstance(x, str) for x in facts["public_claims"]):
        raise ArtifactError("facts.public_claims must be a list of strings")
    return facts


def validate_artifact(artifact_dir: Path, rules_path: Path) -> ValidationResult:
    facts = _load_canonical_artifact(Path(artifact_dir))
    rules = load_rules(Path(rules_path))
    category = facts.get("category")
    if not isinstance(category, str) or category not in rules:
        raise ArtifactError(f"unsupported facts.category: {category!r}")
    policy = rules[category]
    if not isinstance(policy, dict):
        raise ArtifactError(f"rules.{category} must be an object")

    reasons: list[str] = []
    if category == "benchmark":
        runs = _integer(facts, "runs")
        if runs < int(policy["min_runs"]):
            reasons.append(f"benchmark requires at least {policy['min_runs']} runs; got {runs}")
        if bool(policy.get("requires_reproducible")) and not _boolean(facts, "reproducible"):
            reasons.append("benchmark must be reproducible")

    elif category == "performance":
        improvement = _number(facts, "improvement_percent")
        samples = _integer(facts, "samples")
        if improvement < float(policy["min_improvement_percent"]):
            reasons.append(
                f"performance improvement must be at least {policy['min_improvement_percent']}%; got {improvement:g}%"
            )
        if samples < int(policy["min_samples"]):
            reasons.append(f"performance evidence requires at least {policy['min_samples']} samples; got {samples}")

    elif category == "security":
        severity = facts.get("severity")
        allowed = policy.get("allowed_severity", [])
        if severity not in allowed:
            reasons.append(f"security severity must be one of {allowed}; got {severity!r}")
        if bool(policy.get("requires_reproducible")) and not _boolean(facts, "reproducible"):
            reasons.append("security finding must be reproducible")
        if bool(policy.get("requires_disclosure_ready")) and not _boolean(facts, "disclosure_ready"):
            reasons.append("security finding is not disclosure ready")

    elif category == "integration":
        checks = (("demo", "requires_demo"), ("tests", "requires_tests"), ("docs", "requires_docs"))
        for fact_key, policy_key in checks:
            if bool(policy.get(policy_key)) and not _boolean(facts, fact_key):
                reasons.append(f"integration requires {fact_key}=true")

    elif category == "release":
        changes = _integer(facts, "meaningful_changes")
        major = _boolean(facts, "major_capability")
        min_changes = int(policy["min_meaningful_changes"])
        allow_major = bool(policy.get("allow_major_capability"))
        if changes < min_changes and not (allow_major and major):
            reasons.append(
                f"release requires at least {min_changes} meaningful changes or major_capability=true"
            )

    elif category == "dataset":
        examples = _integer(facts, "examples")
        notes = _boolean(facts, "reproducible_notes")
        if examples < int(policy["min_examples"]):
            reasons.append(f"dataset requires at least {policy['min_examples']} examples; got {examples}")
        if bool(policy.get("requires_reproducible_notes")) and not notes:
            reasons.append("dataset requires reproducible validation/generation notes")

    return ValidationResult(eligible=not reasons, reasons=reasons, facts=facts)
