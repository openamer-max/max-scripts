"""OAC tokenomics — the supply allocation, as arithmetic rather than prose.

The constitution states the emission plan in words. Words drift: a share
gets renamed, a percentage gets edited in one place and not the other,
and the three shares stop adding up to the cap -- the classic tokenomics
bug, invisible to every reader because the text still reads fine.

So the numbers live here, once, and the constitution is rendered from
them. The balance cannot be broken by editing prose, because the prose no
longer holds the numbers.

    MINING_POOL   75%   6,750,000,000 OAC
    TREASURY      15%   1,350,000,000 OAC
    CREATOR       10%     900,000,000 OAC
    ------------------------------------
    TOTAL        100%   9,000,000,000 OAC

The module asserts its own balance at import time: a mismatch raises
immediately rather than shipping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

OAC = "OAC"
"""The ticker's display name. Kept as a constant so a rename cannot
leave one directive saying "OAC" and another saying something else."""


@dataclass(frozen=True)
class Allocation:
    """One share of the maximum supply."""

    key: str
    label: str
    percent: int
    amount: int


MAX_SUPPLY = 9_000_000_000
"""The mathematically fixed maximum supply, in OAC."""

EMISSION_YEARS = 32
"""The emission schedule spans 32 years."""

HALVING_CYCLES = 8
"""Eight degressive cycles of four years each."""

HALVING_YEARS = 4
"""Years per cycle."""


ALLOCATION: List[Allocation] = [
    Allocation(
        key="mining_pool",
        label="mining pool and PoUW rewards",
        percent=75,
        amount=6_750_000_000,
    ),
    Allocation(
        key="treasury",
        label="Sovereign Treasury",
        percent=15,
        amount=1_350_000_000,
    ),
    Allocation(
        key="creator",
        label="creator allocation",
        percent=10,
        amount=900_000_000,
    ),
]


def _assert_balance() -> None:
    """The allocation and the schedule must be consistent, exactly.

    Checked at import time: a broken tokenomics plan must fail loudly and
    immediately, not quietly produce a prompt that states wrong figures.

    Two independent balances are verified:

      * the supply -- the three shares must close the maximum supply, and
        each amount must be the percentage it claims,
      * the schedule -- the halving cycles must cover the emission period
        exactly (8 cycles of 4 years = 32 years).
    """
    total_amount = sum(a.amount for a in ALLOCATION)
    total_percent = sum(a.percent for a in ALLOCATION)
    if total_amount != MAX_SUPPLY:
        raise ValueError(
            f"OAC allocation sums to {total_amount:,}, not the "
            f"{MAX_SUPPLY:,} maximum supply"
        )
    if total_percent != 100:
        raise ValueError(
            f"OAC allocation sums to {total_percent}%, not 100%"
        )
    for a in ALLOCATION:
        if a.amount * 100 != a.percent * MAX_SUPPLY:
            raise ValueError(
                f"{a.key}: {a.percent}% is {a.percent * MAX_SUPPLY // 100:,} "
                f"OAC, not {a.amount:,}"
            )
    if HALVING_CYCLES * HALVING_YEARS != EMISSION_YEARS:
        raise ValueError(
            f"{HALVING_CYCLES} halving cycles of {HALVING_YEARS} years "
            f"cover {HALVING_CYCLES * HALVING_YEARS} years, not the "
            f"{EMISSION_YEARS}-year emission schedule"
        )


_assert_balance()


def amount(pct: int) -> int:
    """The OAC amount for a share of the maximum supply."""
    return pct * MAX_SUPPLY // 100


def share(key: str) -> Allocation:
    """One allocation by key."""
    for a in ALLOCATION:
        if a.key == key:
            return a
    raise KeyError(key)


def formatted(pct: int) -> str:
    """A share rendered for prose: ``75% (6,750,000,000 OAC)``."""
    return f"{pct}% ({amount(pct):,} {OAC})"


def balance_lines() -> List[str]:
    """The three shares as prose fragments, in allocation order.

    The order matters: the rendered directive should read like the
    allocation table, largest share first.
    """
    return [f"{a.percent}% ({a.amount:,} {OAC}) to the {a.label}" for a in ALLOCATION]
