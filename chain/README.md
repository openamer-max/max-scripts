# OAC — the Open Amer Coin genesis

This directory holds the **generated** Solidity source that encodes the
OAC allocation. It is not hand-written and must not be edited by hand.

## One source, two projections

```
agent/tokenomics.py          <- the plan (the only place the numbers live)
        |
        +--> agent/genesis_directives.py --> the system prompt the agent reads
        |
        +--> agent/oac_genesis.py --------> chain/contracts/OpenAmerGenesis.sol
```

The constitution (DIR-20, DIR-22, DIR-03) and the contract state the
same allocation because they are rendered from the same module. Editing
the prose alone changes nothing; editing `agent/tokenomics.py` changes
both, and the balance check at import time refuses a plan that does not
close the cap.

## The allocation

| Share | Percent | OAC | Directive |
|---|---|---|---|
| Mining pool / PoUW rewards | 75 % | 6,750,000,000 | DIR-20 |
| Sovereign Treasury | 15 % | 1,350,000,000 | DIR-22 |
| Creator allocation | 10 % | 900,000,000 | DIR-03 |
| **Total** | **100 %** | **9,000,000,000** | maximum supply |

Emission schedule: 32 years, eight degressive halving cycles of four
years each.

## Regenerate

```bash
python scripts/generate_oac_genesis.py          # write the contract
python scripts/generate_oac_genesis.py --check  # verify it is current
python scripts/compile_oac_genesis.py           # compile it with solc
```

`--check` is what CI runs: it fails when the committed file no longer
matches the plan, so the two can never drift apart silently.

## What this is not

This directory contains **source**, not a deployment. There is no chain,
no key and no wallet here, and nothing in OpenAmer deploys anything.
Deployment is a separate, deliberate act by the owner — and the contract
is written so that the numbers it would deploy are already fixed,
immutable and verifiable by anyone.

The contract itself re-checks its own balance in the constructor, so a
mis-built genesis block cannot go live: the shares are `constant`, the
total must equal `MAX_SUPPLY`, and every share must equal the
percentage it claims.

## Verified

`tests/agent/test_oac_genesis.py` pins the content, and
`tests/agent/test_oac_genesis_compiles.py` compiles the contract with
solc and asserts it produces bytecode, an ABI with the allocation
exposed read-only, and no warnings.
