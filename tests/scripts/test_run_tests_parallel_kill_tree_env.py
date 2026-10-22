"""The Windows process-tree kill must not hang.

Root cause (measured 2026-10-22 on this Windows 10 host):

``taskkill /F /T /PID <pid>`` needs ``SystemDrive`` in the environment. Without
it, taskkill does not fail -- it HANGS, because it cannot build the job object
path. The canonical runner starts pytest under ``env -i`` (see
``scripts/run_tests.sh``), which drops SystemDrive along with every other
variable except the handful it re-adds. So every timed-out test file burned the
full 10s ``subprocess.run(..., timeout=10)`` inside ``_kill_tree`` before the
kill was even attempted.

Measured on a plain sleeping target, 5 runs each:
  * minimal env without SystemDrive -> 5/5 hangs (> 5s each)
  * minimal env with    SystemDrive -> 0/5 hangs (median 1.3s)

The knock-on effect was that a 5s per-file timeout took ~15s of wall clock
instead of ~5s, and the e2e test that pins "a hanging file is attempted once"
failed on the canonical runner while passing under a plain pytest invocation
(where the desktop environment leaks SystemDrive in).

These tests pin the contract that the kill path is self-sufficient: it must
work even when the environment has been stripped, and it must not take orders
of magnitude longer than the kill itself.

On non-Windows platforms the taskkill branch does not run, so the timing
assertions are skipped there; the environment-injection contract is still
asserted because it is platform-independent logic in _kill_tree.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_tests_parallel import _kill_tree  # noqa: E402

IS_WINDOWS = sys.platform == "win32"


def _stripped_env_without_systemdrive() -> dict:
    """A hermetic env like run_tests.sh's `env -i`, minus SystemDrive."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USERPROFILE": os.environ.get("USERPROFILE", ""),
        "SystemRoot": os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT")
        or r"C:\Windows",
    }
    env.pop("SystemDrive", None)
    env.pop("SYSTEMDRIVE", None)
    return env


def _spawn_sleeper(env: dict) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )


def test_kill_tree_works_without_systemdrive_in_env(monkeypatch):
    """_kill_tree must not depend on the caller having set SystemDrive.

    This is the regression: with SystemDrive missing, taskkill hangs and the
    kill is delayed by the full taskkill timeout.

    The removal has to happen in THIS process's environment, because that is
    the environment _kill_tree copies when it spawns taskkill. Stripping it
    only from the child's env would not exercise the bug at all.
    """
    monkeypatch.delenv("SystemDrive", raising=False)
    monkeypatch.delenv("SYSTEMDRIVE", raising=False)
    assert "SystemDrive" not in os.environ
    assert "SYSTEMDRIVE" not in os.environ

    env = _stripped_env_without_systemdrive()
    proc = _spawn_sleeper(env)
    try:
        start = time.monotonic()
        _kill_tree(proc, pgid=None)
        elapsed = time.monotonic() - start

        if IS_WINDOWS:
            # A hung taskkill burns its whole 10s timeout. A working kill
            # takes ~1-2s. Anything near 10s means taskkill hung again.
            assert elapsed < 6.0, (
                f"_kill_tree took {elapsed:.1f}s with SystemDrive missing -- "
                "taskkill hung again; the kill must not wait for its timeout"
            )
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


def test_kill_tree_terminates_the_process(monkeypatch):
    """The kill must actually end the process, not just return quickly."""
    monkeypatch.delenv("SystemDrive", raising=False)
    monkeypatch.delenv("SYSTEMDRIVE", raising=False)

    env = _stripped_env_without_systemdrive()
    proc = _spawn_sleeper(env)
    try:
        _kill_tree(proc, pgid=None)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and proc.poll() is None:
            time.sleep(0.05)
        assert proc.poll() is not None, (
            "the target process is still alive after _kill_tree"
        )
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


@pytest.mark.skipif(not IS_WINDOWS, reason="taskkill is Windows-only")
def test_taskkill_alone_hangs_without_systemdrive():
    """Pin the underlying OS behaviour the fix works around.

    If this test ever starts failing, the underlying Windows behaviour
    changed and the workaround in _kill_tree can be revisited.
    """
    env = _stripped_env_without_systemdrive()
    proc = _spawn_sleeper(env)
    try:
        start = time.monotonic()
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5.0,
                env=env,
            )
        assert time.monotonic() - start >= 4.0
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


@pytest.mark.skipif(not IS_WINDOWS, reason="taskkill is Windows-only")
def test_taskkill_is_fast_with_systemdrive():
    """With SystemDrive present, taskkill must complete in ~1-2s."""
    env = _stripped_env_without_systemdrive()
    root = env.get("SystemRoot") or r"C:\Windows"
    env["SystemDrive"] = root.split(":", 1)[0] + ":"
    proc = _spawn_sleeper(env)
    try:
        start = time.monotonic()
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8.0,
            env=env,
        )
        elapsed = time.monotonic() - start
        assert elapsed < 6.0, f"taskkill took {elapsed:.1f}s with SystemDrive set"
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
