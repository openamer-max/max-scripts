#!/usr/bin/env python3
"""Compile the OAC genesis contract and report the compiler's verdict.

Used by CI (and by the test suite) to prove the contract actually builds.
The output is a one-line summary on stdout and the compiler's own
diagnostics on stderr; a failed compilation exits non-zero.

The compiler is resolved the same way the test suite resolves it:
``solc`` on PATH, the npm package ``solc``, or ``npx solc@<version>``.
The npm package is driven through its Node API via
``tests/agent/fixtures/compile_solidity.js`` -- its CLI shim mis-handles
--standard-json on Windows.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import oac_genesis  # noqa: E402

BRIDGE = REPO_ROOT / "tests" / "agent" / "fixtures" / "compile_solidity.js"


def _npm_solc_root() -> Path | None:
    """The local npm ``solc`` package, if installed.

    Searched in the places it actually lands: the repo's own
    ``node_modules`` (what CI installs into), a home-directory install,
    and the scratch directory the test suite uses.
    """
    candidates = [
        REPO_ROOT / "node_modules" / "solc",
        Path.home() / "node_modules" / "solc",
        Path(tempfile.gettempdir()) / "oac-solc" / "node_modules" / "solc",
    ]
    for root in candidates:
        if (root / "index.js").exists():
            return root
    return None


def _command() -> list[str] | None:
    solc = shutil.which("solc")
    if solc:
        return [solc]
    node = shutil.which("node")
    if node:
        root = _npm_solc_root()
        if root is not None:
            return [node, str(BRIDGE), str(root)]
    if shutil.which("npx"):
        return ["npx", "--yes", f"solc@{oac_genesis.SOL_VERSION}"]
    return None


def main() -> int:
    cmd = _command()
    if cmd is None:
        print(
            "no Solidity compiler found (solc, npm solc, or npx)",
            file=sys.stderr,
        )
        return 2

    payload = {
        "language": "Solidity",
        "sources": {
            "OpenAmerGenesis.sol": {"content": oac_genesis.render_contract()}
        },
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode.object"]},
            },
        },
    }
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 1

    out = json.loads(proc.stdout)
    errors = [e for e in out.get("errors", []) if e.get("severity") == "error"]
    warnings = [
        e for e in out.get("errors", []) if e.get("severity") == "warning"
    ]
    for entry in errors + warnings:
        print(entry.get("formattedMessage", str(entry)), file=sys.stderr)
    if errors:
        return 1

    artifact = None
    for sources in out.get("contracts", {}).values():
        if "OpenAmerGenesis" in sources:
            artifact = sources["OpenAmerGenesis"]
            break
    if artifact is None:
        print("the contract was not produced by the compiler", file=sys.stderr)
        return 1

    bytecode = artifact["evm"]["bytecode"]["object"]
    print(
        f"OpenAmerGenesis compiled: {len(bytecode) // 2} bytes of bytecode, "
        f"{len(artifact['abi'])} ABI entries, 0 errors, {len(warnings)} warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
