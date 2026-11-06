#!/usr/bin/env bash
#
# ultimate_upload_boost.sh - erzeugt ein Upload-Manifest fuer eine Video-Charge.
#
# Das Skript laedt NICHTS selbst hoch. Es prueft die Charge, zieht optional
# Captions aus einer Metadata-Datei, schreibt pro Video eine .caption.txt und
# ein JSON-Manifest. Dieses Manifest ist die Eingabe fuer den Upload-Agenten
# (Chrome/CDP mit bereits angemeldetem Profil).
#
# Bewusst NICHT enthalten: erfundene Reichweitenversprechen. Dieses Werkzeug
# kann keine Likes, Follower oder Umsatz garantieren.
#
# Usage:
#   ./ultimate_upload_boost.sh [--video-dir DIR] [--metadata FILE] [--out FILE] [--dry-run]
#
set -euo pipefail

video_dir="${OPENAMER_VIDEO_DIR:-$HOME/social-media/videos/content_batch_04}"
metadata_file="${OPENAMER_METADATA_FILE:-}"
out_file=""
dry_run=0

while [ $# -gt 0 ]; do
  case "$1" in
    --video-dir)  video_dir="${2:?--video-dir braucht einen Wert}"; shift 2 ;;
    --metadata)   metadata_file="${2:?--metadata braucht einen Wert}"; shift 2 ;;
    --out)        out_file="${2:?--out braucht einen Wert}"; shift 2 ;;
    --dry-run)    dry_run=1; shift ;;
    -h|--help)    sed -n '2,20p' "$0"; exit 0 ;;
    *)            echo "Unbekannte Option: $1" >&2; exit 2 ;;
  esac
done

if [ ! -d "$video_dir" ]; then
  echo "FEHLER: Video-Verzeichnis existiert nicht: $video_dir" >&2
  echo "        Setze OPENAMER_VIDEO_DIR oder --video-dir." >&2
  exit 1
fi

if [ -z "$out_file" ]; then
  out_file="$video_dir/upload_manifest.json"
fi

# Videos sammeln (echte Endungen, keine Pseudo-Regex-Tricks)
shopt -s nullglob
videos=()
for f in "$video_dir"/*.mp4 "$video_dir"/*.mov "$video_dir"/*.m4v "$video_dir"/*.webm; do
  [ -f "$f" ] && videos+=("$f")
done
shopt -u nullglob

if [ ${#videos[@]} -eq 0 ]; then
  echo "Keine Videos in $video_dir gefunden (.mp4/.mov/.m4v/.webm)."
  echo "Manifest wird trotzdem geschrieben (leer)."
fi

echo "Charge      : $video_dir"
echo "Videos      : ${#videos[@]}"
echo "Metadata    : ${metadata_file:-(keine)}"
echo "Manifest    : $out_file"
echo ""

json_escape() {
  # Backslashes und Quotes maskieren, Zeilenumbrueche entfernen
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n\r'
}

human_lines=""

{
  printf '{\n'
  printf '  "generated_at": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '  "video_dir": "%s",\n' "$(json_escape "$video_dir")"
  printf '  "metadata_file": "%s",\n' "$(json_escape "${metadata_file:-}")"
  printf '  "video_count": %d,\n' "${#videos[@]}"
  printf '  "videos": [\n'
  first=1
  for f in "${videos[@]}"; do
    name="$(basename "$f")"
    stem="${name%.*}"
    size="$(wc -c <"$f" | tr -d ' ')"
    caption_file=""
    if [ -n "$metadata_file" ] && [ -f "$metadata_file" ]; then
      caption_file="$video_dir/${stem}.caption.txt"
      if [ "$dry_run" -eq 0 ]; then
        {
          echo "# Caption-Vorschlag fuer ${stem}"
          echo "# Quelle: $(basename "$metadata_file")"
          echo
          sed -n '1,40p' "$metadata_file"
        } >"$caption_file"
      fi
    fi
    if [ "$first" -eq 1 ]; then first=0; else printf ',\n'; fi
    printf '    {"file": "%s", "bytes": %s, "caption": "%s"}' \
      "$(json_escape "$name")" "$size" "$(json_escape "$caption_file")"
    human_lines="${human_lines}  - ${name} (${size} Bytes)${caption_file:+ -> $caption_file}
"
  done
  printf '\n  ]\n}\n'
} >"$out_file"

# Menschenlesbare Liste NACH dem JSON ausgeben (darf nicht in die Datei geraten)
[ -n "$human_lines" ] && printf '%s' "$human_lines"

echo ""
echo "Manifest geschrieben: $out_file"
echo ""
echo "Naechster Schritt (durch den Agenten, nicht durch dieses Skript):"
echo "  1. Chrome mit angemeldetem Profil + CDP starten (Port 9222)"
echo "  2. Je Video: YouTube Studio / TikTok / Instagram Reels oeffnen"
echo "  3. Datei per DOM.setFileInputFiles setzen, Caption aus dem Manifest einsetzen"
echo "  4. Veroeffentlichung nur nach ausdruecklicher Freigabe"
