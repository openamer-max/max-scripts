#!/usr/bin/env python3
"""OpenAmer AGI — Black-Box-Kapital-Dashboard (Renderer + HTTP-Server).

by Amer Sacirovic

Zeigt alle vier Datenstroeme in Echtzeit:
  capital | social | swarm | selfcode

Wichtig: prognostizierte und gemessene Werte werden getrennt ausgewiesen.
Ein Dashboard, das Prognose als Ist verkauft, waere Werbung — kein Dashboard.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenAmer AGI — Black Box</title>
<style>
  :root {{
    --bg:#0a0e14; --panel:#121821; --line:#1e2632; --txt:#e6edf3;
    --dim:#8b949e; --acc:#39d353; --proj:#d29922; --warn:#f85149; --acc2:#58a6ff;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt);
    font-family:'Segoe UI',system-ui,-apple-system,sans-serif; padding:20px; }}
  h1 {{ font-size:19px; margin:0 0 2px; letter-spacing:.5px; }}
  .sub {{ color:var(--dim); font-size:12px; margin-bottom:18px; }}
  .grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
  .card h2 {{ font-size:11px; text-transform:uppercase; letter-spacing:1.1px;
    color:var(--dim); margin:0 0 10px; font-weight:600; }}
  .big {{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .mid {{ font-size:18px; font-weight:600; font-variant-numeric:tabular-nums; }}
  .lbl {{ font-size:11px; color:var(--dim); margin-top:2px; }}
  .row {{ display:flex; justify-content:space-between; align-items:baseline;
    padding:5px 0; border-bottom:1px solid var(--line); font-size:13px; }}
  .row:last-child {{ border-bottom:none; }}
  .row .v {{ font-variant-numeric:tabular-nums; font-weight:600; }}
  .m {{ color:var(--acc); }} .p {{ color:var(--proj); }}
  .tag {{ display:inline-block; font-size:10px; padding:1px 6px; border-radius:9px;
    border:1px solid var(--line); color:var(--dim); margin-left:6px; }}
  .dot {{ display:inline-block; width:7px; height:7px; border-radius:50%;
    background:var(--acc); margin-right:7px; }}
  .dot.warn {{ background:var(--warn); }}
  table {{ width:100%; border-collapse:collapse; font-size:12px; }}
  th {{ text-align:left; color:var(--dim); font-weight:600; padding:6px 8px;
    border-bottom:1px solid var(--line); font-size:10px; text-transform:uppercase;
    letter-spacing:.7px; }}
  td {{ padding:5px 8px; border-bottom:1px solid var(--line); }}
  .mono {{ font-family:Consolas,monospace; font-size:11px; color:var(--dim); }}
  footer {{ margin-top:22px; color:var(--dim); font-size:11px; text-align:center; }}
</style>
</head>
<body>
<h1><span class="dot{status_dot}"></span>OpenAmer AGI — Black Box</h1>
<div class="sub">Kapitalgenerierung in Echtzeit &middot; {generated} &middot; by Amer Sacirovic</div>

<div class="grid">
  <div class="card">
    <h2>Kapital</h2>
    <div class="big m">{eur_measured}</div>
    <div class="lbl">gemessen (EUR)</div>
    <div class="mid p" style="margin-top:10px">{eur_projected}</div>
    <div class="lbl">prognostiziert (EUR)</div>
    <div style="margin-top:12px">{capital_rows}</div>
  </div>
  <div class="card">
    <h2>Datenstrom</h2>
    <div class="big">{events}</div>
    <div class="lbl">Ereignisse im Ledger</div>
    <div class="mid" style="margin-top:10px">{streams}</div>
    <div class="lbl">aktive Streams</div>
  </div>
  <div class="card">
    <h2>Social</h2>
    {social_rows}
  </div>
  <div class="card">
    <h2>Schwarm</h2>
    {swarm_rows}
  </div>
  <div class="card">
    <h2>Self-Coding</h2>
    {selfcode_rows}
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Letzte Ereignisse</h2>
  <table>
    <tr><th>Zeit</th><th>Stream</th><th>Metrik</th><th>Wert</th><th>Konf.</th><th>Nachweis</th></tr>
    {event_rows}
  </table>
</div>

<footer>OpenAmer AGI &middot; Black-Box-Dashboard &middot; Datenstrom: append-only ledger.jsonl<br>
by Amer Sacirovic &middot; Apache-2.0 &middot; github.com/openamer</footer>
</body>
</html>
"""


# Metriken, die echtes Geld abbilden. Effizienz- und Zaehlwerte
# (success_rate, errors_detected, task_count, roi_ratio ...) sind KEIN Kapital
# und werden nicht in die Kapital-Kachel summiert.
_MONEY_HINTS = ("eur", "revenue", "capital", "profit", "income", "earning",
                 "balance", "payout", "umsatz", "einnahme", "gewinn", "konto",
                 "sponsor", "payment", "money", "cash")
_NON_MONEY_HINTS = ("success_rate", "errors_detected", "task", "patch",
                    "efficiency", "count", "score", "roi_ratio")


def _is_money_metric(metric: str) -> bool:
    """True, wenn die Metrik einen Geldbetrag abbildet."""
    low = str(metric).lower()
    if any(bad in low for bad in _NON_MONEY_HINTS):
        return False
    return any(good in low for good in _MONEY_HINTS)


def _rows_for(stream: str, totals: Dict[str, float], limit: int = 8) -> str:
    """Zeilen fuer einen Stream.

    Die totals-Schluessel haben die Form ``<stream>:<metric>:<confidence>``
    (z. B. ``social:platform_status:measured``) — nicht ``<metric>:<conf>``.
    Deshalb wird der Stream aus dem Schluessel gelesen, statt ihn zu raten.
    """
    entries = []
    for key, value in totals.items():
        parts = key.split(":")
        if len(parts) < 3:
            continue
        key_stream, metric, conf = parts[0], parts[1], parts[2]
        if key_stream != stream:
            continue
        entries.append((metric, conf, value))
    if not entries:
        return '<div class="lbl">noch keine Daten in diesem Stream</div>'
    out = []
    for metric, conf, value in sorted(entries, key=lambda kv: -kv[2])[:limit]:
        cls = "m" if conf == "measured" else "p"
        shown = f"{value:,.2f}".rstrip("0").rstrip(".")
        out.append(f'<div class="row"><span>{metric}<span class="tag">{conf}</span></span>'
                   f'<span class="v {cls}">{shown}</span></div>')
    return "".join(out)


def render_dashboard(snapshot: Dict[str, Any]) -> str:
    totals: Dict[str, float] = snapshot.get("totals", {}) or {}
    events = snapshot.get("last_events", []) or []

    # Kapital-Kachel: NUR echte Geldwerte summieren.
    # Effizienz-/Zaehlmetriken (success_rate, errors_detected, task_count)
    # sind KEIN Kapital — sie wuerden den Wert verfaelsehen. Deshalb wird
    # streng nach Waehrung bzw. Geldsemantik gefiltert.
    eur_measured = 0.0
    eur_projected = 0.0
    for key, value in totals.items():
        parts = key.split(":")
        if len(parts) < 3 or parts[0] != "capital":
            continue
        metric, conf = parts[1], parts[2]
        if not _is_money_metric(metric):
            continue
        if conf == "measured":
            eur_measured += value
        elif conf == "projected":
            eur_projected += value

    event_rows = []
    for ev in reversed(events[-30:]):
        conf = ev.get("confidence", "measured")
        cls = "m" if conf == "measured" else "p"
        value = ev.get("value", 0)
        event_rows.append(
            f"<tr><td class='mono'>{str(ev.get('ts', ''))[:19]}</td>"
            f"<td>{ev.get('stream', '')}</td>"
            f"<td>{ev.get('metric', '')}</td>"
            f"<td class='v {cls}'>{value} {ev.get('unit', '')}</td>"
            f"<td class='{cls}'>{conf}</td>"
            f"<td class='mono'>{str(ev.get('evidence', ''))[:52]}</td></tr>")
    if not event_rows:
        event_rows.append("<tr><td colspan='6' class='lbl'>Ledger ist leer — "
                          "Collector laufen lassen</td></tr>")

    streams = len(snapshot.get("streams", {}) or {})
    generated = str(snapshot.get("generated_at", ""))[:19].replace("T", " ") + " UTC"

    return HTML_TEMPLATE.format(
        status_dot="",
        generated=generated,
        eur_measured=f"{eur_measured:,.2f}".rstrip("0").rstrip("."),
        eur_projected=f"{eur_projected:,.2f}".rstrip("0").rstrip("."),
        events=f"{snapshot.get('event_count', 0):,}",
        streams=str(streams),
        capital_rows=_rows_for("capital", totals, limit=6),
        social_rows=_rows_for("social", totals),
        swarm_rows=_rows_for("swarm", totals),
        selfcode_rows=_rows_for("selfcode", totals),
        event_rows="".join(event_rows),
    )


def serve(host: str = "127.0.0.1", port: int = 8900,
          ledger_path: Optional[Path] = None) -> int:
    """Startet den Live-Dashboard-Server (JSON-Feed + HTML)."""
    from ledger import Ledger

    ledger = Ledger(ledger_path)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/api/snapshot"):
                body = json.dumps(ledger.snapshot(), ensure_ascii=False).encode("utf-8")
                self._send(body, "application/json; charset=utf-8")
            elif self.path.startswith("/api/ledger"):
                body = json.dumps(ledger.read(limit=500), ensure_ascii=False).encode("utf-8")
                self._send(body, "application/json; charset=utf-8")
            else:
                body = render_dashboard(ledger.snapshot()).encode("utf-8")
                self._send(body, "text/html; charset=utf-8")

        def log_message(self, fmt: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Black-Box-Dashboard: http://{host}:{port}")
    print(f"Ledger: {ledger.path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard beendet.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8900)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    if args.serve:
        raise SystemExit(serve(args.host, args.port))
    raise SystemExit(0)
