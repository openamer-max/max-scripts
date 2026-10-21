#!/usr/bin/env python3
"""OpenAmer AGI — Attribution + deutsche Begleitdokumente fuer den FULL MIRROR.

by Amer Sacirovic

Erzeugt/aktualisiert:
  - ATTRIBUTION_BY_AMER.md   (Rechtlicher Nachweis + Herkunft)
  - README.de.md             (Deutsche Projektpraesentation)
  - Kopfzeilen-Attribution in allen zentralen Python-/Shell-Dateien (idempotent)
  - .gitattributes           (Zeilenenden + LFS-freundliche Filter)
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MIRROR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "openamer-max" / "max-scripts"
AUTHOR = "Amer Sacirovic"
UPSTREAM = "https://github.com/openamer/openamer"
DOWNSTREAM = "https://github.com/openamer-max/max-scripts"

TODAY = datetime.now(timezone.utc).strftime("%d.%m.%Y")

ATTRIBUTION_MD = f"""# Attribution — OpenAmer AGI Spiegel

**by {AUTHOR}**
*Kopie des Originals: {UPSTREAM} — Spiegel: {DOWNSTREAM}*

---

## Was dieses Repository ist

Dieses Repository ist ein **FULL MIRROR** des Open-Quell-Projekts
[`openamer/openamer`]({UPSTREAM}). Es ist ein 1:1-Abbild des Original-Zustands
mit folgenden bewussten Ergaenzungen:

| Element | Regel |
|---|---|
| Programmcode | **unveraendert** uebernommen (keine forks, keine Code-Aenderungen) |
| `LICENSE` | **Original Apache-2.0 bleibt erhalten** — Pflicht bei Weitergabe |
| `README.md` | Original + angehaengter Attributions-Block |
| `README.de.md` | **Zusaetzlich**, deutschsprachige Praesentation (von {AUTHOR}) |
| `ATTRIBUTION_BY_AMER.md` | diese Datei |
| Kopfzeilen | zusaetzliche Kommentarzeile `by {AUTHOR}` in zentralen Dateien |

## Urheberrecht und Lizenz

Das Original steht unter der **Apache License 2.0**. Die Datei `LICENSE` im
Repository-Stamm ist die unveraenderte Original-Lizenz. Alle Rechte am
Original-Code liegen beim Openamer-Projekt bzw. seinen Beitragenden.

Dieser Spiegel:

- veraendert **keinen** Original-Code,
- entfernt **keine** Lizenz- oder Copyright-Hinweise,
- fuegt **keine** Namen oder Marken des Originals in fremde Produkte ein,
- nennt das Original in README und Attribution ausdruecklich als Quelle.

## Verzeichnis-Konvention

Dieses Repository folgt dem im Original etablierten Muster:

```
max-scripts/          -> das originale Python-Paket
scripts/              -> Hilfsskripte
docs/                 -> Projektdokumentation
plugins/              -> Plugin-Registry
```

Die unter `docs/` abgelegten Dateien mit dem Praefix `AM_` (Amer) wurden von
{AUTHOR} ergaenzt.

---

*Spiegel gepflegt von {AUTHOR} — {TODAY}*
"""

README_DE = f"""# OpenAmer AGI — Spiegel

**by {AUTHOR}**
*Original: [`openamer/openamer`]({UPSTREAM}) — dieser Mirror: `{DOWNSTREAM}`*

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

**{AUTHOR}** — Spiegel, Integration, autonome Agenten-Pipeline.
Original-Projekt: Openamer Contributors, Apache-2.0.

---

*Spiegel gepflegt von {AUTHOR} — {TODAY}*
"""

GITATTRIBUTES = """# OpenAmer AGI Mirror — by Amer Sacirovic
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.mp4 binary
*.pdf binary
*.whl binary
*.exe binary
"""


def has_marker(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    except Exception:
        return True
    return AUTHOR in head


def add_header(path: Path) -> bool:
    """Fuegt die Attribution-Zeile nach Shebang/SQL-Delimiter ein. Idempotent."""
    if has_marker(path):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    lines = text.split("\n")
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    elif lines and lines[0].strip() == "#!/usr/bin/env python3 -c":
        insert_at = 1
    if insert_at < len(lines) and lines[insert_at].startswith("#!"):
        insert_at += 1
    header = f"# {MIRROR.name} Mirror — by {AUTHOR}"
    lines.insert(insert_at, header)
    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main() -> int:
    if not MIRROR.is_dir():
        print(f"FEHLER: Mirror-Verzeichnis nicht gefunden: {MIRROR}")
        return 1

    (MIRROR / "ATTRIBUTION_BY_AMER.md").write_text(ATTRIBUTION_MD, encoding="utf-8")
    (MIRROR / "README.de.md").write_text(README_DE, encoding="utf-8")
    (MIRROR / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8")
    print("  ATTRIBUTION_BY_AMER.md geschrieben")
    print("  README.de.md geschrieben")
    print("  .gitattributes geschrieben")

    # README.md um Attributions-Block ergaenzen (idempotent)
    readme = MIRROR / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        marker = "<!-- OPENAMER-MAX-MIRROR-ATTRIBUTION -->"
        if marker not in text:
            block = (
                f"\n\n---\n\n<!-- OPENAMER-MAX-MIRROR-ATTRIBUTION -->\n\n"
                f"## Spiegel-Attribution\n\n"
                f"**by {AUTHOR}** — Dieses Repository ist ein FULL MIRROR von "
                f"[`{UPSTREAM}`]({UPSTREAM}).\n\n"
                f"- Originalcode unveraendert, **Apache-2.0-Lizenz erhalten** (siehe `LICENSE`)\n"
                f"- Deutsche Praesentation: [`README.de.md`](README.de.md)\n"
                f"- Herkunfts- und Lizenznachweis: [`ATTRIBUTION_BY_AMER.md`](ATTRIBUTION_BY_AMER.md)\n\n"
                f"*Spiegel gepflegt von {AUTHOR}.*\n"
            )
            readme.write_text(text.rstrip() + block, encoding="utf-8")
            print("  README.md: Attributions-Block ergaenzt")

    # Kopfzeilen-Attribution in zentralen Dateien
    targets: list[Path] = []
    for pattern in ("*.py", "scripts/*.py", "tools/*.py", "*.sh", "scripts/*.sh",
                    "openamer_cli/*.py", "agent/*.py"):
        targets.extend(MIRROR.glob(pattern))
    changed = 0
    for path in targets:
        if path.is_file() and path.stat().st_size < 2_000_000:
            if add_header(path):
                changed += 1
    print(f"  Kopfzeilen-Attribution: {changed} Dateien angepasst")

    print(f"  Mirror-Pfad: {MIRROR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
