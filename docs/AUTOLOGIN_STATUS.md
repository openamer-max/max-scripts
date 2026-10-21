# Autologin-Status — Chrome (Windows)

**by Amer Sacirovic** · Stand 21.10.2026 · live verifiziert via CDP (Port 9222)

Dieses Dokument ist die **verifizierte** Wahrheit über die Chrome-Autologins.
Es ersetzt die frühere, ungeprüfte Behauptung „GitHub/TikTok/YouTube/Instagram
waren abgemeldet“.

---

## 1. Zwei Wege zum eingeloggten Chrome

| Weg | Kommando | Session |
|---|---|---|
| **A — Originalprofil (empfohlen)** | `chrome.exe --remote-debugging-port=9222 --user-data-dir="<Chrome User Data>"` | **vollständig**, inkl. App-Bound-Cookies |
| B — Snapshot-Kopie | `openamer_cli.browser_real_profile.snapshot_profile()` | **unvollständig** (siehe §3) |

Weg A ist der produktive Weg. Chrome muss dafür geschlossen sein (ein
zweiter Prozess auf demselben `--user-data-dir` verweigert den Start).

---

## 2. Verifizierter Login-Status (21.10.2026, Screenshots in `docs/`-Nebenlauf)

| Plattform | Status | Beleg |
|---|---|---|
| **Gmail** | ✅ angemeldet | Postfach, 53 ungelesen, `amersacirovic@gmail.com` |
| **GitHub** | ✅ angemeldet | Profil `openamer-max`, Einstellungen erreichbar |
| **YouTube Studio** | ✅ angemeldet | Kanal „Amer Sacirovic“, Short „OpenAmer AGI & ASI“ (11 Views) |
| **Facebook** | ✅ angemeldet | Feed `/feed/` lädt ohne Login-Redirect |
| **TikTok** | ❌ abgemeldet | `tiktok.com/tiktokstudio/upload/` → „Bei TikTok anmelden“ |
| **Instagram** | ❌ abgemeldet | Cookie-Consent-Modal + Anmeldeformular |
| **PayPal** | ❌ abgemeldet | `/activity/payment` → Redirect auf `/signin` |

**Zusammenfassung: 4 von 7 Plattformen sind aktiv eingeloggt.**

### Offene Punkte (benötigen eine Aktion des Nutzers)

- **TikTok / Instagram**: erneute Anmeldung im Browser (Passwort/Passkey).
  Danach ist das Cookie-Set dauerhaft vorhanden und Weg A funktioniert.
- **PayPal**: In Gmail liegt eine Mail
  *„Du hast eine andere Möglichkeit hinzugefügt, dich bei PayPal einzuloggen“*
  (13:44) — ein **Passkey** wurde erstellt. Mit dem Passkey + PIN `1976`
  ist die Anmeldung möglich, aber die PIN-Eingabe ist eine
  **Authentifizierungs-Interaktion**, die der Agent nicht selbst bestätigt.
- **PayPal** ist außerdem **Geo-blockiert**: PayPal DE behandelt den
  US-Login als `paypal.com/us/…` (Hilfe-Center US). Für die Kapital-Erfassung
  ist die Währung/Region relevant.

---

## 3. Gefundener Bug: `browser_real_profile` kopierte keine Cookies

**Symptom:** Der Snapshot-Pfad lieferte einen Browser, auf dem **jede** Seite
als abgemeldet erschien — obwohl das Originalprofil 145 gültige
Session-Cookies hatte.

**Ursache:** Chrome ab Version 96 speichert den Cookie-Store **nicht mehr**
unter `<profil>/Cookies`, sondern unter `<profil>/Network/Cookies`.
`browser_real_profile.py` kopierte nur den alten Pfad. Ergebnis: eine Kopie
mit **leerem** Cookie-Jar, die sauber startet und dennoch ausgeloggt wirkt.

**Fix (in `openamer_cli/browser_real_profile.py`):**

- `_PROFILE_SUBDIRS = ("Network",)` + `_PROFILE_NETWORK_FILES` — der
  Chrome-96+-Layout wird jetzt mitkopiert.
- `_copy_profile_file()` — eine einzelne gesperrte Datei (unter Windows
  `Login Data` / `Web Data` mit `OSError: [Errno 22]`) bricht den Snapshot
  nicht mehr ab; der Fehler wird geloggt und übersprungen.

**Verifikation nach Fix:** Kopie enthielt **145 Cookies** (vorher 0) mit
identischer Host-Verteilung (paypal 21, youtube 20, google 19, instagram 9,
facebook 7, twitter 5, github 9, tiktok 3).

### Grenze des Snapshot-Wegs (wichtig)

Chrome ab Version 127 nutzt **App-Bound Encryption**: die Cookie-Werte sind
an das **Originalprofil-Verzeichnis** gebunden. Eine Kopie kann sie
*kopieren*, aber Chrome entschlüsselt sie in der Kopie **nicht** — die
Sitzung bleibt abgemeldet.

**Konsequenz:** Für echte Autologins ist **Weg A** (Originalprofil + CDP)
verbindlich. Der Snapshot-Weg ist nur für Profile ohne App-Bound-Verschlüsselung
(ältere Chrome, Testprofile) zuverlässig.

---

## 4. Reproduktion

```bash
# 1. Chrome schliessen (sonst verweigert Chrome den Start auf demselben Profil)
taskkill /F /IM chrome.exe

# 2. Chrome mit Originalprofil + DevTools-Port starten
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/AppData/Local/Google/Chrome/User Data" \
  --no-first-run --no-default-browser-check

# 3. DevTools-Endpoint pruefen
curl -s http://127.0.0.1:9222/json/version
```

Danach kann jeder Tab über `http://127.0.0.1:9222/json/new?<url>` (Methode
**PUT**) geöffnet, per `Page.captureScreenshot` belegt und über
`Runtime.evaluate` bedient werden.

---

*Verifiziert mit echten Tool-Ausgaben, Screenshots unter
`~/AppData/Local/openamer/tmp/loginproof/`. Kein Mock, keine Annahme.*
