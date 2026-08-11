from __future__ import annotations

import json
import os
import subprocess
import threading
import time

import pytest


def test_public_parser_and_cli_json_contract(monkeypatch, capsys):
    """Breaks if required report/candidate facts disappear from public doctor JSON."""
    from agentci import cli
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    candidates = (
        Candidate('docker', 'container', 'docker', ('docker', '--version')),
        Candidate('bubblewrap', 'os-sandbox', 'bwrap', ('bwrap', '--version')),
        Candidate('wsl', 'os-sandbox', 'wsl.exe', ('wsl.exe', '--status')),
        Candidate('windows-sandbox', 'os-sandbox', 'WindowsSandbox.exe', None, unverified_reason='no safe handshake'),
    )

    def resolve(name):
        return {
            'docker': 'C:/tools/docker.exe',
            'wsl.exe': 'C:/Windows/System32/wsl.exe',
            'WindowsSandbox.exe': 'C:/Windows/System32/WindowsSandbox.exe',
        }.get(name)

    def run(argv, **kwargs):
        if argv[0] == 'C:/tools/docker.exe':
            return subprocess.CompletedProcess(argv, 0, stdout='Docker version 27.3.1, build private-token', stderr='')
        return subprocess.CompletedProcess(argv, 1, stdout='', stderr='not configured')

    report = collect_readiness_report(
        candidates=candidates,
        resolve=resolve,
        run=run,
        platform_facts=('Windows', '11', 'AMD64', '3.11.9'),
    )

    monkeypatch.setattr(cli, 'collect_readiness_report', lambda: report)
    assert cli.main(['sandbox', 'doctor', '--json']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {
        'report_version', 'api_version', 'agentci_version', 'platform', 'state', 'active_backend', 'candidates', 'limitations',
    }
    assert payload['report_version'] == payload['api_version'] == 'v0alpha1'
    assert payload['platform'] == {'system': 'Windows', 'release': '11', 'machine': 'AMD64', 'python': '3.11.9'}
    assert payload['state'] == 'ready'
    assert payload['active_backend'] == 'docker'
    assert 'not isolation proof' in ' '.join(payload['limitations']).lower()
    expected_candidate_fields = {
        'id', 'candidate_class', 'executable', 'version', 'probe_method', 'state', 'discovered', 'installed',
        'configured', 'probed', 'readiness', 'reason',
    }
    assert all(set(candidate) == expected_candidate_fields for candidate in payload['candidates'])
    assert payload['candidates'] == [
        {
            'id': 'docker', 'candidate_class': 'container', 'executable': 'docker.exe', 'version': '27.3.1',
            'probe_method': 'docker --version', 'state': 'healthy', 'discovered': True, 'installed': True,
            'configured': None, 'probed': True, 'readiness': 'ready', 'reason': None,
        },
        {
            'id': 'bubblewrap', 'candidate_class': 'os-sandbox', 'executable': None, 'version': None,
            'probe_method': 'bwrap --version', 'state': 'missing', 'discovered': False, 'installed': False,
            'configured': None, 'probed': False, 'readiness': 'not-ready', 'reason': 'Executable was not found on PATH.',
        },
        {
            'id': 'wsl', 'candidate_class': 'os-sandbox', 'executable': 'wsl.exe', 'version': None,
            'probe_method': 'wsl.exe --status', 'state': 'broken', 'discovered': True, 'installed': True,
            'configured': False, 'probed': True, 'readiness': 'not-ready', 'reason': 'Probe exited unsuccessfully.',
        },
        {
            'id': 'windows-sandbox', 'candidate_class': 'os-sandbox', 'executable': 'WindowsSandbox.exe', 'version': None,
            'probe_method': None, 'state': 'unverified', 'discovered': True, 'installed': True,
            'configured': None, 'probed': False, 'readiness': 'unverified', 'reason': 'no safe handshake',
        },
    ]
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
        if argv[0].endswith('docker.exe'):
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
        if argv[0].endswith('docker'):
            raise subprocess.TimeoutExpired(argv, 2)
        if argv[0].endswith('podman'):
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


def test_resolver_failure_isolated_and_resolved_path_is_probed():
    """Breaks if resolver failure aborts later candidates or probes a different executable."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    candidates = (
        Candidate('docker', 'container', 'docker', ('docker', '--version')),
        Candidate('podman', 'container', 'podman', ('podman', '--version')),
    )
    calls = []

    def resolve(name):
        if name == 'docker':
            raise OSError('resolver failure with C:/Users/alice')
        return 'C:/tools/podman.exe'

    def run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout='podman version 5.2.0', stderr='')

    report = collect_readiness_report(candidates=candidates, resolve=resolve, run=run)
    assert report.candidates[0].state == 'probe-error'
    assert report.candidates[0].discovered is False
    assert report.candidates[0].reason == 'Executable discovery failed.'
    assert report.active_backend == 'podman'
    assert calls == [['C:/tools/podman.exe', '--version']]
    assert report.candidates[1].executable == 'podman.exe'


def test_bounded_probe_cleanup_does_not_wait_for_retained_stdout_writer():
    """Breaks if an inherited stdout writer can outlive the probe cleanup deadline."""
    from agentci.sandbox.readiness import _run_bounded_probe

    retained_writers = []
    finished = threading.Event()
    result = []

    def run(argv, **kwargs):
        output = kwargs['stdout']
        retained_writers.append(os.fdopen(os.dup(output.fileno()), 'wb'))
        output.write(b'tool version 1.2.3')
        output.flush()
        return subprocess.CompletedProcess(argv, 0, stdout=None, stderr=None)

    def invoke():
        try:
            result.append(_run_bounded_probe(run, ['C:/tools/tool.exe', '--version']))
        finally:
            finished.set()

    worker = threading.Thread(target=invoke, daemon=True)
    worker.start()
    try:
        assert finished.wait(0.25), 'bounded cleanup must not wait for inherited stdout EOF'
        assert result[0][1] == b'tool version 1.2.3'
    finally:
        for writer in retained_writers:
            writer.close()
        worker.join(timeout=1)
    assert not worker.is_alive()


def test_bounded_probe_reader_solely_owns_descriptor_during_continuous_output(monkeypatch):
    """Breaks if cleanup double-closes or races a still-active reader's descriptor."""
    from agentci.sandbox import readiness

    real_os = os
    close_calls = []
    reader_closed = threading.Event()
    writer_finished = threading.Event()
    stop_writing = threading.Event()
    keepalive_read, keepalive_write = real_os.pipe()

    class DescriptorOps:
        read_fd = None
        reused_fd = None

        @staticmethod
        def pipe():
            read_fd, write_fd = real_os.pipe()
            DescriptorOps.read_fd = read_fd
            return read_fd, write_fd

        set_blocking = staticmethod(real_os.set_blocking)
        read = staticmethod(real_os.read)
        fdopen = staticmethod(real_os.fdopen)

        @staticmethod
        def close(fd):
            origin = threading.current_thread().name
            close_calls.append((origin, fd))
            if fd == DescriptorOps.read_fd and origin != 'agentci-sandbox-probe-reader' and DescriptorOps.reused_fd is None:
                real_os.close(fd)
                real_os.dup2(keepalive_read, fd)
                DescriptorOps.reused_fd = fd
                return
            real_os.close(fd)
            if fd == DescriptorOps.read_fd:
                reader_closed.set()

    monkeypatch.setattr(readiness, 'os', DescriptorOps)

    def run(argv, **kwargs):
        writer = real_os.fdopen(real_os.dup(kwargs['stdout'].fileno()), 'wb', buffering=0)

        def write_continuously():
            try:
                while not stop_writing.is_set():
                    writer.write(b'tool version 1.2.3\n')
            except OSError:
                pass
            finally:
                writer.close()
                writer_finished.set()

        threading.Thread(target=write_continuously, name='retained-writer', daemon=True).start()
        return subprocess.CompletedProcess(argv, 0, stdout=None, stderr=None)

    started = time.monotonic()
    try:
        _, captured = readiness._run_bounded_probe(run, ['C:/tools/tool.exe', '--version'])
        assert time.monotonic() - started < 0.5
        assert captured.startswith(b'tool version 1.2.3')
        assert reader_closed.wait(0.25)
        assert DescriptorOps.reused_fd is None
        assert close_calls == [('agentci-sandbox-probe-reader', DescriptorOps.read_fd)]
        assert writer_finished.wait(0.5)
    finally:
        stop_writing.set()
        for fd in (keepalive_read, keepalive_write):
            try:
                real_os.close(fd)
            except OSError:
                pass


def test_windows_sandbox_absence_differs_from_detected_unverified_presence():
    """Breaks if absent and present-without-safe-handshake Windows Sandbox look identical."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    candidate = Candidate(
        'windows-sandbox', 'os-sandbox', 'WindowsSandbox.exe', None, unverified_reason='no safe handshake',
    )
    absent = collect_readiness_report(candidates=(candidate,), resolve=lambda name: None)
    present = collect_readiness_report(
        candidates=(candidate,), resolve=lambda name: 'C:/Windows/System32/WindowsSandbox.exe',
    )
    assert (absent.candidates[0].state, absent.candidates[0].discovered, absent.candidates[0].installed) == (
        'missing', False, False,
    )
    assert (present.candidates[0].state, present.candidates[0].discovered, present.candidates[0].installed) == (
        'unverified', True, True,
    )


def test_report_redacts_local_details_and_states_truth_boundary():
    """Breaks if reports disclose local paths/output or omit their readiness limitation."""
    from agentci.sandbox.readiness import Candidate, collect_readiness_report

    captured_stdout = []

    def run(argv, **kwargs):
        captured_stdout.append(kwargs['stdout'])
        return subprocess.CompletedProcess(
            argv, 0, stdout='Docker version 27.3.1, build token=secret-value' + ('x' * 1000), stderr='',
        )

    report = collect_readiness_report(
        candidates=(Candidate('docker', 'container', 'docker', ('docker', '--version')),),
        resolve=lambda name: 'C:/Users/alice/.secret/bin/docker.exe',
        run=run,
        platform_facts=('Windows', '11', 'AMD64', '3.11.9'),
    ).to_dict()
    encoded = json.dumps(report)
    assert report['candidates'][0]['executable'] == 'docker.exe'
    assert report['candidates'][0]['probe_method'] == 'docker --version'
    assert report['candidates'][0]['version'] == '27.3.1'
    assert 'alice' not in encoded
    assert 'secret-value' not in encoded
    assert len(report['candidates'][0]['version']) <= 32
    assert captured_stdout[0] is not subprocess.PIPE
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
