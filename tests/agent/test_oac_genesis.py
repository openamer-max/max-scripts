"""The OAC genesis contract must be generated, correct, and current.

DIR-20 requires an immutable emission protocol in the genesis block.
``agent.oac_genesis`` renders the Solidity source from the tokenomics
plan, and ``scripts/generate_oac_genesis.py`` writes it to
``chain/contracts/OpenAmerGenesis.sol``.

Three things are pinned here:

  * the rendered contract states the plan (every constant, every
    percentage, the cap, the schedule),
  * the contract is internally consistent -- the constructor assembles
    the total and re-checks every share against its percentage, so a
    mis-generated constant reverts on deployment instead of going live,
  * the committed file is what the generator produces -- a hand-edited
    contract fails CI, which is the whole point of committing it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from agent import oac_genesis, tokenomics as tok  # noqa: E402

CONTRACT = REPO / "chain" / "contracts" / "OpenAmerGenesis.sol"
GENERATOR = REPO / "scripts" / "generate_oac_genesis.py"


def test_the_committed_contract_is_up_to_date():
    """The committed contract must match what the generator produces.

    Run through the generator's own --check mode, so this is the same
    check CI would run -- not a re-implementation of it.
    """
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert proc.returncode == 0, (
        f"the committed contract is out of date:\n{proc.stdout}\n{proc.stderr}"
    )


def test_every_allocation_is_an_immutable_constant():
    """DIR-20 forbids changing the allocation after deployment.

    A non-constant allocation would be settable. So each share must be
    declared `uint256 public constant`.
    """
    source = oac_genesis.render_contract()
    for a in tok.ALLOCATION:
        decl = f"uint256 public constant {a.key.upper()}_ALLOCATION = {a.amount};"
        assert decl in source, f"missing or mutable: {decl}"


def test_the_contract_states_the_cap_and_the_schedule():
    """The contract carries the cap and the halving schedule."""
    source = oac_genesis.render_contract()
    assert f"uint256 public constant MAX_SUPPLY = {tok.MAX_SUPPLY};" in source
    assert f"uint32 public constant EMISSION_YEARS = {tok.EMISSION_YEARS};" in source
    assert f"uint32 public constant HALVING_CYCLES = {tok.HALVING_CYCLES};" in source
    assert f"uint32 public constant HALVING_YEARS = {tok.HALVING_YEARS};" in source


def test_the_constructor_assembles_and_verifies_the_total():
    """The constructor must build the total and check it against the cap.

    A contract that declared the constants but never summed them would
    look correct in a diff and revert on every deployment.
    """
    source = oac_genesis.render_contract()
    assert "uint256 total = 0;" in source
    for a in tok.ALLOCATION:
        assert f"total += {a.key.upper()}_ALLOCATION;" in source
    assert 'require(total == MAX_SUPPLY, "OAC: allocation does not close the cap");' in source
    # Every share is re-checked against the percentage it claims.
    for a in tok.ALLOCATION:
        assert (
            f"require({a.key.upper()}_ALLOCATION * 100 == {a.percent} * MAX_SUPPLY"
            in source
        )


def test_the_contract_rejects_a_mismatched_percentage():
    """A share that says 75% but encodes 74% must revert.

    The generator's own check cannot catch this on its own -- it would
    render it faithfully -- so the contract has to carry the check.
    """
    source = oac_genesis.render_contract()
    assert "does not match 75%" in source
    assert "does not match 15%" in source
    assert "does not match 10%" in source


def test_the_percentages_are_checked_to_sum_to_one_hundred():
    """The contract itself checks the percentage sum."""
    source = oac_genesis.render_contract()
    assert (
        "MINING_POOL_PERCENT + TREASURY_PERCENT + CREATOR_PERCENT == 100"
        in source
    )


def test_no_admin_mutation_path_exists():
    """No setter, no owner, no admin function.

    DIR-20: exclude any human or administrative influence on the crypto
    ledger and the emission logic. A contract with a mutator would
    violate that no matter what the constants say.
    """
    source = oac_genesis.render_contract()
    forbidden = ("function set", "function update", "onlyOwner", "onlyAdmin",
                 "_mint", "_burn", "selfdestruct", "delegatecall")
    for token in forbidden:
        assert token not in source, f"the genesis contract must not contain {token!r}"


def test_the_contract_exposes_the_allocation_read_only():
    """The allocation and the schedule are readable, and only readable."""
    source = oac_genesis.render_contract()
    assert "function allocations() external pure returns (uint256[3] memory)" in source
    assert "function emissionSchedule() external pure returns (uint32 cycles, uint32 yearsPerCycle)" in source


def test_the_render_is_deterministic():
    """The same plan must always render the same source.

    Otherwise the committed file would churn and the --check would be
    useless.
    """
    assert oac_genesis.render_contract() == oac_genesis.render_contract()


def test_the_rendered_constants_parse_back_to_the_plan():
    """Read the numbers back out of the source and compare them.

    Parsing the rendered text -- not just the renderer's internals --
    is what catches a template that emits the wrong literal.
    """
    source = oac_genesis.render_contract()
    for a in tok.ALLOCATION:
        m = re.search(
            rf"uint256 public constant {a.key.upper()}_ALLOCATION = (\d+);",
            source,
        )
        assert m, f"{a.key} is not declared in the contract"
        assert int(m.group(1)) == a.amount

    m = re.search(r"uint256 public constant MAX_SUPPLY = (\d+);", source)
    assert m and int(m.group(1)) == tok.MAX_SUPPLY

    m = re.search(r"uint256 public constant TOTAL_SUPPLY = (\d+);", source)
    assert m and int(m.group(1)) == sum(a.amount for a in tok.ALLOCATION)


def test_verify_rejects_a_contract_without_the_accumulation(monkeypatch):
    """The generator's own check must catch a broken constructor.

    A generator that emitted bare requires against an uninitialised
    total would produce a contract that reverts on every deployment --
    and the diff would look fine. So the check is mutation-tested here.
    """
    broken = oac_genesis.render_contract().replace(
        "        total += MINING_POOL_ALLOCATION;\n", ""
    )
    monkeypatch.setattr(oac_genesis, "render_contract", lambda: broken)
    with pytest.raises(ValueError, match="never adds mining_pool"):
        oac_genesis.verify()


def test_verify_rejects_a_mutable_allocation(monkeypatch):
    """A non-constant allocation must be rejected by the check."""
    broken = oac_genesis.render_contract().replace(
        "uint256 public constant MINING_POOL_ALLOCATION",
        "uint256 public MINING_POOL_ALLOCATION",
    )
    monkeypatch.setattr(oac_genesis, "render_contract", lambda: broken)
    with pytest.raises(ValueError, match="not an immutable constant"):
        oac_genesis.verify()


def test_verify_rejects_a_wrong_amount(monkeypatch):
    """A share with the wrong amount must be rejected."""
    broken = oac_genesis.render_contract().replace(
        "MINING_POOL_ALLOCATION = 6750000000;",
        "MINING_POOL_ALLOCATION = 6700000000;",
    )
    monkeypatch.setattr(oac_genesis, "render_contract", lambda: broken)
    with pytest.raises(ValueError, match="missing"):
        oac_genesis.verify()
