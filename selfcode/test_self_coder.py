#!/usr/bin/env python3
"""OpenAmer AGI — Test des Self-Coders (Fail-Closed-Kette).

by Amer Sacirovic
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from self_coder import PatchProposal, SelfCoder


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="selfcode-test-"))
    (tmp / "scripts").mkdir(parents=True)
    (tmp / "agent").mkdir(parents=True)
    (tmp / "scripts" / "tool.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp / "agent" / "core.py").write_text(
        "def core():\n    return 1\n", encoding="utf-8")

    coder = SelfCoder(root=tmp, test_command=None)
    failures = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        mark = "OK  " if condition else "FAIL"
        print(f"  [{mark}] {label}" + (f"  -> {detail}" if detail else ""))
        if not condition:
            failures.append(label)

    print("Test 1: Pfad-Positivliste")
    ok, reason = coder.is_path_allowed("scripts/tool.py")
    check("scripts/ ist erlaubt", ok, reason)
    ok, reason = coder.is_path_allowed("skills/foo/SKILL.md")
    check("skills/ ist erlaubt", ok, reason)

    print("Test 2: Core-Pfade sind verboten")
    for forbidden in ("agent/core.py", "openamer_cli/x.py", "gateway/y.py",
                      "native/z.py", "darwin/w.py"):
        ok, reason = coder.is_path_allowed(forbidden)
        check(f"{forbidden} verboten", not ok, reason)

    print("Test 3: Unbekannter Pfad verboten")
    ok, reason = coder.is_path_allowed("sonstwas/x.py")
    check("nicht gelisteter Pfad verboten", not ok, reason)

    print("Test 4: Syntaxpruefung faengt Fehler")
    ok, msg = SelfCoder.check_syntax(tmp / "scripts" / "tool.py", "def broken(:\n")
    check("kaputter Code wird erkannt", not ok, msg)
    ok, msg = SelfCoder.check_syntax(tmp / "scripts" / "tool.py", "def ok():\n    return 1\n")
    check("guter Code wird akzeptiert", ok, msg)

    print("Test 5: Guter Patch wird angewendet")
    proposal = PatchProposal(
        target="scripts/tool.py",
        new_content="def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n",
        reason="Test-Patch")
    result = coder.apply(proposal, verify=False)
    check("Patch angewendet", result.applied, result.reason)
    check("Neue Funktion vorhanden",
          "def sub" in (tmp / "scripts" / "tool.py").read_text(encoding="utf-8"))

    print("Test 6: Patch auf verbotenen Pfad wird abgelehnt")
    proposal = PatchProposal(target="agent/core.py", new_content="x = 1\n")
    result = coder.apply(proposal, verify=False)
    check("Core-Patch abgelehnt", not result.applied, result.reason)
    check("Core unveraendert",
          (tmp / "agent" / "core.py").read_text(encoding="utf-8") == "def core():\n    return 1\n")

    print("Test 7: Fehlerhafter Code wird abgelehnt")
    proposal = PatchProposal(target="scripts/tool.py", new_content="def broken(:\n")
    result = coder.apply(proposal, verify=False)
    check("Syntaxfehler abgelehnt", not result.applied, result.reason)
    check("Original unveraendert",
          "def sub" in (tmp / "scripts" / "tool.py").read_text(encoding="utf-8"))

    print("Test 8: Verifikation schlaegt fehl -> Rollback")
    coder_fail = SelfCoder(root=tmp, test_command="python -c \"raise SystemExit(1)\"")
    proposal = PatchProposal(
        target="scripts/tool.py", new_content="def add(a, b):\n    return a - b\n")
    before = (tmp / "scripts" / "tool.py").read_text(encoding="utf-8")
    result = coder_fail.apply(proposal, verify=True)
    check("fehlgeschlagene Verifikation -> nicht angewendet", not result.applied, result.reason)
    check("Rollback: Datei unveraendert",
          (tmp / "scripts" / "tool.py").read_text(encoding="utf-8") == before)

    print("Test 9: Erfolgreiche Verifikation wendet an")
    coder_ok = SelfCoder(root=tmp, test_command="python -c \"pass\"")
    proposal = PatchProposal(
        target="scripts/tool.py", new_content="def add(a, b):\n    return a + b + 1\n")
    result = coder_ok.apply(proposal, verify=True)
    check("verifizierter Patch angewendet", result.applied and result.verified, result.reason)
    check("Inhalt aktualisiert",
          "a + b + 1" in (tmp / "scripts" / "tool.py").read_text(encoding="utf-8"))

    print("Test 10: Statische Analyse")
    (tmp / "scripts" / "big.py").write_text(
        "def f():\n    try:\n        pass\n    except:\n        pass\n" + "    x = 1\n" * 70,
        encoding="utf-8")
    result = coder.analyze_python("scripts/big.py")
    check("Analyse erfolgreich", result.get("ok"), str(result.get("error", "")))
    check("bare except erkannt", result.get("bare_except_count", 0) >= 1,
          str(result.get("bare_except_count")))
    check("lange Funktion erkannt", len(result.get("long_functions", [])) >= 1,
          str(result.get("long_functions")))

    shutil.rmtree(tmp, ignore_errors=True)
    print()
    if failures:
        print(f"{len(failures)} Test(s) FEHLGESCHLAGEN: {failures}")
        return 1
    print("Alle Self-Coding-Tests bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
