from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import ConfigError
from .runner import run_suite
from .sandbox import collect_readiness_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='agentci')
    subparsers = parser.add_subparsers(dest='command', required=True)
    test_parser = subparsers.add_parser('test', help='run a deterministic eval suite')
    test_parser.add_argument('path', type=Path)
    test_parser.add_argument('--output-dir', type=Path, default=Path('artifacts'))
    sandbox_parser = subparsers.add_parser('sandbox', help='inspect local sandbox backend readiness')
    sandbox_subparsers = sandbox_parser.add_subparsers(dest='sandbox_command', required=True)
    doctor_parser = sandbox_subparsers.add_parser('doctor', help='run safe local sandbox readiness probes')
    doctor_parser.add_argument('--json', action='store_true', help='emit a machine-readable readiness report')
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
        if args.command == 'sandbox' and args.sandbox_command == 'doctor':
            report = collect_readiness_report()
            if args.json:
                print(json.dumps(report.to_dict(), sort_keys=True))
            else:
                _print_sandbox_doctor(report)
            return 0
    except ConfigError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    return 2


def _print_sandbox_doctor(report) -> None:
    print(f'Sandbox readiness: {report.state}')
    print(f'Active backend: {report.active_backend or "none"}')
    for candidate in report.candidates:
        reason = f' ({candidate.reason})' if candidate.reason else ''
        print(f'- {candidate.id}: {candidate.state}{reason}')
    print('Truth boundary: readiness is not backend execution, isolation proof, or security certification.')


if __name__ == '__main__':
    raise SystemExit(main())
