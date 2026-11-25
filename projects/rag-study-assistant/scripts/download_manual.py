"""Download the exact public manual version used by the evaluation set."""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
destination = ROOT / "data" / "manuals" / "arduino-uno-r3.pdf"
if destination.exists():
    payload = destination.read_bytes()
else:
    with urllib.request.urlopen(manifest["official_url"], timeout=60) as response:
        payload = response.read(10 * 1024 * 1024)
if hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
    sys.exit("The publisher's PDF has changed. Keep the old fixture and review/reversion the ground truth; do not silently update it.")
if not destination.exists():
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
print("Verified Arduino UNO R3 manual: 14 pages; SHA-256 matches data/sources.json")
