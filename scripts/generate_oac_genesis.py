#!/usr/bin/env python3
"""Generate the OAC genesis contract from the tokenomics plan.

DIR-20 requires "an immutable emission protocol in the genesis block".
This renders the Solidity source that encodes it, with every number
derived from ``agent/tokenomics.py`` -- the same module the system
prompt quotes. One source, two projections: the constitution the agent
reads and the contract a chain would execute.

The output is committed, so a change to the plan shows up as a diff in
the contract rather than as a silent divergence. The test suite
asserts the committed file matches what the generator produces, so a
hand-edited contract fails CI.

This generates SOURCE. It deploys nothing: there is no chain, no key
and no wallet here. Deployment is a separate, deliberate act by the
owner.

Usage:
    python scripts/generate_oac_genesis.py [--check] [--out PATH]

    --check   verify the committed file is up to date; exit 1 if not
    --out     write somewhere else (default: chain/contracts/OpenAmerGenesis.sol)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import oac_genesis  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "chain" / "contracts" / "OpenAmerGenesis.sol"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the OAC genesis contract from the tokenomics plan."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed contract is up to date instead of writing",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output path (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args(argv)

    # Verify the rendered source before it touches the disk.
    oac_genesis.verify()
    source = oac_genesis.render_contract()

    out = args.out if args.out.is_absolute() else REPO_ROOT / args.out

    if args.check:
        if not out.exists():
            print(f"FAIL: {out} does not exist")
            return 1
        current = out.read_text(encoding="utf-8")
        if current != source:
            print(f"FAIL: {out} is out of date -- run this script to regenerate")
            return 1
        print(f"OK: {out.relative_to(REPO_ROOT)} is up to date")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(source, encoding="utf-8")
    rel = out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out
    print(f"wrote {rel} ({len(source):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
