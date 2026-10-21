#!/usr/bin/env python3
"""OpenAmer AGI — Test des Schwarm-Schedulers (Abhaengigkeiten, Parallelitaet).

by Amer Sacirovic
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scheduler import (STATUS_DONE, STATUS_RUNNING, SwarmScheduler)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="swarm-test-"))
    scheduler = SwarmScheduler(queue_file=tmp / "queue.json", state_file=tmp / "state.json")
    failures = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        mark = "OK  " if condition else "FAIL"
        print(f"  [{mark}] {label}" + (f"  -> {detail}" if detail else ""))
        if not condition:
            failures.append(label)

    print("Test 1: Abhaengigkeitskette A -> B -> C")
    scheduler.add("A", "researcher", "Rohdaten sammeln")
    scheduler.add("B", "writer", "Text schreiben", parents=["A"])
    scheduler.add("C", "reviewer", "Pruefen", parents=["B"])
    scheduler.add("D", "analyst", "Ohne Abhaengigkeit", priority=5)

    ready = [t.title for t in scheduler.ready_tasks()]
    check("A und D sind startklar", set(ready) == {"A", "D"}, f"ready={ready}")
    check("B wartet auf A", "B" not in ready)
    check("C wartet auf B", "C" not in ready)

    print("Test 2: Claim begrenzt Parallelitaet")
    claimed = scheduler.claim(limit=2)
    check("max 2 Tasks beansprucht", len(claimed) == 2, f"claimed={[t.title for t in claimed]}")
    check("D hat Prioritaet", claimed[0].title == "D", f"erst={claimed[0].title}")

    print("Test 3: Persistenz ueber Neustart")
    scheduler.save()
    reloaded = SwarmScheduler(queue_file=tmp / "queue.json", state_file=tmp / "state.json")
    check("4 Tasks wiederhergestellt", len(reloaded.tasks) == 4, f"n={len(reloaded.tasks)}")
    check("Status erhalten",
          reloaded.tasks["A"].status == STATUS_RUNNING,
          f"A={reloaded.tasks['A'].status}")

    print("Test 4: Kette loest sich auf")
    reloaded.complete("A")
    reloaded.complete("B")
    ready2 = [t.title for t in reloaded.ready_tasks()]
    check("C ist jetzt startklar", "C" in ready2, f"ready={ready2}")
    reloaded.complete("C")
    check("C erledigt", reloaded.tasks["C"].status == STATUS_DONE)

    print("Test 5: Alle Task-Statistik")
    stats = reloaded.stats()
    check("3 erledigt", stats["by_status"].get(STATUS_DONE) == 3, str(stats["by_status"]))

    print("Test 6: Blockieren funktioniert")
    reloaded.block("D", "Abhaengigkeit fehlt")
    check("D blockiert", reloaded.tasks["D"].error == "Abhaengigkeit fehlt")

    shutil.rmtree(tmp, ignore_errors=True)
    print()
    if failures:
        print(f"{len(failures)} Test(s) FEHLGESCHLAGEN: {failures}")
        return 1
    print("Alle Scheduler-Tests bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
