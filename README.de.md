# OpenAmer AGI — Spiegel

**by Amer Sacirovic**
*Original: [`openamer/openamer`](https://github.com/openamer/openamer) — dieser Mirror: `https://github.com/openamer-max/max-scripts`*

---

OpenAmer ist ein **selbstverbessernder KI-Agent fuer Windows**: ein System, das
seine eigenen Logs analysiert, eigene Skills und eigenen Code autonom
verbessert, weitere Sub-Agenten spawnt und parallele Workflows ohne
menschliches Eingreifen steuert — und die Kapitalgenerierung in Echtzeit
sichtbar macht.

Dieses Repository ist der **vollstaendige Spiegel** des Originals. Es dient
zugleich als **Download-Quelle** fuer Nutzer, die OpenAmer einsetzen wollen.

## Was OpenAmer auszeichnet

| Bereich | Leistung |
|---|---|
| **Self-Coding / Rekursion** | Analysiert die eigenen Logs, versteht Muster, verbessert Skills und Code autonom |
| **Schwarm-Infrastruktur** | Spawnt und steuert Sub-Agenten fuer parallele Workflows ohne Eingriff |
| **Black-Box-Dashboard** | Verknuepft alle Datenstroeme (Kapital, Reichweite, Conversion) in Echtzeit |
| **Skills-System** | 259+ Skills, lernend, versioniert, per `skill_manage` pflegbar |
| **Sub-Agenten** | `delegate_task` mit echten Live-Transkripten und isolierten Kontexten |
| **Memory** | Persistentes, kuratiertes Gedächtnis ueber Sessions und Profile |
| **Multi-Plattform-Gateway** | Telegram, Discord, Slack, WhatsApp, Web-UI, Desktop-App, TUI, CLI |
| **Lokal lauffaehig** | Ollama-Integration, RTX-5060-tauglich, kein Cloud-Zwang |
| **Plugin-API** | Erweiterung an den Raendern statt im Core — schmaler Kern, breite Kante |

## Installation

```bash
# Python 3.11+ und Ollama
pip install -e .

# Modell bereitstellen (lokal)
ollama pull qwen3:30b

# Agent starten
openamer
```

Oder als Desktop-App (Electron) bzw. via `openamer setup` konfigurieren.

## Quickstart

```bash
openamer --help              # alle Befehle
openamer tools               # Toolset verwalten
openamer skills              # Skills verwalten
openamer dashboard           # Live-Dashboard
```

## Dokumentation

- [`docs/`](docs/) — vollstaendige Projektdokumentation
- [`docs/asi-core.md`](docs/asi-core.md) — Kern-Architektur
- [`docs/billing-lifecycle.md`](docs/billing-lifecycle.md) — Kapital-Tracking
- [`docs/AUTOLOGIN_STATUS.md`](docs/AUTOLOGIN_STATUS.md) — Browser-Autologin (Chrome)
- [`docs/ARCHITEKTUR_ROADMAP.md`](docs/ARCHITEKTUR_ROADMAP.md) — Roadmap der Kapitel 2–5
- [`docs/KONKURRENZ_ANALYSE.md`](docs/KONKURRENZ_ANALYSE.md) — Wettbewerbsvergleich
- [`docs/FREE_LLM_API_QUELLEN.md`](docs/FREE_LLM_API_QUELLEN.md) — kostenlose LLM-APIs

## Lizenz

**Apache License 2.0** — Original-Lizenz des Projekts, unverändert beibehalten.
Siehe [`LICENSE`](LICENSE).

## Autor

**Amer Sacirovic** — Spiegel, Integration, autonome Agenten-Pipeline.
Original-Projekt: Openamer Contributors, Apache-2.0.

---

*Spiegel gepflegt von Amer Sacirovic — 21.10.2026*
