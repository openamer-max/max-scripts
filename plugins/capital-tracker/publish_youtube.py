#!/usr/bin/env python3
"""OpenAmer AGI — YouTube-Upload-Orchestrator (Werbetext + echter Upload).

by Amer Sacirovic

Nutzt den eingeloggten Chrome (Originalprofil + DevTools-Port 9222) und
verifiziert den Upload am echten DOM. Nutzt ``ad_copy`` fuer den Text und
``youtube_upload`` fuer den Upload-Vorgang.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ad_copy import plan  # noqa: E402
from youtube_upload import upload_youtube  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAmer YouTube-Upload-Orchestrator")
    parser.add_argument("--video", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--privacy", default="Öffentlich")
    args = parser.parse_args()

    description = args.description
    if not description:
        planned = plan(["youtube"], args.title)
        description = planned["youtube"]["description"]

    print(f"Video:        {args.video}")
    print(f"Titel:        {args.title}")
    print(f"Beschreibung: {len(description)} Zeichen")
    print("-" * 62)

    result = upload_youtube(args.video, args.title, description, args.privacy)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
