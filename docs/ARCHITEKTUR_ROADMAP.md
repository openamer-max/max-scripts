# Architektur-Roadmap — OpenAmer AGI

**by Amer Sacirovic** · Stand 21.10.2026

Dieses Dokument beantwortet die Frage: **wo** gehören Kapital-Tracking und
Social-Media-Automatisierung in die bestehende Projektstruktur, und wie
werden Self-Coding, Schwarm-Infrastruktur und Black-Box-Dashboard darauf
aufgesetzt?

---

## 0. Bestandsaufnahme (verifiziert)

Die Analyse des Repos `openamer/openamer` (10.609 Dateien, Branch `main`,
Commit `c316b88e3`) zeigt folgende bereits vorhandene Bausteine:

| Baustein | Ort im Repo | Status |
|---|---|---|
| Agent-Core | `agent/`, `openamer_cli/` | vorhanden, aktiv |
| Native ASI-Tools | `native/` | vorhanden (5 Tools) |
| A2A Global Mesh | `a2a/`, `relay-inbox/` | vorhanden |
| Gateway (Plattformen) | `gateway/` | vorhanden (~20 Plattformen) |
| Darwin-Evolution (Self-Coding) | `darwin/`, `darwin-grid/` | vorhanden, 25 Phasen |
| Cron/Scheduler | `cron/` | vorhanden (Heartbeat statt ~84 Cronjobs) |
| Plugins | `plugins/` | vorhanden, ABC-/Hook-basiert |
| Skills | `skills/`, `optional-skills/` | vorhanden |
| Desktop-Plugins | `desktop-plugins/` | vorhanden |
| Modelle/Provider | `models/`, `providers/` | vorhanden |
| Doku | `docs/` | vorhanden, umfangreich |

**Schlussfolgerung:** Die Bausteine fuer die vier offenen Kapitel existieren
zumeist **bereits**. Die Aufgabe ist nicht „Neues bauen", sondern **Verknuepfen
und An die Kanten stellen** — genau die Leitlinie des Projekts:
*„schmaler Kern, breite Kante"*.

---

## 1. Kapital-Tracking (Black Box) — Platzierung

### Bestehende Ansatzpunkte

- `docs/billing-lifecycle.md` — dokumentiert den Kapital-Lebenszyklus bereits
- `native/` — native ASI-Tools, dort liegt die Heartbeat-Mechanik
- `asi_core/data_hub.json` (lokale Instanz) — Aggregations-Punkt
- `asi_core/conversion_tracker.py` — existiert bereits als Tracker

### Entscheidung

Kapital-Tracking gehoert **nicht** in den Core (`agent/`). Es ist ein
**Service-gated Tool + Plugin**, das aus dem Heartbeat-Stream liest.

```
native/heartbeat/            <- bestehender Taktgeber
        |
        v
plugins/capital-tracker/     <- NEU: Plugin (Service-Gated)
   ├── collector.py          <- liest Logs, Cron-Logs, Platform-Status
   ├── ledger.py             <- append-only JSONL-Ledger (unveraeglich)
   └── metrics.py            <- Kennzahlen: Reichweite, Conversion, EUR
        |
        v
dashboard/                   <- bestehendes Dashboard (Port 8899)
   + black_box.html          <- NEU: Kapital-Dashboard
```

**Rationale:** Das Ledger ist **append-only JSONL** — kein Core-Zustand, kein
Prompt-Cache-Einfluss, kein Eingriff in die Tool-Schleife. Das Dashboard liest
das Ledger, der Agent schreibt es.

### Datenfluss

| Quelle | Intervall | Ziel |
|---|---|---|
| `logs/` (Agent-Logs) | pro Heartbeat | Fehler-/Muster-Zaehler |
| `cron/output/` | pro Heartbeat | Pipeline-Ergebnisse |
| Plattform-Status (IG/TikTok/YT) | pro Zyklus | Reichweite + Follower |
| `conversion_tracker.py` | pro Zyklus | Conversion -> EUR |
| PayPal (Pin 1976 bei Aktion) | Ereignis | Einnahmen-Bestaetigung |

### Akzeptanzkriterien

- `black_box.html` zeigt: Kapital (prognostiziert + real), Reichweite, Conversion, Pipeline-Status
- Datenstrom laeuft **live** (kein Mock) — jede Zeile im Ledger hat einen Timestamp
- Dashboard laeuft ohne den Agenten (statisch + JSON-Feed)

---

## 2. Social-Media-Automatisierung — Platzierung

### Bestehende Ansatzpunkte

- `scripts/tiktok_openamer_agent.py`, `viral_content_deployment.py` (lokal)
- `social/config.yaml`, `social/scripts/` (lokale Instanz)
- `plugins/` — Registry fuer Plattform-Erweiterungen

### Entscheidung

Plattform-Adapter gehoeren **ausschliesslich** in `plugins/`, jeweils ein
Plugin pro Plattform, mit gemeinsamer ABC-Basis:

```
plugins/
  _social_base/              <- NEU: ABC + gemeinsame Pipeline
  social-tiktok/             <- NEU
  social-instagram/           <- NEU
  social-youtube/             <- NEU
  social-facebook/            <- NEU
  social-telegram/            <- vorhanden (Gateway)
```

Gemeinsame Pipeline (identisch fuer alle Plattformen):

```
content_orchestrator -> [plattform-formatiert] -> rate_limit_check -> upload -> log -> ledger
```

**Rationale (Projekt-Linie):** „Third-party products / other people's projects
integrated into the core tree" werden abgelehnt. Plattform-Adapter sind
Kanten-Erweiterungen -> Plugin. Der gemeinsame Kern der Pipeline ist ein
**ABC**, damit keine Kopien entstehen.

### Autologin

Der Chrome-Autologin-Mechanismus ist implementiert und verifiziert
(siehe `docs/AUTOLOGIN_STATUS.md`). Getestet live: **Gmail + PayPal** sind
angemeldet, GitHub/TikTok/YouTube/Instagram waren abgemeldet.

---

## 3. Self-Coding (Rekursions-Schleife) — Platzierung

### Bestehende Ansatzpunkte

- `darwin/` + `darwin-grid/` — 25 Evolutionsphasen, Skill-Mutation, Duell-Logik
- `scripts/autonomous_loop.py` — der 30-Minuten-Autopilot
- `learning-loop/` (lokal) — Fehlerkategorisierung

### Entscheidung

Die Rekursions-Schleife gehoert **in `darwin/`** und wird ueber
`native/`-Heartbeat angestossen. Sie ist bewusst **kein** neues Core-Tool.

```
native/heartbeat
     |
     v
darwin/autonomous_loop.py --loop        <- bestehend, 30-Min-Takt
     |
     +-> logs analysieren        (Eigenes Log-Intake)
     +-> Skill-Mutation          (bestehend, 25 Phasen)
     +-> Code-Verbesserung       (NEU: AST-basiert, gesichert)
     +-> Fitness-Speicherung     (bestehend, Duell-Logik)
```

### Code-Verbesserung: Sicherheitsregeln

Autonomes Aendern von Code braucht eine **Fail-Closed**-Kette, sonst
zerstoert die Selbstverbesserung das System, das sie verbessern soll:

1. Nur in `scripts/`, `skills/`, `optional-skills/` — **nie** in `agent/`
2. Aenderung nur als **Patch in einer Sandbox-Kopie**, nie im Original
3. **Verifikations-Pflicht**: der Patch muss den bestehenden Testlauf bestehen
4. Bei Fehlschlag: **Rollback**, kein Teilerfolg
5. Jede Aenderung wird im Ledger protokolliert (Bezug zu Kapitel 1)

---

## 4. Schwarm-Infrastruktur — Platzierung

### Bestehende Ansatzpunkte

- `delegate_task` (Core) — Subagenten mit isoliertem Kontext, echte Transkripte
- `a2a/` + `relay-inbox/` — Agent-zu-Agent-Kommunikation
- `scripts/swarm_os.py`, `swarm_migration.py` (lokal)
- `asi_core/dispatcher_engine.py` (lokal)

### Entscheidung

Die Schwarm-Steuerung gehoert in **`swarm/`** als eigene Schicht ueber
`delegate_task`, mit der Besonderheit: **Heartbeat-getrieben, nicht
Session-getrieben**. Das erlaubt parallele Workflows ueber Session-Grenzen
hinweg — das Kernargument des Nutzers („ohne deine Eingriffe managen").

```
swarm/
  ├── scheduler.py        <- Heartbeat-Scheduler: parallel, priorisiert
  ├── worker_pool.py      <- Worker mit Energie/Health (darwin)
  ├── task_queue.py       <- persistente Queue (Task-Queue-Skill)
  └── state.py            <- Swarm-State, resumable
```

**Ist-Zustand (verifiziert):** `delegate_task` ist bereits implementiert und
arbeitet — im Testlauf wurden 2 Subagenten parallel dispatcht und lieferten
Ergebnisse. Was fehlt, ist die **dauerhafte, resumable** Ebene darueber.

### Kanban als Board

Das Kanban-Board (`~/.openamer/kanban.db`) ist bereits die Task-Ergebnisse-
Instanz. Es wird zur **Schnittstelle** zwischen Schwarm und Agent:

| Rolle | Mechanismus |
|---|---|
| Dispatch | `kanban_create` mit `assignee` + `parents` (Abhaengigkeiten) |
| Parallelitaet | 3 Worker parallel, `max_concurrent_children` |
| Handoff | `kanban_complete(metadata=...)` — strukturierte Fakten |
| Review | `kanban_request_review` statt `kanban_block` |
| Sichtbarkeit | `kanban_list` → Dashboard |

---

## 5. Zusammenfuehrung: Black-Box-Dashboard

Alle vier Kapitel speisen in **eine** Datenquelle: das append-only Ledger
(`plugins/capital-tracker/ledger.jsonl`).

```
  Self-Coding ──┐
  Schwarm ──────┼──> ledger.jsonl ──> black_box.html
  Social ───────┤                        (Port 8900)
  Kapital ──────┘
```

Der Ledger-Eintrag ist ein **kanonisches Ereignis**:

```json
{
  "ts": "2026-10-21T12:00:00Z",
  "stream": "capital|social|swarm|selfcode",
  "metric": "reach|conversion|revenue|patch|task",
  "value": 1234.5,
  "unit": "EUR|views|posts|patch",
  "evidence": "logs/… | platform: instagram",
  "confidence": "measured|projected"
}
```

`confidence` ist entscheidend: **projected** (Prognose) und **measured**
(gemessen) werden getrennt gefuehrt. Die Black Box zeigt beides, aber
kennzeichnet es — ein Dashboard, das Prognose als Ist verkauft, waere
Werbung, kein Dashboard.

---

## 6. Reihenfolge der Umsetzung

| # | Schritt | Abhaengigkeit | Ergebnis |
|---|---|---|---|
| 1 | `plugins/capital-tracker/` + Ledger | — | Datenmodell steht |
| 2 | `plugins/_social_base/` + ABC | — | gemeinsame Pipeline |
| 3 | `black_box.html` an Port 8900 | 1 | Sichtbarkeit |
| 4 | `swarm/scheduler.py` (Heartbeat) | — | persistente Parallelitaet |
| 5 | Darwin -> Code-Verbesserung mit Sandbox+Test-Pflicht | — | Self-Coding |
| 6 | Kanban <-> Schwarm verdrahten | 4 | durchgaengige Kette |

**Jeder Schritt ist einzeln lauffaehig und einzeln verifizierbar** — kein
Big-Bang-Refactor.

---

*by Amer Sacirovic — OpenAmer AGI*
