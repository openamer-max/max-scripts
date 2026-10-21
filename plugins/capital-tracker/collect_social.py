#!/usr/bin/env python3
"""OpenAmer AGI — Social-Stream: echte Plattformmetriken via Chrome-CDP.

by Amer Sacirovic

Liest die Metriken der eingeloggten Plattformen **live** aus dem Browser
ueber das Chrome DevTools Protocol (Port 9222). Der Browser laeuft mit dem
Originalprofil, also mit der echten Session des Nutzers.

Der Stream schreibt echte Zahlen ins Ledger — oder gar nichts. Wenn eine
Plattform nicht erreichbar oder nicht eingeloggt ist, wird kein Wert
erfunden, sondern der Fehler als Ereignis protokolliert.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
SOCIAL_DIR = HOME / "social"
SOCIAL_JOURNAL = SOCIAL_DIR / "platform_metrics.jsonl"
CDP_PORT = int(os.environ.get("OPENAMER_CDP_PORT", "9222"))


# ------------------------------------------------------------------- CDP
def _cdp_available(port: int = CDP_PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _open_tab(url: str, port: int = CDP_PORT) -> Dict[str, Any]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(url, safe='')}",
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read())


def _find_target(tab_id: str, port: int = CDP_PORT, tries: int = 40) -> Dict[str, Any]:
    for _ in range(tries):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as resp:
            targets = json.loads(resp.read())
        for item in targets:
            if item.get("id") == tab_id and item.get("webSocketDebuggerUrl"):
                return item
        time.sleep(0.4)
    return {}


def _evaluate(ws_url: str, expression: str, wait: float = 6.0) -> str:
    """Wertet JavaScript im Tab aus und gibt den Text zurueck."""
    import websocket

    time.sleep(wait)
    ws = websocket.create_connection(ws_url, timeout=30)
    try:
        ws.send(json.dumps({
            "id": 1, "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True,
                       "awaitPromise": True},
        }))
        result: Dict[str, Any] = {}
        for _ in range(40):
            result = json.loads(ws.recv())
            if result.get("id") == 1:
                break
        return (result.get("result", {}).get("result", {}) or {}).get("value", "") or ""
    finally:
        ws.close()


def _page_text(url: str, wait: float = 8.0, port: int = CDP_PORT) -> Tuple[str, str]:
    """Oeffnet einen Tab und liefert (Titel, sichtbarer Text)."""
    tab = _open_tab(url, port)
    target = _find_target(tab["id"], port)
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        return "", ""
    title = target.get("title", "")
    text = _evaluate(ws_url, "document.body ? document.body.innerText : ''", wait)
    return title, text


# ------------------------------------------------------- Plattform-Scraper
def scrape_youtube(wait: float = 9.0) -> List[Dict[str, Any]]:
    """Liest die Kanalmetriken aus dem YouTube-Studio-Dashboard."""
    title, text = _page_text("https://studio.youtube.com/", wait)
    if not text:
        return [{"platform": "youtube", "ok": False,
                 "error": "Studio nicht erreichbar (nicht eingeloggt?)"}]

    rows: List[Dict[str, Any]] = [{"platform": "youtube", "ok": True}]

    subs = re.search(r"Aktuelle Abonnenten\s*\n\s*([\d.]+)", text)
    if subs:
        rows.append({"platform": "youtube", "metric": "followers",
                     "value": float(subs.group(1).replace(".", "").replace(",", "."))})

    views = re.search(r"Aufrufe\s*\n\s*([\d.]+)\s*\n", text)
    if views:
        rows.append({"platform": "youtube", "metric": "views_28d",
                     "value": float(views.group(1).replace(",", "."))})

    watch = re.search(r"Wiedergabezeit \(Stunden\)\s*([\d.]+)", text)
    if watch:
        rows.append({"platform": "youtube", "metric": "watch_hours_28d",
                     "value": float(watch.group(1).replace(",", "."))})

    likes = re.search(r"Likes\s*\n\s*([\d.]+)", text)
    if likes:
        rows.append({"platform": "youtube", "metric": "likes",
                     "value": float(likes.group(1).replace(",", "."))})

    title_match = re.search(r"Beliebteste Inhalte.*?\n(.*?)\n\s*([\d.]+)\s*\n", text, re.S)
    if title_match:
        rows.append({"platform": "youtube", "metric": "top_video_views",
                     "value": float(title_match.group(2).replace(",", ".")),
                     "title": title_match.group(1).strip()[:120]})

    return rows


def scrape_github(wait: float = 8.0) -> List[Dict[str, Any]]:
    """Liest die öffentlichen Repo-/Profilzahlen des eingeloggten Accounts."""
    title, text = _page_text("https://github.com/openamer-max?tab=repositories", wait)
    if not text:
        return [{"platform": "github", "ok": False, "error": "GitHub nicht erreichbar"}]

    rows: List[Dict[str, Any]] = [{"platform": "github", "ok": True}]
    repos = re.search(r"Repositories\s*\n\s*(\d+)", text)
    if repos:
        rows.append({"platform": "github", "metric": "repositories",
                     "value": float(repos.group(1))})
    followers = re.search(r"Followers\s*\n\s*([\d.]+[kKmM]?)", text)
    if followers:
        value = followers.group(1).lower().replace(",", ".")
        mult = 1000 if "k" in value else (1_000_000 if "m" in value else 1)
        rows.append({"platform": "github", "metric": "followers",
                     "value": float(value.rstrip("km")) * mult})
    return rows


def scrape_paypal(wait: float = 9.0) -> List[Dict[str, Any]]:
    """Prueft die PayPal-Anmeldung und liest Einnahmen, falls eingeloggt."""
    title, text = _page_text("https://www.paypal.com/activity/payments", wait)
    if not text:
        return [{"platform": "paypal", "ok": False, "error": "PayPal nicht erreichbar"}]

    if "/signin" in title or "anmelden" in text.lower()[:200] or "log in" in text.lower()[:200]:
        return [{"platform": "paypal", "ok": False,
                 "error": "nicht eingeloggt (Login erfordert Passkey/PIN)"}]

    rows: List[Dict[str, Any]] = [{"platform": "paypal", "ok": True}]
    for label, metric in (("Einnahmen", "revenue"), ("Erhalten", "received"),
                          ("Abgeschickt", "sent")):
        m = re.search(rf"{label}[^\d\-+]{{0,20}}([\d.,]+)\s*(?:EUR|CHF|USD)?", text)
        if m:
            raw = m.group(1).replace(".", "").replace(",", ".")
            try:
                rows.append({"platform": "paypal", "metric": metric,
                             "value": float(raw), "unit": "EUR"})
            except ValueError:
                pass
    return rows


PLATFORMS = {
    "youtube": scrape_youtube,
    "github": scrape_github,
    "paypal": scrape_paypal,
}


def collect(platforms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Liest alle (oder die angegebenen) Plattformen aus."""
    if not _cdp_available():
        return [{"platform": "cdp", "ok": False,
                 "error": f"Chrome-CDP auf Port {CDP_PORT} nicht erreichbar"}]

    rows: List[Dict[str, Any]] = []
    for name, fn in PLATFORMS.items():
        if platforms and name not in platforms:
            continue
        try:
            rows.extend(fn())
        except Exception as exc:  # noqa: BLE001
            rows.append({"platform": name, "ok": False,
                         "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(1.5)
    return rows


def write_journal(rows: List[Dict[str, Any]]) -> Path:
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with SOCIAL_JOURNAL.open("a", encoding="utf-8") as fh:
        for row in rows:
            row = dict(row)
            row["collected_at"] = stamp
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return SOCIAL_JOURNAL


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer Social-Metriken (Chrome CDP)")
    parser.add_argument("--platform", help="nur eine Plattform (youtube|github|paypal)")
    parser.add_argument("--no-write", action="store_true", help="nicht ins Journal schreiben")
    args = parser.parse_args()

    platforms = [args.platform] if args.platform else None
    rows = collect(platforms)

    for row in rows:
        if row.get("metric"):
            print(f"  {row['platform']:9s} {row['metric']:18s} {row.get('value')}")
        elif row.get("ok") is False:
            print(f"  {row['platform']:9s} FEHLER: {row.get('error')}")
        else:
            print(f"  {row['platform']:9s} erreichbar")

    if not args.no_write:
        path = write_journal(rows)
        print(f"\nJournal: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
