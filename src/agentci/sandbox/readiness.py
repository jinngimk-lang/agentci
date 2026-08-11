"""Bounded, side-effect-free discovery of local sandbox backends."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import threading
from typing import Callable, Sequence

from agentci import __version__


REPORT_VERSION = 'v0alpha1'
PROBE_TIMEOUT_SECONDS = 2
MAX_PROBE_OUTPUT_BYTES = 256
MAX_VERSION_LENGTH = 32
READER_CLEANUP_SECONDS = 0.1
READER_POLL_SECONDS = 0.01
VERSION_PATTERN = re.compile(r'\b(\d+(?:\.\d+){1,3})\b')
LIMITATIONS = (
    'Readiness is not backend execution.',
    'Readiness is not isolation proof.',
    'Readiness is not security certification.',
)


@dataclass(frozen=True)
class Candidate:
    """A local executable candidate and its harmless probe command."""

    id: str
    backend_class: str
    executable: str | None
    probe_argv: tuple[str, ...] | None
    requires_success: bool = True
    unverified_reason: str | None = None


@dataclass(frozen=True)
class CandidateReport:
    id: str
    candidate_class: str
    executable: str | None
    version: str | None
    probe_method: str | None
    state: str
    discovered: bool | None
    installed: bool | None
    configured: bool | None
    probed: bool
    readiness: str
    reason: str | None


@dataclass(frozen=True)
class ReadinessReport:
    platform: dict[str, str]
    state: str
    active_backend: str | None
    candidates: tuple[CandidateReport, ...]
    limitations: tuple[str, ...] = LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        return {
            'report_version': REPORT_VERSION,
            'api_version': REPORT_VERSION,
            'agentci_version': __version__,
            'platform': self.platform,
            'state': self.state,
            'active_backend': self.active_backend,
            'candidates': [asdict(candidate) for candidate in self.candidates],
            'limitations': list(self.limitations),
        }


Resolver = Callable[[str], str | None]
Runner = Callable[..., subprocess.CompletedProcess[str]]


def default_candidates(system: str) -> tuple[Candidate, ...]:
    """Return deterministic preference order for platform-relevant candidates."""
    candidates = (
        Candidate('docker', 'container', 'docker', ('docker', '--version')),
        Candidate('podman', 'container', 'podman', ('podman', '--version')),
        Candidate('bubblewrap', 'os-sandbox', 'bwrap', ('bwrap', '--version')),
    )
    if system.lower() != 'windows':
        return candidates
    return candidates + (
        Candidate('wsl', 'os-sandbox', 'wsl.exe', ('wsl.exe', '--status')),
        Candidate(
            'windows-sandbox',
            'os-sandbox',
            'WindowsSandbox.exe',
            None,
            unverified_reason='Windows Sandbox has no safe executable readiness handshake.',
        ),
    )


def collect_readiness_report(
    *,
    candidates: Sequence[Candidate] | None = None,
    resolve: Resolver = shutil.which,
    run: Runner = subprocess.run,
    platform_facts: tuple[str, str, str, str] | None = None,
) -> ReadinessReport:
    """Probe each candidate independently without creating a sandbox or using a shell."""
    facts = platform_facts or (
        platform.system(),
        platform.release(),
        platform.machine(),
        platform.python_version(),
    )
    system, release, machine, python_version = facts
    reports = tuple(
        _inspect_candidate(candidate, resolve=resolve, run=run)
        for candidate in (candidates or default_candidates(system))
    )
    active_backend = next((candidate.id for candidate in reports if candidate.state == 'healthy'), None)
    return ReadinessReport(
        platform={
            'system': system,
            'release': release,
            'machine': machine,
            'python': python_version,
        },
        state='ready' if active_backend else 'not-ready',
        active_backend=active_backend,
        candidates=reports,
    )


def _inspect_candidate(candidate: Candidate, *, resolve: Resolver, run: Runner) -> CandidateReport:
    if candidate.executable is None:
        return CandidateReport(
            id=candidate.id,
            candidate_class=candidate.backend_class,
            executable=None,
            version=None,
            probe_method=None,
            state='unverified',
            discovered=None,
            installed=None,
            configured=None,
            probed=False,
            readiness='unverified',
            reason=candidate.unverified_reason or 'No safe readiness probe is defined.',
        )

    try:
        resolved = resolve(candidate.executable)
    except Exception:
        return CandidateReport(
            id=candidate.id,
            candidate_class=candidate.backend_class,
            executable=None,
            version=None,
            probe_method=' '.join(candidate.probe_argv) if candidate.probe_argv else None,
            state='probe-error',
            discovered=False,
            installed=None,
            configured=None,
            probed=False,
            readiness='not-ready',
            reason='Executable discovery failed.',
        )

    probe_method = ' '.join(candidate.probe_argv) if candidate.probe_argv else None
    if not resolved:
        return CandidateReport(
            id=candidate.id,
            candidate_class=candidate.backend_class,
            executable=None,
            version=None,
            probe_method=probe_method,
            state='missing',
            discovered=False,
            installed=False,
            configured=None,
            probed=False,
            readiness='not-ready',
            reason='Executable was not found on PATH.',
        )

    executable = Path(resolved).name
    if candidate.unverified_reason or candidate.probe_argv is None:
        return CandidateReport(
            id=candidate.id,
            candidate_class=candidate.backend_class,
            executable=executable,
            version=None,
            probe_method=probe_method,
            state='unverified',
            discovered=True,
            installed=True,
            configured=None,
            probed=False,
            readiness='unverified',
            reason=candidate.unverified_reason or 'No safe readiness probe is defined.',
        )

    execution_argv = [str(resolved), *candidate.probe_argv[1:]]
    try:
        completed, captured_output = _run_bounded_probe(run, execution_argv)
    except subprocess.TimeoutExpired:
        return _failed_candidate(candidate, executable, probe_method, 'probe-timeout', 'Probe exceeded its 2-second limit.')
    except OSError:
        return _failed_candidate(candidate, executable, probe_method, 'broken', 'Executable could not be started.')
    except Exception:
        return _failed_candidate(candidate, executable, probe_method, 'probe-error', 'Probe failed unexpectedly.')

    if completed.returncode != 0:
        return _failed_candidate(candidate, executable, probe_method, 'broken', 'Probe exited unsuccessfully.')
    return CandidateReport(
        id=candidate.id,
        candidate_class=candidate.backend_class,
        executable=executable,
        version=_extract_version(captured_output or completed.stdout),
        probe_method=probe_method,
        state='healthy',
        discovered=True,
        installed=True,
        configured=True if candidate.id == 'wsl' else None,
        probed=True,
        readiness='ready',
        reason=None,
    )


def _extract_version(output: bytes | str | None) -> str | None:
    """Return only a bounded numeric version token; never report raw probe output."""
    if isinstance(output, bytes):
        bounded_output = output[:MAX_PROBE_OUTPUT_BYTES].decode('utf-8', errors='replace')
    elif isinstance(output, str):
        bounded_output = output[:MAX_PROBE_OUTPUT_BYTES]
    else:
        return None
    match = VERSION_PATTERN.search(bounded_output)
    return match.group(1)[:MAX_VERSION_LENGTH] if match else None


def _run_bounded_probe(run: Runner, argv: list[str]) -> tuple[subprocess.CompletedProcess[str], bytes]:
    """Run a probe while draining stdout and retaining no more than the output limit."""
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    captured = bytearray()
    direct_process_finished = threading.Event()

    def drain_output() -> None:
        final_empty_read = False
        try:
            while True:
                try:
                    chunk = os.read(read_fd, 4096)
                except BlockingIOError:
                    if direct_process_finished.is_set():
                        if final_empty_read:
                            return
                        final_empty_read = True
                        continue
                    direct_process_finished.wait(READER_POLL_SECONDS)
                    continue
                if not chunk:
                    return
                final_empty_read = False
                remaining = MAX_PROBE_OUTPUT_BYTES - len(captured)
                if remaining > 0:
                    captured.extend(chunk[:remaining])
        except OSError:
            pass
        finally:
            try:
                os.close(read_fd)
            except OSError:
                pass

    reader = threading.Thread(target=drain_output, daemon=True)
    reader.start()
    try:
        with os.fdopen(write_fd, 'wb') as output:
            completed = run(
                argv,
                shell=False,
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=PROBE_TIMEOUT_SECONDS,
                text=False,
            )
    finally:
        direct_process_finished.set()
        reader.join(READER_CLEANUP_SECONDS)
        if reader.is_alive():
            try:
                os.close(read_fd)
            except OSError:
                pass
    return completed, bytes(captured)


def _failed_candidate(
    candidate: Candidate,
    executable: str,
    probe_method: str,
    state: str,
    reason: str,
) -> CandidateReport:
    return CandidateReport(
        id=candidate.id,
        candidate_class=candidate.backend_class,
        executable=executable,
        version=None,
        probe_method=probe_method,
        state=state,
        discovered=True,
        installed=True,
        configured=False if candidate.id == 'wsl' else None,
        probed=True,
        readiness='not-ready',
        reason=reason,
    )
