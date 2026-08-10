from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an eval suite is invalid."""


@dataclass(frozen=True)
class Actual:
    success: bool
    latency_ms: float | None = None
    cost_usd: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class Expected:
    success: bool
    max_latency_ms: float | None = None
    max_cost_usd: float | None = None


@dataclass(frozen=True)
class LocalCommandTarget:
    command: tuple[str, ...]
    timeout_seconds: float


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: str | None
    actual: Actual | None
    expected: Expected


@dataclass(frozen=True)
class EvalSuite:
    name: str
    cases: list[EvalCase]
    target: LocalCommandTarget | None = None


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
    return float(value)


def _load_target(root: dict[str, Any]) -> LocalCommandTarget | None:
    raw = root.get("target")
    if raw is None:
        return None
    mapping = _require_mapping(raw, "target")
    if mapping.get("type") != "local-command":
        raise ConfigError("target.type must be 'local-command'")
    command = mapping.get("command")
    if not isinstance(command, list):
        raise ConfigError("target.command must be a list of argv strings")
    if not command or any(not isinstance(arg, str) or not arg for arg in command):
        raise ConfigError("target.command must be a non-empty list of non-empty strings")
    timeout_seconds = mapping.get("timeout_seconds", 10)
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
        raise ConfigError("target.timeout_seconds must be a number")
    timeout_seconds = float(timeout_seconds)
    if not math.isfinite(timeout_seconds):
        raise ConfigError("target.timeout_seconds must be finite")
    if timeout_seconds <= 0:
        raise ConfigError("target.timeout_seconds must be > 0")
    return LocalCommandTarget(tuple(command), timeout_seconds)


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
    name = root.get("suite")
    if not isinstance(name, str) or not name.strip():
        raise ConfigError("suite must be a non-empty string")
    target = _load_target(root)
    raw_cases = root.get("cases")
    if not isinstance(raw_cases, list):
        raise ConfigError("cases must be a list")

    cases: list[EvalCase] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_cases):
        mapping = _require_mapping(item, f"cases[{index}]")
        case_id = mapping.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ConfigError(f"cases[{index}].id must be a non-empty string")
        if case_id in seen:
            raise ConfigError(f"duplicate case id: {case_id}")
        seen.add(case_id)

        actual: Actual | None
        if target is None:
            actual_raw = _require_mapping(mapping.get("actual"), f"cases[{index}].actual")
            actual = Actual(
                success=_require_bool(actual_raw, "success", f"cases[{index}].actual"),
                latency_ms=_optional_number(actual_raw, "latency_ms", f"cases[{index}].actual"),
                cost_usd=_optional_number(actual_raw, "cost_usd", f"cases[{index}].actual"),
            )
        else:
            if "actual" in mapping:
                raise ConfigError(f"cases[{index}].actual is not allowed when target is configured")
            actual = None

        expected_raw = _require_mapping(mapping.get("expected"), f"cases[{index}].expected")
        expected = Expected(
            success=_require_bool(expected_raw, "success", f"cases[{index}].expected"),
            max_latency_ms=_optional_number(expected_raw, "max_latency_ms", f"cases[{index}].expected"),
            max_cost_usd=_optional_number(expected_raw, "max_cost_usd", f"cases[{index}].expected"),
        )
        input_value = mapping.get("input")
        if input_value is not None and not isinstance(input_value, str):
            raise ConfigError(f"cases[{index}].input must be a string when present")
        cases.append(EvalCase(case_id, input_value, actual, expected))
    return EvalSuite(name=name, cases=cases, target=target)
