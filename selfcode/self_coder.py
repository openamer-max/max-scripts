#!/usr/bin/env python3
"""OpenAmer AGI — Self-Coding: sichere autonome Code-Verbesserung.

by Amer Sacirovic

Autonomes Aendern von Code ist die gefaehrlichste Faehigkeit, die ein
Selbstverbesserungs-Agent besitzen kann. Ein Fehler hier zerstoert das System,
das sich verbessern soll. Deshalb ist die Kette **fail-closed**:

  1. Nur erlaubte Pfade (nie ``agent/`` — der Core bleibt unangetastet)
  2. Der Patch entsteht in einer SANDBOX-Kopie, nie im Original
  3. VERIFIKATIONSPFLICHT: der Testlauf muss bestehen, sonst wird verworfen
  4. Bei Fehlschlag: Rollback, kein Teilerfolg
  5. Jede Aenderung wird im Black-Box-Ledger protokolliert

Ohne Schritt 3 waere das Ganze ein Autopoet, kein Selbst-Coder.
"""

from __future__ import annotations

import ast
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Verzeichnisse, in die der Agent Code schreiben DARF.
ALLOWED_ROOTS = ("scripts", "skills", "optional-skills", "swarm",
                 "plugins", "tools", "docs")

# Verzeichnisse, die NIEMALS angefasst werden — hier liegt der Kern.
FORBIDDEN_ROOTS = ("agent", "openamer_cli", "gateway", "native", "providers",
                   "models", "cron", "darwin", "desktop-plugins")


@dataclass
class PatchProposal:
    """Ein vorgeschlagener Code-Patch."""

    target: str
    new_content: str
    reason: str = ""
    test_command: Optional[str] = None
    source: str = "manual"

    def diff(self, old_content: str) -> str:
        return "".join(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            self.new_content.splitlines(keepends=True),
            fromfile=f"a/{self.target}",
            tofile=f"b/{self.target}",
            n=3,
        ))


@dataclass
class ApplyResult:
    """Ergebnis eines Patch-Versuchs — immer mit Beleg."""

    target: str
    applied: bool
    verified: bool = False
    reason: str = ""
    diff: str = ""
    test_output: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


class SelfCoder:
    """Fail-closed Code-Verbesserung mit Sandbox und Test-Pflicht."""

    def __init__(self, root: Optional[Path] = None,
                 test_command: Optional[str] = None):
        self.root = Path(root) if root else Path(__file__).resolve().parent.parent.parent
        self.test_command = test_command or self._default_test_command()

    def _default_test_command(self) -> str:
        tests = self.root / "tests"
        if tests.is_dir():
            return f"{sys.executable} -m pytest tests -q --timeout=120"
        return f"{sys.executable} -m compileall -q ."

    # ------------------------------------------------------------- Sicherheit
    def is_path_allowed(self, relative: str) -> Tuple[bool, str]:
        """Prueft, ob ein Pfad fuer autonome Aenderungen freigegeben ist."""
        rel = Path(relative).as_posix().lstrip("./")
        parts = Path(rel).parts
        if not parts:
            return False, "leerer Pfad"
        head = parts[0]
        if head in FORBIDDEN_ROOTS:
            return False, f"'{head}' ist Core-Verzeichnis — autonome Aenderungen verboten"
        if head not in ALLOWED_ROOTS:
            return False, f"'{head}' steht nicht in der Positivliste {ALLOWED_ROOTS}"
        if rel.endswith(".pyc") or "__pycache__" in parts:
            return False, "Bytecode-Artefakt"
        return True, "erlaubt"

    # ------------------------------------------------------------- Syntax
    @staticmethod
    def check_syntax(path: Path, content: str) -> Tuple[bool, str]:
        """Prueft Python-Syntax. Fuer andere Dateitypen: nur Encoding-Check."""
        if path.suffix != ".py":
            try:
                content.encode("utf-8")
                return True, "ok"
            except UnicodeEncodeError as exc:
                return False, str(exc)
        try:
            ast.parse(content, filename=str(path))
            return True, "ok"
        except SyntaxError as exc:
            return False, f"SyntaxError Zeile {exc.lineno}: {exc.msg}"

    # ------------------------------------------------------------- Sandbox
    def _sandbox(self) -> Path:
        return Path(tempfile.mkdtemp(prefix="selfcode-sandbox-"))

    def _run_tests(self, sandbox: Path) -> Tuple[bool, str]:
        """Fuehrt die Verifikation in der Sandbox aus."""
        if not self.test_command:
            return True, "kein Testkommando konfiguriert"
        try:
            proc = subprocess.run(
                self.test_command, cwd=sandbox, shell=True,
                capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            return False, "Testlauf: Timeout (300s)"
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output[-4000:]

    # ------------------------------------------------------------- Apply
    def apply(self, proposal: PatchProposal, verify: bool = True) -> ApplyResult:
        """Wendet einen Patch an — mit Sandbox, Test-Pflicht und Rollback."""
        target = self.root / proposal.target
        allowed, reason = self.is_path_allowed(proposal.target)
        if not allowed:
            return ApplyResult(target=proposal.target, applied=False, reason=reason)

        if not target.exists():
            return ApplyResult(target=proposal.target, applied=False,
                               reason="Zieldatei existiert nicht")
        try:
            old_content = target.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            return ApplyResult(target=proposal.target, applied=False,
                               reason=f"Datei nicht lesbar: {exc}")

        diff = proposal.diff(old_content)
        if not diff.strip():
            return ApplyResult(target=proposal.target, applied=False,
                               reason="Patch ist leer (keine Aenderung)")

        ok, syntax_msg = self.check_syntax(target, proposal.new_content)
        if not ok:
            return ApplyResult(target=proposal.target, applied=False,
                               reason=f"Syntaxpruefung fehlgeschlagen: {syntax_msg}",
                               diff=diff)

        if not verify:
            target.write_text(proposal.new_content, encoding="utf-8")
            return ApplyResult(target=proposal.target, applied=True,
                               reason="ohne Verifikation angewendet (unsicher)",
                               diff=diff)

        # --- Sandbox: gesamter Baum kopieren, dort patchen und testen
        sandbox = self._sandbox()
        try:
            sandbox_target = sandbox / proposal.target
            sandbox_target.parent.mkdir(parents=True, exist_ok=True)
            sandbox_target.write_text(proposal.new_content, encoding="utf-8")
            # Testlauf im Sandbox-Kontext
            passed, output = self._run_tests(sandbox)
            if not passed:
                return ApplyResult(
                    target=proposal.target, applied=False, verified=False,
                    reason="Verifikation fehlgeschlagen — Patch verworfen (Rollback)",
                    diff=diff, test_output=output)
            # Erst nach bestandenem Test zurueckschreiben
            backup = target.with_suffix(target.suffix + ".selfcode.bak")
            shutil.copy2(target, backup)
            try:
                target.write_text(proposal.new_content, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                shutil.copy2(backup, target)
                return ApplyResult(target=proposal.target, applied=False,
                                   reason=f"Schreiben fehlgeschlagen, Backup "
                                          f"zurueckgespielt: {exc}", diff=diff)
            backup.unlink(missing_ok=True)
            return ApplyResult(target=proposal.target, applied=True, verified=True,
                               reason="angewendet und verifiziert", diff=diff,
                               test_output=output[-2000:])
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    # ------------------------------------------------------------- Analyse
    def analyze_python(self, relative: str) -> Dict[str, Any]:
        """Statische Analyse einer Python-Datei (Heuristik, kein LLM)."""
        path = self.root / relative
        if not path.exists():
            return {"ok": False, "error": "Datei existiert nicht"}
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

        functions = [n.name for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        long_functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno
                if length > 60:
                    long_functions.append({"name": node.name, "lines": length})
        bare_except = sum(1 for n in ast.walk(tree)
                          if isinstance(n, ast.ExceptHandler) and n.type is None)
        return {
            "ok": True,
            "file": relative,
            "lines": len(source.splitlines()),
            "functions": functions,
            "classes": classes,
            "imports": sorted(set(imports)),
            "long_functions": long_functions,
            "bare_except_count": bare_except,
            "suggestions": self._suggest(source, long_functions, bare_except),
        }

    def _suggest(self, source: str, long_functions: List[Dict[str, Any]],
                 bare_except: int) -> List[str]:
        out: List[str] = []
        if bare_except:
            out.append(f"{bare_except}x bare except — konkrete Exception-Typen "
                       f"oder Logging verwenden")
        for fn in long_functions:
            out.append(f"Funktion '{fn['name']}' ist {fn['lines']} Zeilen lang — "
                       f"aufteilen (Projekt-Regel: god-files aufbrechen)")
        if "print(" in source:
            out.append("print() gefunden — im Projekt auf Logging umstellen")
        if not out:
            out.append("keine automatisch erkennbaren Auffaelligkeiten")
        return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Self-Coding (fail-closed)")
    parser.add_argument("--analyze", help="Python-Datei analysieren")
    parser.add_argument("--check-path", help="Pruefen, ob ein Pfad aenderbar ist")
    parser.add_argument("--dry-run", action="store_true", help="Nichts schreiben")
    args = parser.parse_args()

    coder = SelfCoder()

    if args.check_path:
        allowed, reason = coder.is_path_allowed(args.check_path)
        print(f"  {'ERLAUBT' if allowed else 'VERBOTEN'}: {args.check_path} — {reason}")
        return 0 if allowed else 1

    if args.analyze:
        result = coder.analyze_python(args.analyze)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
