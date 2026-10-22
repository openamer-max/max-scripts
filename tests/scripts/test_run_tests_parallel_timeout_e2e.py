"""End-to-end check: a genuinely hanging test file costs exactly one attempt.

The unit test mocks _run_one_file_once. This drives the real subprocess path
with a file that sleeps past the timeout, and asserts the runner reports the
timeout instead of retrying it for a second full timeout window.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_tests_parallel import _run_one_file  # noqa: E402


def test_real_hanging_file_is_attempted_once(tmp_path):
    """One attempt, not one per retry slot.

    With --file-timeout 5 and retries=3 this used to take 20s (4 x 5s). It
    must now take ~5s, because a timeout is deterministic.
    """
    test_file = tmp_path / "test_real_hang.py"
    test_file.write_text(
        "import time\n\n\ndef test_hangs():\n    time.sleep(120)\n",
        encoding="utf-8",
    )

    start = time.monotonic()
    _, rc, output, _, _ = _run_one_file(
        test_file, ["-p", "no:cacheprovider", "-q"], tmp_path,
        file_timeout=5.0, retries=3,
    )
    elapsed = time.monotonic() - start

    assert rc == 124, f"expected the timeout exit code, got {rc}"
    assert "exceeded" in output, f"timeout explanation missing: {output[:200]!r}"
    # One attempt at 5s must stay well under two attempts (10s).
    assert elapsed < 9.0, (
        f"the hanging file was retried: {elapsed:.1f}s for a 5s timeout "
        f"with 3 retries -- a retry would push this past 10s"
    )


if __name__ == "__main__":  # pragma: no cover
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
