#!/usr/bin/env python3
"""OpenAmer AGI — Schwarm-Scheduler (Heartbeat-getrieben, resumable).

by Amer Sacirovic

Warum ein eigener Scheduler statt Session-getriebener Delegation:
  ``delegate_task`` laeuft innerhalb einer Session und stirbt mit ihr. Der
  Nutzer-Zweck ist aber *parallele Workflows ohne Eingriff* — also ueber
  Session-Grenzen hinweg. Das Board (Kanban) ist die persistente Ebene;
  dieser Scheduler ist die Ausfuehrungsebene darueber.

Kernregeln:
  - Ein Task wandert nur vorwaerts: ready -> running -> done/blocked
  - Abhaengigkeiten (``parents``) werden respektiert: ein Task startet erst,
    wenn alle Eltern erledigt sind
  - Jeder Zustandswechsel wird im Black-Box-Ledger protokolliert
  - Fail-Closed: ein Worker-Crash blockiert den Task, er verschwindet nicht
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
SWARM_DIR = HOME / "swarm"
QUEUE_FILE = SWARM_DIR / "queue.json"
STATE_FILE = SWARM_DIR / "state.json"

STATUS_QUEUED = "queued"
STATUS_READY = "ready"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_BLOCKED = "blocked"

MAX_PARALLEL = 3


@dataclass
class SwarmTask:
    """Ein Arbeitstask im Schwarm."""

    title: str
    assignee: str
    body: str = ""
    parents: List[str] = field(default_factory=list)
    priority: int = 0
    status: str = STATUS_QUEUED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class SwarmScheduler:
    """Persistente, resumable Task-Queue mit Abhaengigkeits-Aufloesung."""

    def __init__(self, queue_file: Optional[Path] = None,
                 state_file: Optional[Path] = None):
        self.queue_file = Path(queue_file) if queue_file else QUEUE_FILE
        self.state_file = Path(state_file) if state_file else STATE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, SwarmTask] = {}
        self.counter = 0
        self._load()

    # ----------------------------------------------------------- Persistenz
    def _load(self) -> None:
        if self.queue_file.exists():
            try:
                data = json.loads(self.queue_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            for row in data.get("tasks", []):
                task = SwarmTask(**row)
                self.tasks[task.title] = task
            self.counter = data.get("counter", 0)

    def save(self) -> None:
        payload = {
            "counter": self.counter,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [asdict(t) for t in self.tasks.values()],
        }
        tmp = self.queue_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.queue_file)

    # -------------------------------------------------------------- Operationen
    def add(self, title: str, assignee: str, body: str = "",
            parents: Optional[List[str]] = None,
            priority: int = 0) -> SwarmTask:
        task = SwarmTask(title=title, assignee=assignee, body=body,
                         parents=list(parents or []), priority=priority)
        self.tasks[title] = task
        self.counter += 1
        self.save()
        return task

    def parents_done(self, task: SwarmTask) -> bool:
        return all(self.tasks.get(p, None) is not None
                   and self.tasks[p].status == STATUS_DONE
                   for p in task.parents)

    def ready_tasks(self) -> List[SwarmTask]:
        """Tasks, die jetzt starten duerfen.

        Beruecksichtigt ``queued`` UND ``ready``: ein Task, der in ``ready``
        steht, wartet nur noch auf einen freien Worker-Slot — er darf bei
        einem weiteren Tick nicht verschwinden.
        """
        out = [t for t in self.tasks.values()
               if t.status in (STATUS_QUEUED, STATUS_READY) and self.parents_done(t)]
        out.sort(key=lambda t: (-t.priority, t.created_at))
        return out

    def claim(self, limit: int = MAX_PARALLEL) -> List[SwarmTask]:
        """Nimmt bis zu ``limit`` Tasks in Bearbeitung.

        Bereits laufende Tasks zaehlen gegen das Limit — sonst waechst die
        Parallelitaet bei jedem Tick ueber die Grenze hinaus.
        """
        claimed: List[SwarmTask] = []
        # Belegung = bereits laufende + gerade beanspruchte Tasks.
        occupied = sum(1 for t in self.tasks.values() if t.status == STATUS_RUNNING)
        for task in self.ready_tasks():
            if occupied >= limit:
                break
            if task.status == STATUS_RUNNING:
                continue
            task.status = STATUS_RUNNING
            task.started_at = datetime.now(timezone.utc).isoformat()
            claimed.append(task)
            occupied += 1
        if claimed:
            self.save()
        return claimed

    def complete(self, title: str, result: Optional[Dict[str, Any]] = None) -> None:
        task = self.tasks.get(title)
        if not task:
            return
        task.status = STATUS_DONE
        task.finished_at = datetime.now(timezone.utc).isoformat()
        task.result = result or {}
        self.save()

    def block(self, title: str, reason: str) -> None:
        task = self.tasks.get(title)
        if not task:
            return
        task.status = STATUS_BLOCKED
        task.finished_at = datetime.now(timezone.utc).isoformat()
        task.error = reason
        self.save()

    def promote(self) -> List[SwarmTask]:
        """Queued -> ready, sobald alle Eltern erledigt sind."""
        promoted = []
        for task in self.tasks.values():
            if task.status == STATUS_QUEUED and self.parents_done(task):
                task.status = STATUS_READY
                promoted.append(task)
        if promoted:
            self.save()
        return promoted

    def stats(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for task in self.tasks.values():
            counts[task.status] = counts.get(task.status, 0) + 1
        return {
            "total": len(self.tasks),
            "by_status": counts,
            "ready": len(self.ready_tasks()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def write_state(self) -> Path:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.stats(), ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        return self.state_file


def ledger_hook(event: Dict[str, Any]) -> None:
    """Schreibt ein Schwarm-Ereignis in den Black-Box-Ledger (best effort)."""
    try:
        plugin = Path(__file__).resolve().parent.parent / "plugins" / "capital-tracker"
        sys_path = str(plugin)
        import sys
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from ledger import Event, Ledger, STREAM_SWARM  # type: ignore
        Ledger().append(Event(
            stream=STREAM_SWARM,
            metric=str(event.get("metric", "swarm_event")),
            value=float(event.get("value", 1)),
            unit=str(event.get("unit", "")),
            evidence=str(event.get("evidence", "")),
            confidence=str(event.get("confidence", "measured")),
        ))
    except Exception:
        pass  # Ledger darf den Scheduler nie stoppen


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Schwarm-Scheduler")
    parser.add_argument("--add", help="Task: 'Titel|Assignee|Beschreibung'")
    parser.add_argument("--parents", help="Komma-getrennte Eltern-Titel")
    parser.add_argument("--tick", action="store_true", help="Einmaliger Scheduler-Tick")
    parser.add_argument("--complete", help="Task als erledigt markieren")
    parser.add_argument("--block", help="Task blockieren (mit Grund nach '|')")
    parser.add_argument("--stats", action="store_true", help="Status anzeigen")
    args = parser.parse_args()

    scheduler = SwarmScheduler()

    if args.add:
        parts = args.add.split("|")
        title = parts[0].strip()
        assignee = parts[1].strip() if len(parts) > 1 else "default"
        body = parts[2].strip() if len(parts) > 2 else ""
        parents = [p.strip() for p in (args.parents or "").split(",") if p.strip()]
        task = scheduler.add(title, assignee, body, parents)
        print(f"Task angelegt: {task.title} (assignee={task.assignee}, "
              f"parents={task.parents or '-'})")
        ledger_hook({"metric": "task_created", "value": 1,
                     "evidence": f"swarm/{task.title}"})

    if args.complete:
        scheduler.complete(args.complete)
        print(f"Task erledigt: {args.complete}")
        ledger_hook({"metric": "task_done", "value": 1,
                     "evidence": f"swarm/{args.complete}"})

    if args.block:
        parts = args.block.split("|", 1)
        scheduler.block(parts[0], parts[1] if len(parts) > 1 else "kein Grund")
        print(f"Task blockiert: {parts[0]}")

    if args.tick:
        scheduler.promote()
        claimed = scheduler.claim()
        print(f"Tick: {len(claimed)} Task(s) in Bearbeitung")
        for task in claimed:
            print(f"  -> {task.title} [{task.assignee}]")
            ledger_hook({"metric": "task_running", "value": 1,
                         "evidence": f"swarm/{task.title}"})
        scheduler.write_state()

    if args.stats or not (args.add or args.complete or args.block or args.tick):
        stats = scheduler.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        scheduler.write_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
