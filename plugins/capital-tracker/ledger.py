#!/usr/bin/env python3
"""OpenAmer AGI — Black-Box-Kapital-Ledger (append-only, kanonisches Ereignis).

by Amer Sacirovic

Ein einziger, append-only Datenstrom, in den alle vier Kapitel einspeisen:
Kapital (Capital), Social, Schwarm (Swarm) und Self-Coding (SelfCode).

Warum append-only JSONL:
  - kein Core-Zustand  -> kein Einfluss auf den Prompt-Cache
  - auditierbar        -> jede Zeile ist ein Ereignis mit Zeitstempel
  - leicht streambar   -> das Dashboard liest, ohne den Strom zu blockieren
  - kein Lock nötig    -> append ist auf Windows und POSIX atomar genug fuer
                          einen einzelnen Writer pro Stream

Prognose und Messung werden getrennt gefuehrt ("confidence"), damit das
Dashboard niemals Prognose als Ist verkauft.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
LEDGER_DIR = HOME / "blackbox"
LEDGER_FILE = LEDGER_DIR / "ledger.jsonl"

# Kanonische Streams
STREAM_CAPITAL = "capital"
STREAM_SOCIAL = "social"
STREAM_SWARM = "swarm"
STREAM_SELFCODE = "selfcode"
VALID_STREAMS = {STREAM_CAPITAL, STREAM_SOCIAL, STREAM_SWARM, STREAM_SELFCODE}

CONFIDENCE_MEASURED = "measured"
CONFIDENCE_PROJECTED = "projected"
VALID_CONFIDENCE = {CONFIDENCE_MEASURED, CONFIDENCE_PROJECTED}


@dataclass
class Event:
    """Ein kanonisches Ledger-Ereignis."""

    stream: str
    metric: str
    value: float
    unit: str = ""
    evidence: str = ""
    confidence: str = CONFIDENCE_MEASURED
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.stream not in VALID_STREAMS:
            raise ValueError(f"unbekannter Stream: {self.stream!r} (erlaubt: {sorted(VALID_STREAMS)})")
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"unbekannte Confidence: {self.confidence!r}")
        if not self.metric:
            raise ValueError("metric darf nicht leer sein")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class Ledger:
    """Append-only Ledger mit Snapshot-Funktion fuer das Dashboard."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else LEDGER_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ schreiben
    def append(self, event: Event) -> Event:
        event.validate()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(event.to_json() + "\n")
        return event

    def record(self, stream: str, metric: str, value: float, *,
               unit: str = "", evidence: str = "",
               confidence: str = CONFIDENCE_MEASURED,
               tags: Optional[Dict[str, Any]] = None) -> Event:
        return self.append(Event(stream=stream, metric=metric, value=float(value),
                                 unit=unit, evidence=evidence,
                                 confidence=confidence, tags=tags or {}))

    def bulk(self, events: Iterable[Event]) -> int:
        count = 0
        for event in events:
            self.append(event)
            count += 1
        return count

    # ------------------------------------------------------------- lesen
    def read(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        if limit:
            rows = rows[-limit:]
        return rows

    def snapshot(self) -> Dict[str, Any]:
        """Aggregierter Zustand fuer das Dashboard.

        Die totals-Schluessel haben die Form ``<stream>:<metric>:<confidence>`` —
        der Stream ist Teil des Schluessels, damit Dashboard und Aggregation
        dieselbe Taxonomie benutzen und sich nicht auseinanderlaufen koennen.
        """
        rows = self.read()
        by_stream: Dict[str, Dict[str, float]] = {}
        totals: Dict[str, float] = {}
        for row in rows:
            stream = row.get("stream", "?")
            metric = row.get("metric", "?")
            value = float(row.get("value", 0) or 0)
            conf = row.get("confidence", CONFIDENCE_MEASURED)
            bucket = by_stream.setdefault(stream, {})
            key = f"{stream}:{metric}:{conf}"
            bucket[key] = bucket.get(key, 0.0) + value
            totals[key] = totals.get(key, 0.0) + value
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(rows),
            "streams": by_stream,
            "totals": totals,
            "last_events": rows[-40:],
        }

    def export_json(self, target: Optional[Path] = None) -> Path:
        target = Path(target) if target else LEDGER_DIR / "snapshot.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2),
                          encoding="utf-8")
        return target

    def export_html(self, target: Optional[Path] = None) -> Path:
        from blackbox_dashboard import render_dashboard
        target = Path(target) if target else LEDGER_DIR / "black_box.html"
        target.write_text(render_dashboard(self.snapshot()), encoding="utf-8")
        return target


# ------------------------------------------------------------ Collector
class Collector:
    """Sammelt die echten Datenstroeme aus dem lokalen OpenAmer-Install.

    Jede Quelle ist optional: fehlt sie, liefert der Collector schlicht keine
    Ereignisse fuer diesen Strom. Es wird **nichts erfunden** — ein Strom ohne
    echte Quelle bleibt im Dashboard leer statt gefuellt.
    """

    def __init__(self, home: Optional[Path] = None):
        self.home = Path(home) if home else HOME
        self.ledger = Ledger()

    # ------------------------------------------- Kapital (echte Quellen)
    def collect_capital(self) -> List[Event]:
        """Liest Kapitaldaten aus den echten lokalen Quellen.

        Quellen (Reihenfolge = Prioritaet):
          1. ``asi_core/data_hub.json``       — profit/roi-Tracker (gemessen)
          2. ``asi_core/conversion_data.json`` — Conversion-Metriken
          3. ``blackbox/paypal_transactions.json`` — reale PayPal-Zahlungen
          4. ``<repo>/Black Box/Financial-Tracking/**/*.json`` — Finanzprotokoll

        Trennt streng zwischen gemessenen Werten (measured) und Prognosen
        (projected) — das Dashboard darf Prognose nie als Ist ausweisen.
        """
        events: List[Event] = []

        # 1) data_hub.json: der zentrale Kapital-Tracker der lokalen Instanz
        hub_path = self.home / "asi_core" / "data_hub.json"
        if hub_path.exists():
            try:
                hub = json.loads(hub_path.read_text(encoding="utf-8"))
            except Exception:
                hub = None
            if isinstance(hub, dict):
                for section, payload in hub.items():
                    if not isinstance(payload, dict):
                        continue
                    for metric, value in payload.items():
                        if not isinstance(value, (int, float)):
                            continue
                        conf = (CONFIDENCE_PROJECTED
                                if "projection" in str(metric).lower()
                                or "forecast" in str(metric).lower()
                                or "projected" in str(metric).lower()
                                else CONFIDENCE_MEASURED)
                        events.append(Event(
                            stream=STREAM_CAPITAL, metric=f"{section}.{metric}",
                            value=float(value), unit="",
                            evidence="asi_core/data_hub.json",
                            confidence=conf,
                            tags={"section": section, "metric": metric}))

        # 2) conversion_data.json: Conversion-Metriken + Projektionen
        tracker_data = self.home / "asi_core" / "conversion_data.json"
        if tracker_data.exists():
            try:
                data = json.loads(tracker_data.read_text(encoding="utf-8"))
            except Exception:
                data = None
            if isinstance(data, dict):
                for metric, value in (data.get("metrics") or {}).items():
                    try:
                        events.append(Event(
                            stream=STREAM_CAPITAL, metric=str(metric),
                            value=float(value), unit="EUR",
                            evidence="asi_core/conversion_data.json",
                            confidence=CONFIDENCE_MEASURED))
                    except (TypeError, ValueError):
                        continue
                for metric, value in (data.get("projections") or {}).items():
                    try:
                        events.append(Event(
                            stream=STREAM_CAPITAL, metric=str(metric),
                            value=float(value), unit="EUR",
                            evidence="asi_core/conversion_data.json (projection)",
                            confidence=CONFIDENCE_PROJECTED))
                    except (TypeError, ValueError):
                        continue

        # 3) Reale PayPal-Transaktionen (gemessen, kein Forecast)
        events.extend(self._collect_paypal_transactions())

        # 4) Black Box Financial-Tracking (lokale Instanz)
        bb_root = self.home.parent.parent / "openamer-max" / "Black Box" / "Financial-Tracking"
        if bb_root.is_dir():
            for path in sorted(bb_root.rglob("*.json"))[:20]:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if isinstance(data, dict):
                    for metric, value in list(data.items())[:10]:
                        if isinstance(value, (int, float)):
                            events.append(Event(
                                stream=STREAM_CAPITAL, metric=str(metric),
                                value=float(value), unit="EUR",
                                evidence=str(path.name),
                                confidence=CONFIDENCE_MEASURED))
        return events

    def _collect_paypal_transactions(self) -> List[Event]:
        """Liest echte PayPal-Zahlungen aus dem lokalen Transaktionsjournal.

        Format (JSONL oder JSON-Liste), je Zeile ein Feld ``amount`` in EUR
        sowie optional ``status``/``date``/``currency``. Nur abgeschlossene
        Zahlungen zaehlen als gemessenes Kapital.
        """
        events: List[Event] = []
        journal = LEDGER_DIR / "paypal_transactions.jsonl"
        if not journal.exists():
            return events
        rows: List[Dict[str, Any]] = []
        try:
            text = journal.read_text(encoding="utf-8")
        except Exception:
            return events
        stripped = text.strip()
        if not stripped:
            return events
        if stripped.startswith("["):
            try:
                rows = json.loads(stripped)
            except Exception:
                rows = []
        else:
            for line in stripped.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw = row.get("amount")
            if raw is None:
                continue
            try:
                amount = float(str(raw).replace(",", "."))
            except (TypeError, ValueError):
                continue
            status = str(row.get("status", "completed")).lower()
            if status not in {"completed", "complete", "success", "succeeded", "paid"}:
                continue
            events.append(Event(
                stream=STREAM_CAPITAL, metric="paypal.revenue",
                value=amount, unit=str(row.get("currency", "EUR")),
                evidence="blackbox/paypal_transactions.jsonl",
                confidence=CONFIDENCE_MEASURED,
                tags={"status": status, "date": str(row.get("date", ""))}))
        return events

    # ------------------------------------------- Social (echte Quellen)
    def collect_platform_status(self) -> List[Event]:
        """Liest asi_core/system_status.json (Plattform-Status)."""
        events: List[Event] = []
        path = self.home / "asi_core" / "system_status.json"
        if not path.exists():
            return events
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return events
        status = data.get("platform_status", {}) or {}
        for platform, accounts in status.items():
            for handle, state in (accounts or {}).items():
                events.append(Event(
                    stream=STREAM_SOCIAL, metric="platform_status",
                    value=1.0, unit="ready" if state == "Ready" else "down",
                    evidence=f"asi_core/system_status.json:{platform}/{handle}",
                    tags={"platform": platform, "handle": handle, "state": state},
                ))
        return events

    def collect_social_posts(self) -> List[Event]:
        """Liest veroeffentlichte Posts aus dem Social-Journal.

        Erwartet ``blackbox/social_posts.jsonl`` mit je Zeile ``platform``,
        ``post_id`` und optional ``views``/``likes``/``reach``. Das Journal
        wird von den Plattform-Adaptern geschrieben (siehe ``_social_base``).
        """
        events: List[Event] = []
        journal = LEDGER_DIR / "social_posts.jsonl"
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
            for metric in ("views", "likes", "reach", "followers"):
                if metric in row and isinstance(row[metric], (int, float)):
                    events.append(Event(
                        stream=STREAM_SOCIAL, metric=f"{platform}.{metric}",
                        value=float(row[metric]), unit=str(row.get("unit", "count")),
                        evidence=f"blackbox/social_posts.jsonl:{platform}",
                        tags={"platform": platform, "post_id": str(row.get("post_id", ""))}))
        return events

    # ------------------------------------------- Schwarm (echte Quellen)
    def collect_cron(self) -> List[Event]:
        """Zaehlt Cron-Ausfuehrungen und ihre Ergebnisse."""
        events: List[Event] = []
        cron_dir = self.home / "cron"
        if not cron_dir.is_dir():
            return events
        out = cron_dir / "output"
        if not out.is_dir():
            return events
        for item in sorted(out.iterdir(), key=lambda p: p.stat().st_mtime)[-30:]:
            try:
                age_h = (time.time() - item.stat().st_mtime) / 3600
            except OSError:
                continue
            events.append(Event(
                stream=STREAM_SWARM, metric="cron_output",
                value=1.0, unit="run",
                evidence=f"cron/output/{item.name}",
                tags={"age_hours": round(age_h, 2)},
            ))
        return events

    def collect_swarm_queue(self) -> List[Event]:
        """Liest die persistente Schwarm-Queue (swarm/scheduler.py)."""
        events: List[Event] = []
        queue = self.home / "swarm" / "queue.json"
        if not queue.exists():
            return events
        try:
            data = json.loads(queue.read_text(encoding="utf-8"))
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

    # ------------------------------------- Self-Coding (echte Quellen)
    def collect_skills(self) -> List[Event]:
        """Zaehlt installierte Skills je Kategorie."""
        events: List[Event] = []
        skills_dir = self.home / "skills"
        if not skills_dir.is_dir():
            return events
        counts: Dict[str, int] = {}
        for path in skills_dir.rglob("SKILL.md"):
            rel = path.relative_to(skills_dir)
            category = rel.parts[0] if len(rel.parts) > 1 else "_root"
            counts[category] = counts.get(category, 0) + 1
        for category, count in counts.items():
            events.append(Event(
                stream=STREAM_SELFCODE, metric="skills_installed",
                value=float(count), unit="skills",
                evidence=f"skills/{category}",
                tags={"category": category},
            ))
        return events

    def collect_error_patterns(self) -> List[Event]:
        """Analysiert ``logs/errors.log`` — der Input fuer den Self-Coder."""
        events: List[Event] = []
        err_log = self.home / "logs" / "errors.log"
        if not err_log.exists():
            return events
        try:
            text = err_log.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return events
        patterns: Dict[str, int] = {}
        for line in text.splitlines():
            m = re.search(r"\b(WARNING|ERROR|CRITICAL)\b", line)
            if not m:
                continue
            key = m.group(1).lower()
            patterns[key] = patterns.get(key, 0) + 1
        for level, count in patterns.items():
            events.append(Event(
                stream=STREAM_SELFCODE, metric="log_patterns",
                value=float(count), unit="occurrences",
                evidence="logs/errors.log",
                tags={"level": level}))
        return events

    def collect_all(self) -> List[Event]:
        return (self.collect_capital() + self.collect_platform_status()
                + self.collect_social_posts() + self.collect_cron()
                + self.collect_swarm_queue() + self.collect_skills()
                + self.collect_error_patterns())


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Black-Box-Ledger")
    parser.add_argument("--collect", action="store_true", help="Datenstroeme einsammeln")
    parser.add_argument("--snapshot", action="store_true", help="Snapshot schreiben")
    parser.add_argument("--html", action="store_true", help="HTML-Dashboard schreiben")
    parser.add_argument("--tail", type=int, default=0, help="letzte N Ereignisse zeigen")
    args = parser.parse_args()

    collector = Collector()
    if args.collect:
        events = collector.collect_all()
        collector.ledger.bulk(events)
        print(f"{len(events)} Ereignisse in {collector.ledger.path} geschrieben")
    if args.snapshot:
        path = collector.ledger.export_json()
        print(f"Snapshot: {path}")
    if args.html:
        path = collector.ledger.export_html()
        print(f"Dashboard: {path}")
    if args.tail:
        for row in collector.ledger.read(limit=args.tail):
            print(f"  {row.get('ts')}  {row.get('stream'):9s} {row.get('metric'):20s} "
                  f"{row.get('value')} {row.get('unit','')}")
    if not any([args.collect, args.snapshot, args.html, args.tail]):
        print(f"Ledger: {collector.ledger.path}")
        print(f"Ereignisse: {len(collector.ledger.read())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
