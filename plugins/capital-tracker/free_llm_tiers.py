#!/usr/bin/env python3
"""OpenAmer AGI — Kostenlose-LLM-Fallback-Kette (Provider-Fallback-Plugin).

by Amer Sacirovic

Warum als Plugin und nicht als Core-Tool:
    Die Projektlinie lautet "schmaler Kern, breite Kante". Eine Fallback-Kette
    fuer Provider braucht kein eigenes Modell-Tool — sie liest die bereits
    vorhandene ``custom_providers``-Konfiguration und schlaegt den
    naechsten verfuegbaren Provider vor. Das bleibt damit am Rand.

Recherche-Basis (21.10.2026, Google via eingeloggten Chrome):
    - OpenRouter  : ":free"-Modell-Tags, ein Key, keine Kreditkarte
    - GroqCloud   : LPU-Inferenz, Llama/Qwen, ohne Kreditkarte
    - Mistral     : La Plateforme, Codestral/Ministral
    - Google AI   : Gemini Flash / Flash-Lite (neue Accounts: Karte/Prepaid)
    - NVIDIA NIM  : Nemotron-Katalog, ~40 Requests/Minute

Das Modul erfindet **keine** Keys und ruft **keine** API ohne Key auf. Es
bewertet nur die bereits konfigurierten Provider und liefert eine
ReihenfolgeEmpfehlung.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
CONFIG = HOME / "config.yaml"
REPORT = HOME / "blackbox" / "free_llm_tiers.json"


@dataclass
class Provider:
    """Ein Provider-Eintrag aus der OpenAmer-Konfiguration."""

    name: str
    base_url: str
    models: List[str] = field(default_factory=list)
    tier: str = "unbekannt"
    notes: str = ""

    def has_key(self) -> bool:
        """Prueft, ob fuer diesen Provider ein API-Key hinterlegt ist.

        Der Key wird **nur geprueft**, nie ausgegeben.
        """
        env = HOME / ".env"
        if not env.exists():
            return False
        try:
            text = env.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return False
        key = re.sub(r"[^A-Z0-9]+", "_", self.name.upper()).strip("_")
        candidates = [f"{key}_API_KEY", f"{key}_KEY"]
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name = line.split("=", 1)[0].strip()
            if name in candidates and line.split("=", 1)[1].strip():
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "base_url": self.base_url,
                "models": self.models, "tier": self.tier, "notes": self.notes,
                "has_key": self.has_key()}


# Bekannte kostenlose Tiers (aus der Recherche vom 21.10.2026)
FREE_TIERS: Dict[str, Dict[str, str]] = {
    "openrouter": {
        "tier": "free",
        "notes": ":free-Modell-Tags, ein API-Key, keine Kreditkarte noetig",
    },
    "groq": {
        "tier": "free",
        "notes": "LPU-Inferenz, Llama/Qwen, ohne Kreditkarte, strenge Rate-Limits",
    },
    "mistral": {
        "tier": "free",
        "notes": "La Plateforme, Codestral/Ministral im Free-Tier",
    },
    "google": {
        "tier": "free",
        "notes": "Gemini Flash/Flash-Lite; neue Accounts brauchen Karte oder Prepaid",
    },
    "nvidia": {
        "tier": "free",
        "notes": "NIM/Nemotron-Katalog, ca. 40 Requests/Minute fuer Tests",
    },
    "cloudflare": {
        "tier": "free",
        "notes": "Workers AI, in der Top-5-Liste 2026 genannt",
    },
    "localhost": {
        "tier": "lokal",
        "notes": "Ollama — kein API-Limit, laeuft auf eigener Hardware",
    },
    "ollama": {
        "tier": "lokal",
        "notes": "Ollama — kein API-Limit, laeuft auf eigener Hardware",
    },
}


def _tier_for(name: str, base_url: str) -> Dict[str, str]:
    haystack = f"{name} {base_url}".lower()
    for key, info in FREE_TIERS.items():
        if key in haystack:
            return info
    return {"tier": "unbekannt", "notes": ""}


def load_providers(config_path: Optional[Path] = None) -> List[Provider]:
    """Liest die ``custom_providers`` aus der OpenAmer-Konfiguration."""
    path = Path(config_path) if config_path else CONFIG
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    providers: List[Provider] = []
    in_block = False
    current: Optional[Provider] = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith("custom_providers:"):
            in_block = True
            continue
        if in_block and indent == 0:
            break
        if not in_block:
            continue

        if stripped.startswith("- name:"):
            name = stripped.split(":", 1)[1].strip().strip("'\"")
            current = Provider(name=name, base_url="")
            providers.append(current)
            continue
        if current is None:
            continue
        if stripped.startswith("base_url:"):
            current.base_url = stripped.split(":", 1)[1].strip().strip("'\"")
        elif stripped.startswith("model:"):
            current.models.append(stripped.split(":", 1)[1].strip().strip("'\""))
        elif stripped.startswith("- ") and current.models:
            current.models.append(stripped[2:].strip().strip("'\""))
        elif stripped.startswith("-"):
            current.models.append(stripped[2:].strip().strip("'\""))

    for prov in providers:
        info = _tier_for(prov.name, prov.base_url)
        prov.tier = info["tier"]
        prov.notes = info["notes"]
    return providers


def fallback_chain(providers: List[Provider]) -> List[Provider]:
    """Sortiert die Provider fuer eine Fallback-Kette.

    Reihenfolge: lokal (kein Limit) -> free (mit Key) -> free (ohne Key)
    -> unbekannt. Innerhalb einer Stufe gewinnt der Anbieter mit mehr Modellen.
    """
    rank = {"lokal": 0, "free": 1, "unbekannt": 2}
    return sorted(
        providers,
        key=lambda p: (rank.get(p.tier, 3), 0 if p.has_key() else 1, -len(p.models)),
    )


def report(providers: Optional[List[Provider]] = None) -> Dict[str, Any]:
    """Erzeugt den Report (fuer das Black-Box-Ledger)."""
    providers = providers if providers is not None else load_providers()
    chain = fallback_chain(providers)
    return {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "provider_count": len(providers),
        "free_tier_count": sum(1 for p in providers if p.tier == "free"),
        "with_key": sum(1 for p in providers if p.has_key()),
        "chain": [p.to_dict() for p in chain],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Free-LLM-Fallback-Kette")
    parser.add_argument("--report", action="store_true", help="JSON-Report schreiben")
    parser.add_argument("--json", action="store_true", help="als JSON ausgeben")
    args = parser.parse_args()

    data = report()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Provider: {data['provider_count']}  |  free: {data['free_tier_count']}  "
              f"|  mit Key: {data['with_key']}")
        print("-" * 78)
        for i, p in enumerate(data["chain"], 1):
            key = "Key" if p["has_key"] else "kein Key"
            print(f"{i:2d}. [{p['tier']:9s}] {p['name'][:34]:34s} {key:8s} "
                  f"{len(p['models'])} Modelle")
            if p["notes"]:
                print(f"      -> {p['notes']}")
    if args.report:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
