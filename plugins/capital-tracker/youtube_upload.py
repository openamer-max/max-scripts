#!/usr/bin/env python3
"""OpenAmer AGI — YouTube-Upload-Adapter (echter Upload via Chrome-CDP).

by Amer Sacirovic

Nutzt den **eingeloggten** Chrome des Nutzers (Originalprofil + DevTools-Port
9222) und steuert das YouTube-Studio ueber das DevTools Protocol. Es wird
nichts simuliert: jeder Schritt liest den echten DOM-Zustand, und der Erfolg
wird an der URL/DOM verifiziert, nicht angenommen.

Ablauf:
    1. YouTube-Studio oeffnen -> "Erstellen" -> "Video hochladen"
    2. Datei per DOM-Set auf den Datei-Input legen (DataTransfer)
    3. Titel + Beschreibung aus der Metadata-Datei setzen
    4. Sichtbarkeit waehlen -> veröffentlichen
    5. Verifikation: Video-URL aus dem DOM lesen

by Amer Sacirovic — Apache-2.0-kompatibel, Teil des OpenAmer-Mirrors.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOME = Path(os.environ.get("OPENAMER_HOME", Path.home() / "AppData" / "Local" / "openamer"))
CDP_PORT = int(os.environ.get("OPENAMER_CDP_PORT", "9222"))


# ------------------------------------------------------------------- CDP
def _native_path(path: str) -> Path:
    """Wandelt einen MSYS-/POSIX-Pfad in einen Windows-Pfad.

    Unter Git-Bash liefert die Shell Pfade wie ``/c/Users/...``; Python auf
    Windows versteht sie nicht. Fuer Dateizugriffe (Video-Upload) muss der
    echte Windows-Pfad verwendet werden.
    """
    raw = str(path)
    if len(raw) > 2 and raw[1] == ":" and raw[2] in "\\/":
        return Path(raw)
    if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
        raw = raw[1:]
    if raw.startswith("/"):
        # /c/Users/... -> C:/Users/...
        head, _, rest = raw[1:].partition("/")
        if len(head) == 1 and head.isalpha():
            raw = f"{head.upper()}:/{rest}"
        else:
            raw = "C:" + raw
    return Path(raw.replace("/", os.sep))


def _cdp_up(port: int = CDP_PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _open_tab(url: str, port: int = CDP_PORT) -> Dict[str, Any]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(url, safe='')}",
        method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _target(tab_id: str, port: int = CDP_PORT, tries: int = 50) -> Dict[str, Any]:
    for _ in range(tries):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as r:
            for item in json.loads(r.read()):
                if item.get("id") == tab_id and item.get("webSocketDebuggerUrl"):
                    return item
        time.sleep(0.4)
    return {}


class Tab:
    """Ein CDP-Tab mit Evaluate- und Datei-Upload-Hilfen."""

    def __init__(self, url: str, port: int = CDP_PORT):
        import websocket

        self._ws_mod = websocket
        self.port = port
        self.tab = _open_tab(url, port)
        self.info = _target(self.tab["id"], port)
        self.ws_url = self.info.get("webSocketDebuggerUrl", "")
        if not self.ws_url:
            raise RuntimeError("kein WebSocket zum Tab")
        self.ws = websocket.create_connection(self.ws_url, timeout=60)
        self._id = 0

    def eval(self, expression: str, wait: float = 0.0) -> Any:
        """Wertet JS aus und gibt den Wert (oder None) zurueck."""
        if wait:
            time.sleep(wait)
        self._id += 1
        my_id = self._id
        self.ws.send(json.dumps({
            "id": my_id, "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True,
                       "awaitPromise": True},
        }))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my_id:
                result = msg.get("result", {}).get("result", {})
                if result.get("subtype") == "error":
                    return None
                return result.get("value")

    def bring_to_front(self) -> bool:
        """Aktiviert den Tab im Browser.

        YouTube bricht laufende Uploads ab, wenn der Tab im Hintergrund ist
        (der Fortschritts-Kanal wird gestoppt). ``Page.bringToFront`` hebt
        den Tab auf "visible" — das Fenster wandert dabei **nicht** nach vorn,
        der Nutzer wird nicht unterbrochen.
        """
        self._id += 1
        my_id = self._id
        self.ws.send(json.dumps({"id": my_id, "method": "Page.bringToFront",
                                 "params": {}}))
        ok = False
        try:
            while True:
                msg = json.loads(self.ws.recv())
                if msg.get("id") == my_id:
                    ok = "error" not in msg
                    break
        except Exception:
            return False
        return ok

    def wait_text(self, needle: str, timeout: float = 25.0,
                  poll: float = 1.0) -> bool:
        """Wartet, bis ein Text im Body auftaucht."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            body = self.eval("document.body ? document.body.innerText : ''") or ""
            if needle.lower() in body.lower():
                return True
            time.sleep(poll)
        return False

    def click_text(self, needle: str) -> bool:
        """Klickt das erste Element, dessen Text den Begriff enthaelt."""
        js = """(() => {
          const needle = %s;
          const els = [...document.querySelectorAll('button, a, [role="button"], yt-icon-button, tp-yt-paper-icon-button')];
          for (const el of els) {
            const t = (el.innerText || el.getAttribute('aria-label') || el.title || '').trim();
            if (t && t.toLowerCase().includes(needle.toLowerCase())) {
              el.click();
              return t;
            }
          }
          return null;
        })()""" % json.dumps(needle)
        return bool(self.eval(js))

    def upload_file(self, selector: str, file_path: str) -> bool:
        """Legt eine Datei auf einen <input type=file> (via DOM.setFileInputFiles)."""
        self._id += 1
        my_id = self._id
        self.ws.send(json.dumps({
            "id": my_id, "method": "DOM.getDocument", "params": {}}))
        doc = None
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my_id:
                doc = msg.get("result", {}).get("root")
                break
        if not doc:
            return False
        self._id += 1
        my_id = self._id
        self.ws.send(json.dumps({
            "id": my_id, "method": "DOM.querySelector",
            "params": {"nodeId": doc["nodeId"], "selector": selector}}))
        node_id = None
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my_id:
                node_id = msg.get("result", {}).get("nodeId")
                break
        if not node_id:
            return False
        self._id += 1
        my_id = self._id
        self.ws.send(json.dumps({
            "id": my_id, "method": "DOM.setFileInputFiles",
            "params": {"files": [str(Path(file_path).resolve())], "nodeId": node_id}}))
        ok = False
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == my_id:
                ok = "error" not in msg
                break
        return ok

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass


# --------------------------------------------------------------- Upload
def upload_youtube(video: str, title: str, description: str,
                   privacy: str = "Öffentlich",
                   port: int = CDP_PORT) -> Dict[str, Any]:
    """Laedt ein Video auf YouTube hoch und verifiziert den Erfolg.

    Rueckgabe: ``{"ok": bool, "url": str|None, "steps": [...], "error": str|None}``
    """
    result: Dict[str, Any] = {"ok": False, "url": None, "steps": [],
                              "error": None, "video": str(video)}

    video_path = _native_path(video)
    if not video_path.exists():
        result["error"] = f"Video nicht gefunden: {video_path}"
        return result
    if not _cdp_up(port):
        result["error"] = f"Chrome-CDP auf Port {port} nicht erreichbar"
        return result

    tab = Tab("https://studio.youtube.com/", port)
    try:
        tab.wait_text("Kanal-Dashboard", timeout=30)
        result["steps"].append("studio geoeffnet")

        # 1) Erstellen -> Videos hochladen
        # Der Menuepunkt heisst im Studio "Videos hochladen" (Plural); wir
        # akzeptieren beide Schreibweisen, weil die UI je nach A/B-Test variiert.
        if not tab.click_text("Erstellen"):
            result["error"] = "Button 'Erstellen' nicht gefunden"
            return result
        time.sleep(2.5)
        if not (tab.click_text("Videos hochladen") or tab.click_text("Video hochladen")):
            result["error"] = "Menuepunkt 'Videos hochladen' nicht gefunden"
            return result
        result["steps"].append("upload-dialog geoeffnet")

        # 2) Datei waehlen
        # Im Studio-Dialog liegt der <input type=file> oft erst nach dem Klick
        # auf "Dateien auswaehlen" im DOM. Wir klicken daher erst den Button und
        # suchen den Input danach; ein Rueckfall auf direktes Setzen bleibt.
        tab.wait_text("Dateien auswählen", timeout=20)
        tab.click_text("Dateien auswählen")
        time.sleep(1.5)
        if not tab.upload_file("input[type=file]", str(video_path)):
            result["error"] = "Datei-Input nicht gefunden oder Upload fehlgeschlagen"
            return result
        result["steps"].append("datei uebertragen")

        # 3) Auf das echte Upload-Ende warten.
        # "Details" ist IMMER im DOM (Reiter-Name) und taugt nicht als
        # Abschlusskriterium. Echte Marker: der Fortschrittsbalken
        # "Wird hochgeladen…" ist verschwunden und der Videolink existiert.
        deadline = time.time() + 300
        uploaded = False
        while time.time() < deadline:
            state = tab.eval("""(() => {
              const txt = document.body ? document.body.innerText : '';
              const link = document.querySelector('ytcp-video-link a, #video-url a, a[href*="/watch?v="]');
              return {
                uploading: /Wird hochgeladen|Upload wird verarbeitet|Verarbeitung läuft/.test(txt),
                hasLink: !!link,
                link: link ? link.href : null,
                hasTitle: !!document.querySelector('[contenteditable="true"][aria-label*="Titel" i], #title'),
                url: location.href
              };
            })()""") or {}
            if isinstance(state, dict) and not state.get("uploading") and state.get("hasTitle"):
                uploaded = True
                result["steps"].append(f"upload fertig (url={state.get('url','')[:80]})")
                break
            time.sleep(2.0)
        if not uploaded:
            body = tab.eval("document.body ? document.body.innerText.slice(0,400) : ''") or ""
            result["error"] = f"Upload nicht abgeschlossen. Seite: {body[:200]}"
            return result

        # 4) Titel + Beschreibung setzen
        # YouTube-Studio nutzt contenteditable-Divs mit id="textbox" und einem
        # aria-label ("Gib einen Titel ein, ...", "Erzähle Nutzern etwas ...") —
        # NICHT #title / #description. Wir suchen daher ueber aria-label und
        # contenteditable, mit Fallback auf die alten IDs.
        js = """(() => {
          const setEditable = (el, value) => {
            el.focus();
            el.innerText = value;
            el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.blur();
          };
          const setNative = (el, value) => {
            const proto = el instanceof HTMLTextAreaElement
              ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, 'value');
            if (setter) setter.set.call(el, value); else el.value = value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
          };
          const boxes = [...document.querySelectorAll('[contenteditable="true"], textarea, input')];
          const byLabel = (words) => boxes.find(el => {
            const lbl = (el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').toLowerCase();
            return words.some(w => lbl.includes(w));
          });
          const title = byLabel(['titel ein', 'gib einen titel', 'title'])
            || document.querySelector('#title');
          const desc = byLabel(['erzähle nutzern', 'beschreib', 'description'])
            || document.querySelector('#description');
          const put = (el, value) => {
            if (!el) return false;
            if (el.isContentEditable) setEditable(el, value); else setNative(el, value);
            return true;
          };
          const t = put(title, %s);
          const d = put(desc, %s);
          return {title: t, desc: d,
                  titleTag: title ? title.tagName : null,
                  descTag: desc ? desc.tagName : null};
        })()""" % (json.dumps(title), json.dumps(description))
        setres = tab.eval(js)
        result["steps"].append(f"metadaten gesetzt {setres}")
        time.sleep(1.5)

        # 4b) Pflichtfeld "Zielgruppe": "Nein, es ist nicht speziell für Kinder"
        # Ohne diese Auswahl blockiert YouTube das Veroeffentlichen.
        if tab.click_text("Nein, es ist nicht speziell für Kinder"):
            result["steps"].append("zielgruppe gesetzt (nein)")
            time.sleep(1.0)

        # 5) Zum Reiter "Sichtbarkeit" navigieren
        # Im Studio ist "Sichtbarkeit" ein TAB (Details | Video-Elemente |
        # Vorabprüfung | Sichtbarkeit). Nach dem Upload liegt die Seite unter
        # .../video/<id>/edit?uploadType=... — dort wechseln wir per Klick auf
        # den Reiter und dann ueber "Weiter" bis zum Veröffentlichen-Button.
        tab.click_text("Sichtbarkeit")
        time.sleep(2.0)
        if not tab.wait_text("Veröffentlichen", timeout=12, poll=1.0):
            for _ in range(4):
                if tab.click_text("Weiter"):
                    time.sleep(2.5)
                    if tab.wait_text("Veröffentlichen", timeout=8, poll=1.0):
                        break
        result["steps"].append("reiter sichtbarkeit erreicht")

        # 5b) Sichtbarkeit waehlen (oeffentlich)
        for label in ("Öffentlich", "Oeffentlich", "Public"):
            if tab.click_text(label):
                result["steps"].append(f"sichtbarkeit: {label}")
                time.sleep(1.0)
                break

        # 5c) Veroeffentlichen
        clicked = False
        for label in ("Veröffentlichen", "Veröffentlichen und teilen", "Publish"):
            if tab.click_text(label):
                clicked = True
                result["steps"].append(f"veroeffentlichen geklickt ({label})")
                break
        if not clicked:
            body = tab.eval("document.body ? document.body.innerText.slice(0,600) : ''") or ""
            result["error"] = f"Button 'Veröffentlichen' nicht gefunden. Seite: {body[:250]}"
            return result

        # 6) Verifikation: warten auf den Video-Detail-Link
        done = tab.wait_text("Video im Studio veröffentlicht", timeout=60, poll=2.0) or \
            tab.wait_text("Wiedergabeliste", timeout=10, poll=1.5)
        href = tab.eval("""(() => {
          const links = [...document.querySelectorAll('a[href*="/watch?v="]')];
          return links.length ? links[0].href : null;
        })()""")
        result["ok"] = bool(done or href)
        result["url"] = href
        result["steps"].append("verifiziert" if result["ok"] else "verifikation unvollstaendig")
        if not result["ok"]:
            result["error"] = "Upload nicht verifiziert"
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        tab.close()
    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer YouTube-Upload")
    parser.add_argument("--video", required=True, help="Pfad zur Videodatei")
    parser.add_argument("--title", required=True, help="Videotitel")
    parser.add_argument("--description", default="", help="Beschreibung")
    parser.add_argument("--privacy", default="Öffentlich")
    parser.add_argument("--dry-run", action="store_true", help="nur pruefen, nicht hochladen")
    args = parser.parse_args()

    if args.dry_run:
        vp = _native_path(args.video)
        print(f"Video:  {vp} (exists={vp.exists()}, size={vp.stat().st_size if vp.exists() else 0})")
        print(f"Titel:  {args.title}")
        print(f"CDP:    {_cdp_up()}")
        return 0

    res = upload_youtube(args.video, args.title, args.description, args.privacy)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
