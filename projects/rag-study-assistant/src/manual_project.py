"""Portable paths and the provenance of the public demonstration manual."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    source = Path(__file__).resolve().parent
    return source.parent if source.name == "src" else source


def writable_root() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else project_root()


def sample_path() -> Path:
    return project_root() / "data" / "manuals" / "arduino-uno-r3.pdf"


def source_manifest() -> dict:
    return json.loads((project_root() / "data" / "sources.json").read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def describe_source(path: Path) -> dict:
    digest = file_sha256(path)
    known = source_manifest()
    if digest == known["sha256"]:
        return dict(known)
    return {
        "source_id": f"pdf-{digest[:16]}",
        "title": path.stem,
        "publisher": "User-selected document; publisher not recorded",
        "sha256": digest,
        "sections": {},
        "usage_basis": "User-selected local PDF; permission not verified by the application.",
    }
