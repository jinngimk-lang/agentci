from __future__ import annotations

import json
import subprocess

import pytest


def test_public_parser_and_cli_json_contract(monkeypatch, capsys):
    """Breaks if the public doctor command or its JSON transport disappears."""
    from agentci import cli

    class Report:
        def to_dict(self):
            return {
                'report_version': 'v0alpha1',
                'agentci_version': '0.1.0',
                'platform': {'system': 'Windows', 'release': '11', 'machine': 'AMD64', 'python': '3.11'},
                'state': 'ready',
                'active_backend': 'docker',
                'candidates': [],
                'limitations': ['Readiness is not isolation proof.'],
            }

    monkeypatch.setattr(cli, 'collect_readiness_report', lambda: Report())
    assert cli.main(['sandbox', 'doctor', '--json']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['report_version'] == 'v0alpha1'
    assert payload['active_backend'] == 'docker'
    assert payload['limitations'] == ['Readiness is not isolation proof.']
    assert cli.build_parser().parse_args(['sandbox', 'doctor', '--json']).json is True


def test_broken_preferred_candidate_falls_back_to_healthy_candidate():
    """Breaks if a resolved-but-broken preferred executable blocks a healthy fallback."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    candidates = (
        Candidate('docker', 'container', 'docker', ('docker', '--version')),
        Candidate('podman', 'container', 'podman', ('podman', '--version')),
    )

    def resolve(name):
        return f'C:/tools/{name}.exe'

    def run(argv, **kwargs):
        if argv[0] == 'docker':
            raise OSError('stale launcher')
        return subprocess.CompletedProcess(argv, 0, stdout='podman 5.0', stderr='')

    report = collect_readiness_report(candidates=candidates, resolve=resolve, run=run)
    assert report.active_backend == 'podman'
    assert [(candidate.id, candidate.state) for candidate in report.candidates] == [
        ('docker', 'broken'),
        ('podman', 'healthy'),
    ]


def test_timeout_and_unexpected_probe_errors_do_not_abort_fallback():
    """Breaks if one timeout/error stops the report before later candidates are probed."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    candidates = (
        Candidate('docker', 'container', 'docker', ('docker', '--version')),
        Candidate('podman', 'container', 'podman', ('podman', '--version')),
        Candidate('bubblewrap', 'os-sandbox', 'bwrap', ('bwrap', '--version')),
    )

    def run(argv, **kwargs):
        if argv[0] == 'docker':
            raise subprocess.TimeoutExpired(argv, 2)
        if argv[0] == 'podman':
            raise RuntimeError('unexpected')
        return subprocess.CompletedProcess(argv, 0, stdout='bwrap 1.0', stderr='')

    report = collect_readiness_report(candidates=candidates, resolve=lambda name: name, run=run)
    assert [candidate.state for candidate in report.candidates] == ['probe-timeout', 'probe-error', 'healthy']
    assert report.active_backend == 'bubblewrap'


def test_all_missing_or_unverified_candidates_have_no_active_backend():
    """Breaks if discovery alone or an unverified candidate is treated as ready."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    report = collect_readiness_report(
        candidates=(
            Candidate('docker', 'container', 'docker', ('docker', '--version')),
            Candidate('windows-sandbox', 'os-sandbox', None, None, unverified_reason='safe executable handshake unavailable'),
        ),
        resolve=lambda name: None,
        run=lambda argv, **kwargs: pytest.fail('missing candidate must not be probed'),
    )
    assert report.state == 'not-ready'
    assert report.active_backend is None
    assert [candidate.state for candidate in report.candidates] == ['missing', 'unverified']


def test_report_redacts_local_details_and_states_truth_boundary():
    """Breaks if reports disclose local paths/output or omit their readiness limitation."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    report = collect_readiness_report(
        candidates=(Candidate('docker', 'container', 'docker', ('docker', '--version')),),
        resolve=lambda name: 'C:/Users/alice/.secret/bin/docker.exe',
        run=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, stdout='token=secret-value', stderr=''),
        platform_facts=('Windows', '11', 'AMD64', '3.11.9'),
    ).to_dict()
    encoded = json.dumps(report)
    assert report['candidates'][0]['executable'] == 'docker.exe'
    assert report['candidates'][0]['probe_method'] == 'docker --version'
    assert 'alice' not in encoded
    assert 'secret-value' not in encoded
    assert 'current working directory' not in encoded
    assert 'not isolation proof' in ' '.join(report['limitations']).lower()
    assert 'not security certification' in ' '.join(report['limitations']).lower()


def test_present_but_unconfigured_wsl_is_not_ready():
    """Breaks if a Windows Store/stub WSL entrypoint is treated as a usable backend."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    report = collect_readiness_report(
        candidates=(Candidate('wsl', 'os-sandbox', 'wsl.exe', ('wsl.exe', '--status'), requires_success=True),),
        resolve=lambda name: 'C:/Windows/System32/wsl.exe',
        run=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 1, stdout='', stderr='WSL is not configured'),
    )
    candidate = report.candidates[0]
    assert candidate.state == 'broken'
    assert report.active_backend is None
