from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.growth_policy import ArtifactError, validate_artifact


DEFAULT_RULES = Path('.company/growth/rules.yaml')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate a canonical growth artifact')
    parser.add_argument('artifact_dir', type=Path)
    parser.add_argument('--rules', type=Path, default=DEFAULT_RULES)
    args = parser.parse_args(argv)
    try:
        result = validate_artifact(args.artifact_dir, args.rules)
    except ArtifactError as exc:
        print(f'INVALID: {exc}')
        return 2
    if result.eligible:
        print(f'ELIGIBLE: {result.facts["artifact_id"]}')
        return 0
    print(f'INELIGIBLE: {result.facts["artifact_id"]}')
    for reason in result.reasons:
        print(f'- {reason}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
