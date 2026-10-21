#!/usr/bin/env python3
"""OpenAmer AGI — Autonomer Tick-Runner (Schwarm + Self-Coding + Kapital).

by Amer Sacirovic

Dies ist der **Taktgeber** der Autonomie. Er ruft in festen Intervallen:

  1. Schwarm-Scheduler   — startklaere Tasks claimen, Abhaengigkeiten aufloesen
  2. Self-Coder-Analyse  — die erlaubten Pfade auf Verbesserungs-Kandidaten pruefen
  3. Black-Box-Collector  — alle vier Datenstroeme ins Ledger schreiben
  4. Social-Metriken     — optional (erfordert Chrome mit Originalprofil)

Der Runner ist **fail-safe**: ein fehlgeschlagener Schritt stoppt den Rest
nicht, sondern wird protokolliert. Genau das ist der Unterschied zwischen
"der Agent laeuft" und "der Agent laeuft und kann nicht daran sterben".

Aufruf:

    python tick_runner.py --once         # ein Tick
    python tick_runner.py --interval 300  # Dauerloop (fuer den Cron/Heartbeat)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
MIRROR = HERE.parent.parent
HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
STATE_DIR = HOME / "swarm"
TICK_LOG = STATE_DIR / "ticks.jsonl"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MIRROR / "swarm"))
sys.path.insert(0, str(MIRROR / "selfcode"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def record(step: str, ok: bool, detail: Any = None) -> None:
    """Schreibt das Tick-Ergebnis ins Tick-Journal (append-only)."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with TICK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "step": step, "ok": ok,
                                 "detail": detail}, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ------------------------------------------------------------ 1) Schwarm
def tick_swarm() -> Dict[str, Any]:
    """Schwarm-Scheduler ticken: startklaere Tasks claimen und starten."""
    try:
        from scheduler import SwarmScheduler, ledger_hook  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"scheduler nicht ladbar: {exc}"}

    try:
        sched = SwarmScheduler()
        ready = sched.ready_tasks()
        claimed = sched.claim()
        sched.write_state()
        for task in claimed:
            ledger_hook({"metric": "task_claimed", "value": 1,
                         "evidence": f"swarm/{task.title}"})
        stats = sched.stats()
        return {"ok": True, "ready": len(ready), "claimed": len(claimed),
                "stats": stats}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------- 2) Self-Coding
def tick_selfcode() -> Dict[str, Any]:
    """Self-Coder-Analyse: erlaubte Pfade statisch pruefen.

    Der Self-Coder veraendert hier **nichts** — der Tick meldet nur
    Verbesserungs-Kandidaten. Aenderungen bleiben eine bewusste, verifizierte
    Aktion (siehe ``selfcode/self_coder.py --apply``), nie ein Nebeneffekt
    eines Hintergrund-Ticks.
    """
    try:
        from self_coder import SelfCoder  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"self_coder nicht ladbar: {exc}"}

    try:
        coder = SelfCoder(root=MIRROR)
        candidates: List[Dict[str, Any]] = []
        for rel in ("scripts/generate-docs.py", "scripts/code-review-check.py",
                    "swarm/scheduler.py", "selfcode/self_coder.py"):
            try:
                report = coder.analyze_python(rel)
                if report.get("issues"):
                    candidates.append({"path": rel, "issues": report["issues"]})
            except Exception:
                continue
        return {"ok": True, "candidates": len(candidates), "detail": candidates[:5]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ----------------------------------------------------------- 3) Kapital
def tick_collector() -> Dict[str, Any]:
    """Alle vier Datenstroeme ins Ledger schreiben."""
    try:
        from collect import run_once  # type: ignore
        summary = run_once()
        return {"ok": True, **summary}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ------------------------------------------------------------ 4) Social
def tick_social(enabled: bool = True) -> Dict[str, Any]:
    """Plattformmetriken live lesen (benoetigt Chrome mit Originalprofil)."""
    if not enabled:
        return {"ok": True, "skipped": "social deaktiviert"}
    try:
        from collect_social import collect, write_journal  # type: ignore
        rows = collect()
        write_journal(rows)
        metrics = [r for r in rows if r.get("metric")]
        return {"ok": True, "rows": len(rows), "metrics": len(metrics)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ----------------------------------------------------------------- Tick
def run_tick(with_social: bool = True) -> Dict[str, Any]:
    """Ein vollstaendiger Tick. Fehler in einem Schritt stoppen die anderen nicht."""
    results: Dict[str, Any] = {"ts": _now()}
    for name, fn in (("swarm", tick_swarm),
                     ("selfcode", tick_selfcode),
                     ("collector", tick_collector),
                     ("social", lambda: tick_social(with_social))):
        res = fn()
        results[name] = res
        record(name, bool(res.get("ok")), res)
        log(f"{name:10s} {'OK ' if res.get('ok') else 'ERR'} "
            f"{json.dumps({k: v for k, v in res.items() if k != 'ok'}, ensure_ascii=False)[:150]}")
    return results


def serve(interval: int = 300, with_social: bool = True) -> int:
    log(f"Tick-Loop: alle {interval}s (Abbruch mit Strg+C)")
    while True:
        try:
            run_tick(with_social)
        except Exception as exc:  # noqa: BLE001
            log(f"TICK-FEHLER: {type(exc).__name__}: {exc}")
        time.sleep(interval)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer autonomer Tick-Runner")
    parser.add_argument("--once", action="store_true", help="ein einzelner Tick")
    parser.add_argument("--interval", type=int, default=300, help="Intervall in Sekunden")
    parser.add_argument("--no-social", action="store_true", help="Social-Metriken ueberspringen")
    args = parser.parse_args()

    if args.once:
        result = run_tick(not args.no_social)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    return serve(args.interval, not args.no_social)


if __name__ == "__main__":
    raise SystemExit(main())
