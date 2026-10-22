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
import statistics
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

    This is the regression: with SystemDrive missing, taskkill takes a slow
    fallback path, and under load that slow path blows past the 10s taskkill
    timeout -- so the kill became late and a 5s per-file timeout took ~15s.

    The removal has to happen in THIS process's environment, because that is
    the environment _kill_tree copies when it spawns taskkill. Stripping it
    only from the child's env does not exercise the bug at all.

    The bound is deliberately generous. On an idle machine the unfixed path
    still finishes in ~1s, so a tight absolute threshold would pass against
    the unfixed code; the tight relative assertion lives in
    test_taskkill_is_slower_without_systemdrive. This test's job is the
    contract "the kill never waits for taskkill's timeout".
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
            # A taskkill that hits its own 10s timeout adds 10s to every
            # timed-out file. The fix must keep the kill in the ~1s range
            # even when the caller stripped SystemDrive.
            assert elapsed < 6.0, (
                f"_kill_tree took {elapsed:.1f}s with SystemDrive missing -- "
                "taskkill fell back to its slow path; the kill must not "
                "wait for taskkill's timeout"
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
def test_kill_tree_passes_systemdrive_to_taskkill(monkeypatch):
    """_kill_tree must hand taskkill an env that contains SystemDrive.

    This is the invariant the fix establishes, and it is checkable without
    relying on timing: taskkill needs SystemDrive to take its fast path,
    and _kill_tree is the only place that can supply it when the caller
    stripped it (the canonical runner starts pytest under `env -i`).

    The timing-based tests around it are load-dependent -- on an idle
    machine the unfixed slow path still finishes in ~1s -- so this
    structural assertion is what actually pins the fix. It fails against
    the unfixed code on every machine, at every load.
    """
    monkeypatch.delenv("SystemDrive", raising=False)
    monkeypatch.delenv("SYSTEMDRIVE", raising=False)

    captured = {}

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr("scripts.run_tests_parallel.subprocess.run", _fake_run)

    proc = _spawn_sleeper(dict(os.environ))
    try:
        _kill_tree(proc, pgid=None)
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    assert captured.get("cmd"), "taskkill was never invoked"
    assert "taskkill" in " ".join(captured["cmd"]), (
        f"expected a taskkill invocation, got {captured['cmd']}"
    )
    env = captured.get("env")
    assert env is not None, (
        "taskkill must be invoked with an explicit env -- otherwise it "
        "inherits the caller's env, which may lack SystemDrive"
    )
    assert env.get("SystemDrive") or env.get("SYSTEMDRIVE"), (
        "the env handed to taskkill must contain SystemDrive; without it "
        "taskkill takes the slow fallback path and the kill arrives late"
    )


@pytest.mark.skipif(not IS_WINDOWS, reason="taskkill is Windows-only")
def test_taskkill_is_slower_without_systemdrive():
    """Pin the underlying OS behaviour the fix works around.

    Without SystemDrive, taskkill takes a slow fallback path: it cannot
    build the job object path directly and has to search for the drive.

    Measured on an idle host: ~1.05 s without vs ~0.19 s with (about 6x).
    Under CPU load the slow path stretches to ~6-7 s and blows past a 5-10 s
    timeout -- which is how the kill became late in the first place.

    The comparison is RELATIVE on purpose. An absolute threshold does not
    work: on an idle machine the slow path never exceeds the timeout, so a
    "did it hang?" assertion passes against the unfixed code. Measuring both
    variants in the same run cancels out the machine's load.

    If this test ever starts failing, the underlying Windows behaviour
    changed and the workaround in _kill_tree can be revisited.
    """
    def _run(env, timeout=30.0):
        proc = _spawn_sleeper(env)
        try:
            start = time.monotonic()
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                env=env,
            )
            return time.monotonic() - start
        finally:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                pass

    without = _stripped_env_without_systemdrive()
    with_drive = dict(without)
    root = with_drive.get("SystemRoot") or r"C:\Windows"
    with_drive["SystemDrive"] = root.split(":", 1)[0] + ":"

    # Interleave the two so both see the same machine load.
    slow, fast = [], []
    for _ in range(3):
        slow.append(_run(without))
        fast.append(_run(with_drive))

    slow_med = statistics.median(slow)
    fast_med = statistics.median(fast)

    assert slow_med > fast_med * 2.0, (
        f"taskkill without SystemDrive was not slower than with it: "
        f"without={slow_med:.2f}s {slow} with={fast_med:.2f}s {fast} -- "
        "the slow fallback path the fix works around may be gone"
    )


@pytest.mark.skipif(not IS_WINDOWS, reason="taskkill is Windows-only")
def test_taskkill_is_fast_with_systemdrive():
    """With SystemDrive present, taskkill must complete quickly.

    A loose bound on purpose: this runs on whatever load the machine
    happens to have, so the absolute number is not the contract -- the
    relative comparison in the test above is.
    """
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
            timeout=30.0,
            env=env,
        )
        elapsed = time.monotonic() - start
        assert elapsed < 8.0, f"taskkill took {elapsed:.1f}s with SystemDrive set"
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
