"""Regression test for the batch_runner --list_distributions CLI flag.

History: the main() parameter was originally named ``list_distributions``,
which shadowed the imported ``list_distributions()`` function from
toolset_distributions -- calling ``batch_runner.py --list_distributions``
raised ``TypeError: 'bool' object is not callable``.

A first fix renamed the *parameter* to ``list_distributions_flag``. That
silently broke the documented CLI: ``--list_distributions`` stopped being
recognized (rc=2, "--dataset_file is required") and only the undocumented
``--list_distributions_flag`` worked.

The correct fix keeps the public flag name intact and aliases the *import*
instead. These tests pin both halves of that contract:

  1. the documented flag ``--list_distributions`` works end to end, and
  2. the imported function is still callable under its own name inside
     batch_runner's module namespace.

They are behavior contracts, not change detectors: they assert how the
public flag and the module-level helper must relate, not a frozen value.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

import batch_runner


def test_documented_flag_is_accepted_by_main():
    """main() must keep the documented parameter name --list_distributions."""
    import inspect

    params = inspect.signature(batch_runner.main).parameters
    assert "list_distributions" in params, (
        "main() must expose the documented 'list_distributions' parameter so "
        "that `python batch_runner.py --list_distributions` keeps working"
    )


def test_imported_distribution_helper_is_callable():
    """The list_distributions() helper must not be shadowed by a bool."""
    from toolset_distributions import list_distributions

    dists = batch_runner._list_distributions()
    assert isinstance(dists, dict)
    assert dists, "toolset_distributions must expose at least one distribution"
    # Sanity: same object shape as the canonical helper.
    assert set(dists.keys()) == set(list_distributions().keys())


def test_cli_flag_lists_distributions_end_to_end():
    """`python batch_runner.py --list_distributions` must exit 0 and list them."""
    result = subprocess.run(
        [sys.executable, "batch_runner.py", "--list_distributions"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"expected rc=0, got {result.returncode}\n"
        f"stdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}"
    )
    assert "Available Toolset Distributions" in result.stdout
    # A distribution name from the canonical set must show up in the output.
    from toolset_distributions import list_distributions

    expected = sorted(list_distributions().keys())
    assert expected, "no distributions registered"
    assert any(name in result.stdout for name in expected), (
        "no distribution name appeared in the CLI output"
    )


@pytest.mark.parametrize("flag", ["--list_distributions", "--list-distributions"])
def test_both_underscore_and_dash_spellings_work(flag):
    """Fire accepts both the underscore and the dash spelling."""
    result = subprocess.run(
        [sys.executable, "batch_runner.py", flag],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"{flag} failed with rc={result.returncode}: {result.stderr[-300:]}"
    )
