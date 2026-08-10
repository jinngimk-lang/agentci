from __future__ import annotations

import json
import math
import os
import queue
import signal
import subprocess
import threading
import time
from typing import Any, BinaryIO

from .config import Actual, EvalCase, LocalCommandTarget

LOCAL_COMMAND_OUTPUT_LIMIT_BYTES = 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000


def _error(started: float, message: str) -> Actual:
    return Actual(success=False, latency_ms=_elapsed_ms(started), error=message)


def _parse_output(stdout: str, started: float) -> Actual:
    try:
        raw: Any = json.loads(stdout)
    except json.JSONDecodeError:
        return _error(started, "local command returned invalid JSON")
    if not isinstance(raw, dict):
        return _error(started, "local command output must be a JSON object")
    success = raw.get("success")
    if not isinstance(success, bool):
        return _error(started, "local command output.success must be a boolean")
    cost_usd = raw.get("cost_usd")
    if cost_usd is not None:
        if isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float)):
            return _error(started, "local command output.cost_usd must be a non-negative finite number")
        cost_usd = float(cost_usd)
        if not math.isfinite(cost_usd) or cost_usd < 0:
            return _error(started, "local command output.cost_usd must be a non-negative finite number")
    return Actual(success=success, latency_ms=_elapsed_ms(started), cost_usd=cost_usd)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            if process.poll() is None:
                process.kill()
    elif process.poll() is None:
        process.kill()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            process.kill()
        process.wait()


def _read_bounded_stream(
    stream: BinaryIO,
    name: str,
    sink: bytearray | None,
    overflow: queue.Queue[str],
) -> None:
    total = 0
    try:
        while True:
            chunk = stream.read(_READ_CHUNK_BYTES)
            if not chunk:
                return
            total += len(chunk)
            if sink is not None and len(sink) < LOCAL_COMMAND_OUTPUT_LIMIT_BYTES:
                remaining = LOCAL_COMMAND_OUTPUT_LIMIT_BYTES - len(sink)
                sink.extend(chunk[:remaining])
            if total > LOCAL_COMMAND_OUTPUT_LIMIT_BYTES:
                overflow.put(name)
                return
    finally:
        stream.close()


def _join_readers(readers: tuple[threading.Thread, threading.Thread]) -> None:
    for reader in readers:
        reader.join(timeout=5)


def execute_local_command(target: LocalCommandTarget, case: EvalCase) -> Actual:
    payload = json.dumps({"id": case.id, "input": case.input}, ensure_ascii=False, separators=(",", ":")) + "\n"
    started = time.perf_counter()
    popen_kwargs: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        process = subprocess.Popen(list(target.command), **popen_kwargs)
    except FileNotFoundError:
        return _error(started, f"local command executable not found: {target.command[0]}")
    except OSError as exc:
        return _error(started, f"local command could not start: {exc}")

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    stdout = bytearray()
    overflow: queue.Queue[str] = queue.Queue()
    stdout_reader = threading.Thread(
        target=_read_bounded_stream,
        args=(process.stdout, "stdout", stdout, overflow),
        daemon=True,
    )
    stderr_reader = threading.Thread(
        target=_read_bounded_stream,
        args=(process.stderr, "stderr", None, overflow),
        daemon=True,
    )
    readers = (stdout_reader, stderr_reader)
    for reader in readers:
        reader.start()

    try:
        process.stdin.write(payload.encode("utf-8"))
        process.stdin.close()
    except (BrokenPipeError, OSError):
        try:
            process.stdin.close()
        except OSError:
            pass

    deadline = time.monotonic() + target.timeout_seconds
    while True:
        try:
            overflow_name = overflow.get_nowait()
        except queue.Empty:
            overflow_name = None
        if overflow_name is not None:
            _terminate_process_tree(process)
            _join_readers(readers)
            return _error(
                started,
                f"local command {overflow_name} exceeded {LOCAL_COMMAND_OUTPUT_LIMIT_BYTES} byte limit",
            )
        if process.poll() is not None and not any(reader.is_alive() for reader in readers):
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _terminate_process_tree(process)
            _join_readers(readers)
            return _error(started, f"local command timed out after {target.timeout_seconds:g} seconds")
        try:
            overflow_name = overflow.get(timeout=min(0.01, remaining))
        except queue.Empty:
            continue
        _terminate_process_tree(process)
        _join_readers(readers)
        return _error(
            started,
            f"local command {overflow_name} exceeded {LOCAL_COMMAND_OUTPUT_LIMIT_BYTES} byte limit",
        )

    if process.returncode != 0:
        return _error(started, f"local command exited with code {process.returncode}")
    try:
        decoded_stdout = bytes(stdout).decode("utf-8")
    except UnicodeDecodeError:
        return _error(started, "local command stdout must be UTF-8")
    return _parse_output(decoded_stdout, started)
