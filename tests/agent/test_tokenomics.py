"""The OAC allocation must be arithmetic, not prose.

The tokenomics live in ``agent/tokenomics.py`` so the constitution is
rendered from them. These tests pin the two things that matter:

  * the balance closes the cap, exactly, and
  * a broken allocation fails loudly at import time rather than shipping
    a prompt that states wrong figures.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from agent import tokenomics as tok  # noqa: E402


def test_the_allocation_closes_the_cap_exactly():
    """75 + 15 + 10 = 100, and the amounts sum to the maximum supply."""
    assert sum(a.percent for a in tok.ALLOCATION) == 100
    assert sum(a.amount for a in tok.ALLOCATION) == tok.MAX_SUPPLY


@pytest.mark.parametrize("a", tok.ALLOCATION, ids=lambda a: a.key)
def test_each_share_is_the_percentage_it_claims(a):
    """The amount must be exactly the percentage of the cap.

    A share that says 75% but encodes 74% is the classic tokenomics bug.
    """
    assert a.amount == a.percent * tok.MAX_SUPPLY // 100
    assert a.amount * 100 == a.percent * tok.MAX_SUPPLY


def test_the_three_shares_are_the_expected_ones():
    """The allocation is fixed: mining pool, treasury, creator."""
    assert [a.key for a in tok.ALLOCATION] == [
        "mining_pool",
        "treasury",
        "creator",
    ]
    assert [a.percent for a in tok.ALLOCATION] == [75, 15, 10]
    assert [a.amount for a in tok.ALLOCATION] == [
        6_750_000_000,
        1_350_000_000,
        900_000_000,
    ]


def test_amount_is_derived_not_declared():
    """amount() computes from the cap, so it cannot drift from the percent."""
    assert tok.amount(75) == 6_750_000_000
    assert tok.amount(15) == 1_350_000_000
    assert tok.amount(10) == 900_000_000
    assert tok.amount(50) == 4_500_000_000


def test_formatted_renders_the_share_for_prose():
    """The prose form: '75% (6,750,000,000 OAC)'."""
    assert tok.formatted(75) == "75% (6,750,000,000 OAC)"
    assert tok.formatted(10) == "10% (900,000,000 OAC)"


def test_balance_lines_cover_every_share():
    """The rendered balance names all three shares, in allocation order."""
    lines = tok.balance_lines()
    assert len(lines) == 3
    assert "mining pool" in lines[0]
    assert "Sovereign Treasury" in lines[1]
    assert "creator allocation" in lines[2]


def test_a_broken_allocation_fails_at_import_time():
    """A wrong balance must raise immediately, not silently ship.

    Runs a fresh interpreter with a patched allocation, because the
    balance check runs at import. If the check is ever removed, this
    test fails -- the module would import happily with a broken plan.
    """
    script = f"""
import sys
sys.path.insert(0, {str(REPO)!r})
import agent.tokenomics as tok
tok.ALLOCATION = [
    tok.Allocation("mining_pool", "mining pool", 70, 6_750_000_000),
    *tok.ALLOCATION[1:],
]
tok._assert_balance()
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert proc.returncode != 0, (
        "a 70/15/10 allocation must not pass the balance check"
    )
    assert "not 100%" in proc.stderr or "maximum supply" in proc.stderr, (
        f"unexpected failure: {proc.stderr[-500:]}"
    )


def test_the_halving_schedule_covers_the_emission_period():
    """8 cycles of 4 years must be the 32-year emission schedule.

    The second balance, independent of the supply one: a schedule whose
    cycles do not cover the period is the same class of bug.
    """
    assert tok.HALVING_CYCLES * tok.HALVING_YEARS == tok.EMISSION_YEARS
    assert tok.EMISSION_YEARS == 32
    assert tok.HALVING_CYCLES == 8
    assert tok.HALVING_YEARS == 4


def test_a_broken_schedule_fails_at_import_time():
    """A schedule that does not cover the emission period must raise."""
    script = f"""
import sys
sys.path.insert(0, {str(REPO)!r})
import agent.tokenomics as tok
tok.HALVING_YEARS = 5
tok._assert_balance()
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert proc.returncode != 0, "a 5-year cycle must not pass the schedule check"
    assert "emission schedule" in proc.stderr, (
        f"unexpected failure: {proc.stderr[-500:]}"
    )


def test_the_constitution_renders_the_allocation():
    """The rendered block carries the same numbers the module computes.

    This is the link between the arithmetic and the prompt: if the
    constitution stopped quoting the module, the two could drift apart
    again.
    """
    from agent.genesis_directives import render_genesis_block

    block = render_genesis_block()
    for a in tok.ALLOCATION:
        assert f"{a.percent}% ({a.amount:,} OAC)" in block, (
            f"the constitution does not quote {a.key} correctly"
        )
    assert f"{tok.MAX_SUPPLY:,} OAC" in block
