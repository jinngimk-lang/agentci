from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import ConfigError
from .runner import run_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='agentci')
    subparsers = parser.add_subparsers(dest='command', required=True)
    test_parser = subparsers.add_parser('test', help='run a deterministic eval suite')
    test_parser.add_argument('path', type=Path)
    test_parser.add_argument('--output-dir', type=Path, default=Path('artifacts'))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == 'test':
            result = run_suite(args.path, args.output_dir)
            print(
                f'AgentCI {result.suite}: {result.passed_cases}/{result.total_cases} passed '
                f'({result.success_rate:.1%})'
            )
            print(f'Report: {args.output_dir / "agentci-report.md"}')
            return 0 if result.failed_cases == 0 else 1
    except ConfigError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
