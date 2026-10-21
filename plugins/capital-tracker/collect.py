#!/usr/bin/env python3
"""OpenAmer AGI — Integrierter Collector: speist alle vier Datenstroeme.

by Amer Sacirovic

Dieses Modul ist das Bindeglied zwischen den vier Kapiteln und dem
Black-Box-Dashboard. Es zieht die Daten aus den **echten** lokalen Quellen
und schreibt sie in das kanonische Ledger.

Wichtig: der Collector erfindet nichts. Jeder Strom, dessen Quelle fehlt,
bleibt im Dashboard leer. Ein Strom mit echten Werten ist ein
Arbeitsnachweis; ein Strom mit erfundenen Werten waere Werbung.

Aufruf:

    python collect.py            # einmal einsammeln
    python collect.py --serve    # zyklisch (fuer den Heartbeat)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
MIRROR = HERE.parent.parent
HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))

sys.path.insert(0, str(HERE))

from ledger import (  # noqa: E402
    CONFIDENCE_MEASURED,
    STREAM_CAPITAL,
    STREAM_SOCIAL,
    STREAM_SWARM,
    STREAM_SELFCODE,
    Collector,
    Event,
    Ledger,
)


# ------------------------------------------------------------------ Schwarm
def collect_swarm_events(scheduler_module=None) -> List[Event]:
    """Liest die echte Schwarm-Queue und meldet Task-Statistik.

    Der Scheduler liegt im Mirror unter ``swarm/scheduler.py``. Fehlt er,
    bleibt der Schwarm-Stream leer — er wird nicht simuliert.
    """
    events: List[Event] = []
    queue_file = HOME / "swarm" / "queue.json"
    if not queue_file.exists():
        return events

    try:
        data = json.loads(queue_file.read_text(encoding="utf-8"))
    except Exception:
        return events

    tasks = data.get("tasks", data) if isinstance(data, dict) else data
    if not isinstance(tasks, list):
        return events

    counts: Dict[str, int] = {}
    for task in tasks:
        if isinstance(task, dict):
            status = str(task.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
    for status, count in counts.items():
        events.append(Event(
            stream=STREAM_SWARM, metric="task_status",
            value=float(count), unit="tasks",
            evidence="swarm/queue.json",
            tags={"status": status}))
    return events


# ------------------------------------------------------- Social (Journal)
def collect_social_events() -> List[Event]:
    """Liest das Platform-Metriken-Journal (``social/platform_metrics.jsonl``).

    Geschrieben von ``collect_social.py`` (echte Werte aus dem eingeloggten
    Chrome via CDP). Nur Zeilen mit ``metric``+``value`` werden zu Ereignissen
    — Fehlmeldungen (z. B. "nicht eingeloggt") werden als Ereignis mit Wert 0
    und passendem Tag protokolliert, damit der Zustand sichtbar ist.
    """
    events: List[Event] = []
    journal = HOME / "social" / "platform_metrics.jsonl"
    if not journal.exists():
        return events
    try:
        text = journal.read_text(encoding="utf-8")
    except Exception:
        return events
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        platform = str(row.get("platform", "unknown"))
        if row.get("metric") and isinstance(row.get("value"), (int, float)):
            events.append(Event(
                stream=STREAM_SOCIAL, metric=f"{platform}.{row['metric']}",
                value=float(row["value"]), unit=str(row.get("unit", "count")),
                evidence="social/platform_metrics.jsonl",
                tags={"platform": platform,
                      "collected_at": str(row.get("collected_at", ""))}))
        elif row.get("ok") is False:
            events.append(Event(
                stream=STREAM_SOCIAL, metric=f"{platform}.reachable",
                value=0.0, unit="bool",
                evidence="social/platform_metrics.jsonl",
                tags={"platform": platform,
                      "error": str(row.get("error", ""))[:200]}))
    return events


# --------------------------------------------------- Self-Coding (Analyse)
def collect_selfcode_events() -> List[Event]:
    """Meldet den Self-Coder-Stand: analysierbare Dateien + Log-Muster.

    Die eigentliche Code-Verbesserung laeuft ueber ``selfcode/self_coder.py``;
    dieser Collector meldet nur den *Zustand* (wie viele Dateien liegen im
    erlaubten Bereich, wie viele Log-Muster liegen an).
    """
    events: List[Event] = []
    coder = MIRROR / "selfcode" / "self_coder.py"
    if coder.exists():
        try:
            source = coder.read_text(encoding="utf-8")
            events.append(Event(
                stream=STREAM_SELFCODE, metric="selfcoder_available",
                value=1.0, unit="active",
                evidence="selfcode/self_coder.py",
                tags={"size_bytes": len(source)}))
        except Exception:
            pass

    scheduler = MIRROR / "swarm" / "scheduler.py"
    if scheduler.exists():
        events.append(Event(
            stream=STREAM_SELFCODE, metric="swarm_scheduler_available",
            value=1.0, unit="active",
            evidence="swarm/scheduler.py"))
    return events


# ------------------------------------------------------- Kapital (PayPal)
def collect_capital_events() -> List[Event]:
    """Kapital aus den echten lokalen Quellen (siehe Collector.collect_capital)."""
    return Collector(HOME).collect_capital()


# ----------------------------------------------------------------- Orchestrierung
def collect_all() -> List[Event]:
    """Sammelt alle vier Stroeme ein. Reihenfolge = Ausgabe-Reihenfolge."""
    return (collect_capital_events()
            + collect_social_events()
            + collect_swarm_events()
            + collect_selfcode_events()
            + Collector(HOME).collect_skills()
            + Collector(HOME).collect_error_patterns())


def run_once(ledger: Optional[Ledger] = None) -> Dict[str, Any]:
    """Einmal einsammeln und den Snapshot aktualisieren."""
    ledger = ledger or Ledger()
    events = collect_all()
    ledger.bulk(events)
    snapshot = ledger.export_json()
    summary = {
        "events": len(events),
        "ledger": str(ledger.path),
        "snapshot": str(snapshot),
        "streams": sorted({e.stream for e in events}),
    }
    return summary


def serve(interval: int = 300) -> int:
    """Zyklich einsammeln — der Heartbeat ruft das alle ``interval`` Sekunden."""
    ledger = Ledger()
    print(f"Collector-Loop: alle {interval}s (Abbruch mit Strg+C)")
    while True:
        try:
            summary = run_once(ledger)
            print(f"  {summary['events']} Ereignisse | Streams: "
                  f"{', '.join(summary['streams']) or '—'}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FEHLER: {type(exc).__name__}: {exc}")
        time.sleep(interval)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Black-Box-Collector")
    parser.add_argument("--serve", action="store_true", help="zyklisch einsammeln")
    parser.add_argument("--interval", type=int, default=300, help="Intervall in Sekunden")
    args = parser.parse_args()

    if args.serve:
        return serve(args.interval)
    summary = run_once()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
