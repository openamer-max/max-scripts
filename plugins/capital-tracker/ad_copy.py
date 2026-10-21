#!/usr/bin/env python3
"""OpenAmer AGI — Werbetext-Generator fuer alle Plattformen.

by Amer Sacirovic

Ein Text, eine Aussage, ein Ziel: der Beitrag fuehrt zum Download von
OpenAmer (github.com/openamer). Der Text ist an die Plattform angepasst
(Laenge, Ton, Emoji-Dichte) und nennt immer den Download-Link.

Es werden **keine** Zahlen erfunden: Reichweiten-/Einnahmenangaben kommen aus
dem Black-Box-Ledger, nicht aus diesem Modul.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))

REPO_URL = "https://github.com/openamer"
DOWNLOAD_URL = "https://github.com/openamer/openamer/releases"
MIRROR_URL = "https://github.com/openamer-max/max-scripts"

HASHTAGS_CORE = ["OpenAmer", "OpenAmerAGI", "AIAgent", "SelfImprovingAI",
                  "Automation", "LocalAI", "KI"]
HASHTAGS_LONG = ["OpenAmer", "OpenAmerAGI", "AIAgent", "SelfImprovingAI",
                  "Automation", "LocalAI", "KI", "OpenSource", "Python",
                  "ClaudeCode", "AgenticAI", "Tech", "FutureOfWork",
                  "ContentAutomation", "DevCommunity", "MachineLearning"]


def _ledger_totals() -> Dict[str, float]:
    """Liest die echten Kennzahlen aus dem Ledger (leer, wenn keiner existiert)."""
    snap = HOME / "blackbox" / "snapshot.json"
    if not snap.exists():
        return {}
    try:
        data = json.loads(snap.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data.get("totals", {}) or {}


def _fmt(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    if float(value).is_integer():
        return f"{int(value):,}".replace(",", ".")
    return f"{value:.1f}".replace(".", ",")


def youtube_description(title: str, video: str) -> str:
    """Beschreibung fuer YouTube (Shorts + regulaer)."""
    totals = _ledger_totals()
    views = _fmt(totals.get("social:youtube.views_28d:measured"))
    followers = _fmt(totals.get("social:youtube.followers:measured"))

    lines = [
        f"🧬 {title}",
        "",
        "OpenAmer ist dein autonomer KI-Agent fuer Windows. Er verbessert sich "
        "selbst — er analysiert seine eigenen Logs, optimiert eigene Skills "
        "und Code, spawnt Sub-Agenten fuer parallele Workflows und macht die "
        "Kapitalgenerierung in Echtzeit sichtbar.",
        "",
        "✅ Skills & Self-Coding  — der Agent verbessert sich selbst weiter",
        "✅ Schwarm-Infra      — Sub-Agenten laufen parallel, ohne dein Zutun",
        "✅ Black-Box-Dashboard — alle Datenstroeme live in einer Oberflaeche",
        "✅ Lokal lauffaehig   — Ollama, RTX 5060, kein Cloud-Zwang",
        "✅ Multi-Plattform    — Telegram, Discord, Slack, WhatsApp, Web-UI, Desktop, TUI",
        "✅ Plugin-Architektur — schmaler Kern, breite Kante",
        "",
        "⬇️ JETZT DOWNLOADEN (kostenlos & quelloffen):",
        DOWNLOAD_URL,
        "",
        f"📖 Projekt: {REPO_URL}",
        f"🔁 Vollstaendiger Spiegel: {MIRROR_URL}",
        "",
        "📌 Links in der Beschreibung: Release-Download, Doku, Source-Code.",
        "",
        " ".join("#" + h for h in HASHTAGS_CORE + ["Shorts", "OpenSource"]),
    ]
    if views:
        lines.insert(9, f"📊 Aktuell im Kanal: {views} Aufrufe in 28 Tagen"
                         + (f" · {followers} Abonnenten" if followers else ""))
    return "\n".join(lines)


def short_caption(text: str, max_len: int = 2200) -> str:
    """Kurzer Caption-Text fuer TikTok / Instagram / Facebook."""
    body = (
        "🧬 OpenAmer AGI — dein autonomer KI-Agent.\n\n"
        "Er analysiert seine eigenen Logs, verbessert Skills und Code selbst, "
        "spawnt Sub-Agenten fuer parallele Workflows und zeigt dir die "
        "Kapitalgenerierung live.\n\n"
        "⬇️ Kostenlos, quelloffen, lokal lauffaehig:\n"
        f"{REPO_URL}\n\n"
        + " ".join("#" + h for h in HASHTAGS_CORE)
    )
    if len(body) > max_len:
        body = body[:max_len - 1].rstrip() + "…"
    return body


def plan(platforms: List[str], title: str) -> Dict[str, Dict[str, str]]:
    """Erzeugt den Textplan je Plattform."""
    out: Dict[str, Dict[str, str]] = {}
    for platform in platforms:
        key = platform.lower()
        if key in {"youtube", "yt"}:
            out[platform] = {"title": title,
                             "description": youtube_description(title, "")}
        elif key in {"instagram", "ig", "reels"}:
            out[platform] = {"title": title[:100],
                             "description": short_caption(title, 2200)}
        elif key in {"tiktok", "tt"}:
            out[platform] = {"title": title[:100],
                             "description": short_caption(title, 2200)}
        elif key in {"facebook", "fb"}:
            out[platform] = {"title": title[:100],
                             "description": short_caption(title, 5000)}
        else:
            out[platform] = {"title": title[:100],
                             "description": short_caption(title, 2200)}
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Werbetext-Planer")
    parser.add_argument("--platforms", default="youtube,tiktok,instagram,facebook")
    parser.add_argument("--title", required=True)
    parser.add_argument("--json", action="store_true", help="als JSON ausgeben")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    result = plan(platforms, args.title)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    for platform, data in result.items():
        print(f"\n{'=' * 62}\n{platform.upper()}\n{'=' * 62}")
        print(f"Titel:       {data['title']}")
        print(f"Beschreibung:\n{data['description']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
