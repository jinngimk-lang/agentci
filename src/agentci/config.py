from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an eval suite is invalid."""


# Keys accepted at each level. Anything else is a typo, and a typo used to be
# dropped silently: writing `expected.max_latency` instead of `max_latency_ms`
# meant the threshold was ignored entirely, so a case whose actual latency was
# 9000 ms passed against an intended 100 ms limit and the suite exited 0. A tool
# that exists to reject false PASS cannot afford that, so unknown keys are now a
# hard error naming the offending key and its closest valid spelling.
ROOT_KEYS = frozenset({"suite", "cases"})
CASE_KEYS = frozenset({"id", "input", "actual", "expected"})
ACTUAL_KEYS = frozenset({"success", "latency_ms", "cost_usd"})
EXPECTED_KEYS = frozenset({"success", "max_latency_ms", "max_cost_usd"})


def _closest_match(word: str, candidates: frozenset[str]) -> str | None:
    """Return the candidate most similar to `word`, or None when nothing is close.

    Deliberately dependency-free: difflib is stdlib but this needs only the best
    single guess, and keeping it explicit makes the suggestion behaviour testable.
    """
    best: str | None = None
    best_score = 0.0
    lowered = word.lower()
    for candidate in candidates:
        target = candidate.lower()
        # Cheap similarity: shared character count weighted by length agreement.
        shared = sum(1 for a, b in zip(lowered, target) if a == b)
        if max(len(lowered), len(target)) == 0:
            continue
        score = (shared / max(len(lowered), len(target))) * (min(len(lowered), len(target)) / max(len(lowered), len(target)))
        if score > best_score:
            best_score = score
            best = candidate
    return best if best_score >= 0.6 else None


def _require_known_keys(mapping: dict[str, Any], allowed: frozenset[str], where: str) -> None:
    unknown = [key for key in mapping if key not in allowed]
    if not unknown:
        return
    problems: list[str] = []
    for key in sorted(unknown):
        hint = _closest_match(str(key), allowed)
        if hint:
            problems.append(f"{where}.{key} is not a valid key (did you mean '{hint}'?)")
        else:
            problems.append(f"{where}.{key} is not a valid key")
    valid = ", ".join(sorted(allowed))
    raise ConfigError("; ".join(problems) + f". Valid keys in {where}: {valid}")


@dataclass(frozen=True)
class Actual:
    success: bool
    latency_ms: float | None = None
    cost_usd: float | None = None


@dataclass(frozen=True)
class Expected:
    success: bool
    max_latency_ms: float | None = None
    max_cost_usd: float | None = None


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: str | None
    actual: Actual
    expected: Expected


@dataclass(frozen=True)
class EvalSuite:
    name: str
    cases: list[EvalCase]


def _require_mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{where} must be an object")
    return value


def _require_bool(mapping: dict[str, Any], key: str, where: str) -> bool:
    if key not in mapping or not isinstance(mapping[key], bool):
        raise ConfigError(f"{where}.{key} must be a boolean")
    return mapping[key]


def _optional_number(mapping: dict[str, Any], key: str, where: str) -> float | None:
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{where}.{key} must be a number")
    if value < 0:
        raise ConfigError(f"{where}.{key} must be >= 0")
    return value


def load_suite(path: str | Path) -> EvalSuite:
    source = Path(path)
    if source.suffix.lower() not in {".yaml", ".yml", ".json"}:
        raise ConfigError("unsupported file extension; use .yaml, .yml, or .json")
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read suite: {exc}") from exc
    try:
        raw = json.loads(text) if source.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"invalid suite syntax: {exc}") from exc
    root = _require_mapping(raw, "root")
    _require_known_keys(root, ROOT_KEYS, "root")
    name = root.get("suite")
    if not isinstance(name, str) or not name.strip():
        raise ConfigError("suite must be a non-empty string")
    raw_cases = root.get("cases")
    if not isinstance(raw_cases, list):
        raise ConfigError("cases must be a list")

    cases: list[EvalCase] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_cases):
        mapping = _require_mapping(item, f"cases[{index}]")
        _require_known_keys(mapping, CASE_KEYS, f"cases[{index}]")
        case_id = mapping.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ConfigError(f"cases[{index}].id must be a non-empty string")
        if case_id in seen:
            raise ConfigError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        actual_raw = _require_mapping(mapping.get("actual"), f"cases[{index}].actual")
        expected_raw = _require_mapping(mapping.get("expected"), f"cases[{index}].expected")
        _require_known_keys(actual_raw, ACTUAL_KEYS, f"cases[{index}].actual")
        _require_known_keys(expected_raw, EXPECTED_KEYS, f"cases[{index}].expected")
        actual = Actual(
            success=_require_bool(actual_raw, "success", f"cases[{index}].actual"),
            latency_ms=_optional_number(actual_raw, "latency_ms", f"cases[{index}].actual"),
            cost_usd=_optional_number(actual_raw, "cost_usd", f"cases[{index}].actual"),
        )
        expected = Expected(
            success=_require_bool(expected_raw, "success", f"cases[{index}].expected"),
            max_latency_ms=_optional_number(expected_raw, "max_latency_ms", f"cases[{index}].expected"),
            max_cost_usd=_optional_number(expected_raw, "max_cost_usd", f"cases[{index}].expected"),
        )
        input_value = mapping.get("input")
        if input_value is not None and not isinstance(input_value, str):
            raise ConfigError(f"cases[{index}].input must be a string when present")
        cases.append(EvalCase(case_id, input_value, actual, expected))
    return EvalSuite(name=name, cases=cases)
