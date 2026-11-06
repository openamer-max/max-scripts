#!/usr/bin/env python3
"""verify-upload-status.py - prueft, ob die Upload-Pipeline vollstaendig ist.

Portabel: keine fest verdrahteten Windows-Pfade. Alles relativ zum Repo oder
per Option/Umgebungsvariable gesetzt.

Beim frueheren Stand waren drei Dinge kaputt:
  1. absolute Pfade wie "/c/Users/amer7/..." (existieren nur auf diesem Rechner)
  2. `f.endswith(".mp4" if False else ".mp4|avi")` -- eine Endung, die es nie gibt,
     also wurde IMMER 0 Videos gezaehlt
  3. Ausgabe behauptete "READY" und "Executing IMMEDIATELY", ohne etwas zu pruefen

Exitcode: 0 = alles vorhanden, 1 = etwas fehlt.

Usage:
    python scripts/verify-upload-status.py [--video-dir DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Echte Video-Endungen als Tupel -- kein Pseudo-Regex in str.endswith()
VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm")

REQUIRED_FILES = {
    "Upload-Skript": "scripts/ultimate_upload_boost.sh",
    "Viral-Strategie": "docs/viral-growth-strategy.md",
    "Upload-Pipeline": "docs/upload-pipeline.md",
}


def native_path(raw: str) -> Path:
    """Wandelt MSYS-/Git-Bash-Pfade (/c/Users/...) in Windows-Pfade (C:/Users/...).

    Ohne das wird aus "/c/Users/x" unter Windows "\\c\\Users\\x" und existiert nie.
    """
    s = str(raw).strip()
    if re.match(r"^/[A-Za-z]/", s):
        s = f"{s[1].upper()}:/{s[3:]}"
    return Path(s).expanduser()


def count_videos(directory: Path) -> int:
    """Zaehlt Videodateien korrekt -- auch bei gemischten Endungen."""
    try:
        return sum(1 for p in directory.iterdir()
                   if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload-Pipeline pruefen")
    ap.add_argument(
        "--video-dir",
        default=os.environ.get("OPENAMER_VIDEO_DIR", str(Path.home() / "social-media" / "videos" / "content_batch_04")),
        help="Verzeichnis mit den Videos (Default: $OPENAMER_VIDEO_DIR oder ~/social-media/videos/content_batch_04)",
    )
    ap.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    args = ap.parse_args()

    checks: dict[str, dict] = {}
    for label, rel in REQUIRED_FILES.items():
        path = REPO_ROOT / rel
        checks[label] = {"ok": path.is_file(), "path": str(path)}

    video_dir = native_path(args.video_dir)
    videos = count_videos(video_dir)
    checks["Video-Verzeichnis"] = {
        "ok": video_dir.is_dir(),
        "path": str(video_dir),
        "videos": videos,
    }

    all_ok = all(c["ok"] for c in checks.values()) and videos > 0

    if args.json:
        print(json.dumps({"ok": all_ok, "checks": checks}, indent=2, ensure_ascii=False))
        return 0 if all_ok else 1

    print("Upload-Pipeline - Ist-Stand")
    print("=" * 62)
    for label, c in checks.items():
        mark = "OK  " if c["ok"] else "FEHLT"
        extra = f"  ({c['videos']} Videos)" if "videos" in c else ""
        print(f"[{mark}] {label:<20} {c['path']}{extra}")
    print("=" * 62)

    if all_ok:
        print(f"Bereit: {videos} Video(s) gefunden, alle Bausteine vorhanden.")
        print("Naechster Schritt: scripts/ultimate_upload_boost.sh erzeugt das Manifest.")
        return 0

    if videos == 0:
        print("Keine Videos gefunden -- Upload ist damit nicht moeglich.")
    missing = [k for k, c in checks.items() if not c["ok"]]
    if missing:
        print("Fehlende Bausteine: " + ", ".join(missing))
    print("Status: NICHT bereit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
