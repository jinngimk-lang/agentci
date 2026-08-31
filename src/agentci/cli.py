from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import ConfigError
from .runner import run_suite
from .sandbox import collect_readiness_report
from .showcase import load_showcase_catalog


_STARTER_CONFIG = """suite: starter
cases:
  - id: first-check
    input: "Verify a deterministic result"
    actual:
      success: true
      latency_ms: 100
      cost_usd: 0.0
    expected:
      success: true
      max_latency_ms: 1000
      max_cost_usd: 0.01
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='agentci')
    subparsers = parser.add_subparsers(dest='command', required=True)
    init_parser = subparsers.add_parser('init', help='create a minimal runnable AgentCI eval config')
    init_parser.add_argument('path', nargs='?', type=Path, default=Path('agentci.yaml'))
    test_parser = subparsers.add_parser('test', help='run a deterministic eval suite')
    test_parser.add_argument('path', type=Path)
    test_parser.add_argument('--output-dir', type=Path, default=Path('artifacts'))
    sandbox_parser = subparsers.add_parser('sandbox', help='inspect and verify sandbox evidence')
    sandbox_subparsers = sandbox_parser.add_subparsers(dest='sandbox_command', required=True)
    doctor_parser = sandbox_subparsers.add_parser('doctor', help='run safe local sandbox readiness probes')
    doctor_parser.add_argument('--json', action='store_true', help='emit a machine-readable readiness report')
    verify_parser = sandbox_subparsers.add_parser('verify', help='validate one canonical sandbox EvidenceEnvelope')
    verify_parser.add_argument('path', type=Path)
    verify_parser.add_argument('--json', action='store_true', help='emit a machine-readable verification result')
    verify_parser.add_argument('--print-digest', action='store_true', help='include the canonical artifact digest')
    verify_parser.add_argument(
        '--receipt',
        type=Path,
        help='write an opt-in strict content-addressed verification receipt manifest',
    )
    verify_parser.add_argument(
        '--receipt-bundle',
        type=Path,
        help='read the exact signed observer and cleanup sidecar directory for --receipt',
    )
    showcase_parser = subparsers.add_parser('showcase', help='discover truth-bounded AgentCI cases')
    showcase_subparsers = showcase_parser.add_subparsers(dest='showcase_command', required=True)
    showcase_list_parser = showcase_subparsers.add_parser('list', help='list canonical showcase entries')
    showcase_list_parser.add_argument('--json', action='store_true', help='emit the machine-readable showcase catalog')
    showcase_show_parser = showcase_subparsers.add_parser('show', help='show one canonical showcase entry')
    showcase_show_parser.add_argument('showcase_id')
    showcase_show_parser.add_argument('--json', action='store_true', help='emit the machine-readable showcase entry')
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == 'init':
            with args.path.open('x', encoding='utf-8') as starter_file:
                starter_file.write(_STARTER_CONFIG)
            print(f'Created: {args.path}')
            print(f'Next: agentci test {args.path}')
            return 0
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
        if args.command == 'sandbox' and args.sandbox_command == 'verify':
            if args.receipt_bundle is not None and args.receipt is None:
                parser.error('--receipt-bundle requires --receipt')
            # Keep repository-only verifier dependencies off legacy `test` and
            # readiness paths until the wheel-safe resource gate is satisfied.
            from .sandbox.verification import verify_evidence_file

            result = verify_evidence_file(
                args.path,
                include_digest=args.print_digest,
                receipt_path=args.receipt,
                receipt_bundle_path=args.receipt_bundle,
            )
            if args.json:
                print(json.dumps(result.to_dict(), sort_keys=True))
            else:
                _print_sandbox_verification(result)
            return 0 if result.valid and (args.receipt is None or result.receipt_written) else 1
        if args.command == 'showcase' and args.showcase_command == 'list':
            catalog = load_showcase_catalog()
            if args.json:
                print(json.dumps(catalog, sort_keys=True))
            else:
                _print_showcase_list(catalog)
            return 0
        if args.command == 'showcase' and args.showcase_command == 'show':
            catalog = load_showcase_catalog()
            item = next((candidate for candidate in catalog['items'] if candidate['id'] == args.showcase_id), None)
            if item is None:
                print(f'error: unknown showcase id: {args.showcase_id}', file=sys.stderr)
                return 2
            if args.json:
                print(json.dumps(item, sort_keys=True))
            else:
                _print_showcase_item(item)
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


def _print_sandbox_verification(result) -> None:
    print(f'Evidence envelope: {"valid" if result.valid else "invalid"}')
    print(f'Run: {result.run_id or "unknown"}')
    print(f'Recorded verdict: {result.recorded_verdict or "unknown"}')
    print(f'Expected verdict: {result.expected_verdict}')
    if result.artifact_digest:
        print(f'Artifact digest: {result.artifact_digest}')
    for error in result.errors:
        print(f'- ERROR: {error}')
    print('Truth boundary: valid evidence is not a security certification; inspect the recorded verdict and limitations.')


def _print_showcase_list(catalog) -> None:
    print('AgentCI showcase:')
    for item in catalog['items']:
        print(f"- {item['id']} [{item['evidence_maturity']}] {item['title']}")
        print(f"  command: {' '.join(item['released_command'])}")
        print(f"  boundary: {item['claim_boundary']}")
    print('Truth boundary: showcase metadata does not certify any sandbox backend.')


def _print_showcase_item(item) -> None:
    print(f"{item['id']} [{item['evidence_maturity']}]")
    print(item['title'])
    print(f"Semantic class: {item['semantic_class']}")
    print(f"Command: {' '.join(item['released_command'])}")
    if item.get('repository_path'):
        print(f"Repository path: {item['repository_path']}")
    print(f"Claim boundary: {item['claim_boundary']}")
    print(f"Certification claim: {str(item['certification_claim']).lower()}")


if __name__ == '__main__':
    raise SystemExit(main())
