"""A per-file timeout must not be retried like a flaky test.

``_run_one_file`` re-runs a file whose exit code is non-zero, so a genuinely
flaky file can pass on the second attempt. A per-file timeout is a different
failure: the file hangs deterministically. Retrying it costs another full
``file_timeout`` (900s in CI) and buries the hang under a second timeout --
which is how a CI test slice ended up sitting at exactly 30 minutes before
the job-level timeout killed it, with the offending file never named.

Contract: exit code 124 is the runner's own convention for "killed by
timeout". It is reported as a failure immediately, without a retry.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_tests_parallel import _run_one_file  # noqa: E402

TIMEOUT_RC = 124


def _write_hanging_test(tmp_path: Path) -> Path:
    """A test file that blocks forever, so the runner kills it on timeout."""
    test_file = tmp_path / "test_hangs.py"
    test_file.write_text(
        "import time\n\n\ndef test_never_ends():\n    time.sleep(3600)\n",
        encoding="utf-8",
    )
    return test_file


def test_timeout_is_not_retried(tmp_path, monkeypatch):
    """A timed-out file is attempted once, not twice.

    The retry doubles the wall-clock cost of a hang and hides which file
    hung, so the timeout path must short-circuit the retry loop.
    """
    test_file = _write_hanging_test(tmp_path)
    attempts = []

    def _fake_run_once(file, pytest_args, repo_root, file_timeout):
        attempts.append(file)
        return file, TIMEOUT_RC, f"({file_timeout:.0f}s exceeded)", {}, file_timeout

    monkeypatch.setattr(
        "scripts.run_tests_parallel._run_one_file_once", _fake_run_once
    )

    _, rc, output, _, _ = _run_one_file(
        test_file, [], tmp_path, file_timeout=1.0, retries=3
    )

    assert len(attempts) == 1, (
        "a timed-out file must be attempted exactly once; "
        f"it was attempted {len(attempts)} times"
    )
    assert rc == TIMEOUT_RC
    # The runner's timeout output says "<n>s exceeded", not "timeout" -- match
    # on the exit code (already asserted) and just keep the output non-empty
    # so the report shows why the file failed.
    assert output.strip(), "a timeout must carry an explanation"


def test_real_failure_is_still_retried(tmp_path, monkeypatch):
    """The retry must survive for genuine flakiness.

    A non-timeout failure that passes on the second attempt is a flaky test
    and must still be reported as passing (with a FLAKY banner) -- that is
    the whole point of the retry, and the timeout fix must not disable it.
    """
    test_file = tmp_path / "test_flaky.py"
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    attempts = []

    def _fake_run_once(file, pytest_args, repo_root, file_timeout):
        attempts.append(file)
        if len(attempts) == 1:
            return file, 1, "1 failed", {}, 0.1
        return file, 0, "1 passed", {"passed": 1}, 0.1

    monkeypatch.setattr(
        "scripts.run_tests_parallel._run_one_file_once", _fake_run_once
    )

    _, rc, output, _, _ = _run_one_file(
        test_file, [], tmp_path, file_timeout=30.0, retries=1
    )

    assert len(attempts) == 2, "a real failure must still get its one retry"
    assert rc == 0, "a flaky file that passes on retry must count as passed"
    assert "FLAKY" in output


def test_timeout_failure_is_reported_as_failed(tmp_path, monkeypatch):
    """A timeout that also times out on retry must not be laundered green.

    Even if a retry is attempted, a second timeout must not be reported as
    a pass -- the file stays failed.
    """
    test_file = _write_hanging_test(tmp_path)

    def _fake_run_once(file, pytest_args, repo_root, file_timeout):
        return file, TIMEOUT_RC, f"({file_timeout:.0f}s exceeded)", {}, file_timeout

    monkeypatch.setattr(
        "scripts.run_tests_parallel._run_one_file_once", _fake_run_once
    )

    _, rc, _, _, _ = _run_one_file(
        test_file, [], tmp_path, file_timeout=1.0, retries=1
    )

    assert rc == TIMEOUT_RC, "a timeout must never be reported as success"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
