#!/usr/bin/env python3
"""OpenAmer AGI — Gemeinsame Social-Media-Pipeline (ABC-Basis).

by Amer Sacirovic

Warum eine ABC und nicht vier Kopien:
  Jede Plattform (TikTok, Instagram, YouTube, Facebook) braucht dieselbe
  Pipeline — formatieren, Rate-Limit pruefen, hochladen, loggen, bilanzieren.
  Vier Kopien dieser Logik driften auseinander; die ABC haelt sie zusammen.
  Das entspricht der Projektlinie: gemeinsame Schnittstelle statt
  Mehrfach-Implementierung.

Ablauf einer Pipeline:

    content -> adapt(platform) -> rate_limit_check -> publish
            -> log(ledger) -> metrics

Jeder Schritt ist eine eigene Methode, damit eine Plattform nur das ueberschreiben
muss, was sie wirklich anders macht.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
SOCIAL_DIR = HOME / "social"
POST_LOG = SOCIAL_DIR / "post_log.jsonl"


@dataclass
class Post:
    """Ein zu publizierender Beitrag."""

    text: str
    media_path: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    publish_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def caption(self, max_len: int = 2200) -> str:
        tags = " ".join("#" + h.lstrip("#") for h in self.hashtags)
        body = f"{self.text}\n\n{tags}".strip() if tags else self.text
        if len(body) > max_len:
            body = body[:max_len - 1].rstrip() + "…"
        return body


@dataclass
class PublishResult:
    """Ergebnis eines Publish-Vorgangs — mit ehrlichem Status."""

    platform: str
    ok: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: str = "measured"  # measured = realer Upload bestaetigt

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


class RateLimiter:
    """Einfacher, persistenter Rate-Limiter pro Plattform."""

    def __init__(self, path: Optional[Path] = None, per_day: int = 3):
        self.path = Path(path) if path else (SOCIAL_DIR / "rate_limits.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.per_day = per_day
        self._state = self._load()

    def _load(self) -> Dict[str, List[str]]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def count_today(self, platform: str) -> int:
        today = datetime.now(timezone.utc).date().isoformat()
        return sum(1 for ts in self._state.get(platform, []) if ts.startswith(today))

    def allow(self, platform: str) -> bool:
        return self.count_today(platform) < self.per_day

    def record(self, platform: str) -> None:
        self._state.setdefault(platform, []).append(
            datetime.now(timezone.utc).isoformat())
        self._save()


class SocialPipeline(ABC):
    """Basis fuer alle Plattform-Adapter."""

    #: Anzeigename der Plattform
    platform: str = "base"
    #: Maximale Caption-Laenge
    max_caption: int = 2200
    #: Beitraege pro Tag
    per_day: int = 3

    def __init__(self, rate_limiter: Optional[RateLimiter] = None,
                 log_path: Optional[Path] = None):
        self.rate_limiter = rate_limiter or RateLimiter(per_day=self.per_day)
        self.log_path = Path(log_path) if log_path else POST_LOG
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------- Platform-Hooks
    @abstractmethod
    def publish(self, post: Post) -> PublishResult:
        """Fuehrt den eigentlichen Upload aus. Muss implementiert werden."""

    def adapt(self, post: Post) -> Post:
        """Plattformspezifische Anpassung (Standard: unveraendert)."""
        return post

    def preflight(self, post: Post) -> Optional[str]:
        """Prueft Voraussetzungen. Gibt eine Fehlermeldung zurueck oder None."""
        if not post.text.strip() and not post.media_path:
            return "Beitrag hat weder Text noch Medien"
        if post.media_path and not Path(post.media_path).exists():
            return f"Mediendatei nicht gefunden: {post.media_path}"
        return None

    # ------------------------------------------------------------- Pipeline
    def run(self, post: Post) -> PublishResult:
        """Die vollstaendige Pipeline. Jeder Schritt protokolliert sich."""
        problem = self.preflight(post)
        if problem:
            result = PublishResult(platform=self.platform, ok=False, error=problem)
            self.log(result)
            return result

        if not self.rate_limiter.allow(self.platform):
            result = PublishResult(
                platform=self.platform, ok=False,
                error=f"Rate-Limit erreicht ({self.per_day}/Tag)")
            self.log(result)
            return result

        adapted = self.adapt(post)
        try:
            result = self.publish(adapted)
        except Exception as exc:  # noqa: BLE001
            result = PublishResult(platform=self.platform, ok=False,
                                   error=f"{type(exc).__name__}: {exc}")

        if result.ok:
            self.rate_limiter.record(self.platform)
        self.log(result)
        return result

    def log(self, result: PublishResult) -> None:
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(result.to_json() + "\n")

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        rows = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:]


class NativeAppPipeline(SocialPipeline):
    """Adapter fuer Plattformen, die ueber die native App / Browser laufen.

    Waehrend die Browser-Automation unter Windows bei YouTube 404 liefert
    (dokumentiert im Skill ``youtube-content``), ist der native Weg der
    zuverlaessigere. Dieser Adapter kapselt den Browser-/App-Aufruf, damit
    die Pipeline einheitlich bleibt.
    """

    def publish(self, post: Post) -> PublishResult:
        raise NotImplementedError(
            "Der native Adapter braucht den konkreten Browser-/App-Schritt. "
            "Nutze openamer_cli/browser_real_profile fuer die Autologin-Session.")


def make_platform_plan(platforms: List[str], caption: str,
                       media: Optional[str] = None) -> List[Post]:
    """Erzeugt denselben Beitrag fuer mehrere Plattformen.

    Der Werbetext fuer OpenAmer ist bewusst im Text enthalten — er verweist
    auf github.com/openamer, damit jeder Beitrag zum Download fuehrt.
    """
    base_tags = ["OpenAmer", "OpenAmerAGI", "KI", "AIAgent", "Automation",
                 "ContentAutomation", "SelfImprovingAI"]
    return [Post(text=caption, media_path=media, hashtags=list(base_tags),
                 metadata={"platform": p}) for p in platforms]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Social-Pipeline")
    parser.add_argument("--plan", help="Plattformliste, kommagetrennt")
    parser.add_argument("--caption", help="Text/Beschriftung")
    parser.add_argument("--media", help="Pfad zur Mediendatei")
    parser.add_argument("--log", action="store_true", help="Letzte Uploads zeigen")
    args = parser.parse_args()

    if args.log:
        rows = [json.loads(line) for line in
                (POST_LOG.read_text(encoding="utf-8").splitlines() if POST_LOG.exists() else [])
                if line.strip()]
        for row in rows[-20:]:
            mark = "OK " if row.get("ok") else "ERR"
            print(f"  [{mark}] {row.get('timestamp','')[:19]} {row.get('platform','')}"
                  f" {row.get('error') or row.get('url') or ''}")
        return 0

    platforms = [p.strip() for p in (args.plan or "").split(",") if p.strip()]
    caption = args.caption or ("OpenAmer AGI — dein autonomer KI-Agent. "
                              "Skills, Schwarm, Black-Box-Dashboard. "
                              "Jetzt nutzen: github.com/openamer")
    posts = make_platform_plan(platforms, caption, args.media)
    print(f"{len(posts)} Beitrag(e) vorbereitet fuer: {', '.join(platforms)}")
    for post in posts:
        print(f"  {post.metadata['platform']:10s} {len(post.caption())} Zeichen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
