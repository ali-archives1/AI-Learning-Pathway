"""Shared utilities for PDF validation, chunking, and Ollama HTTP requests."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from config import CHUNK_OVERLAP, CHUNK_SIZE, OLLAMA_BASE_URL


class RAGError(Exception):
    """Base exception with text suitable for display in the application."""


class OllamaConnectionError(RAGError):
    """Raised when the local Ollama service cannot be reached."""


class OllamaResponseError(RAGError):
    """Raised when Ollama returns an invalid or unsuccessful response."""


class PDFProcessingError(RAGError):
    """Raised when a PDF cannot be read or contains no extractable text."""


_DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def ollama_request(
    endpoint: str,
    payload: dict[str, Any] | None = None,
    *,
    method: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    """Call Ollama over its local HTTP API without using system proxies."""

    url = f"{OLLAMA_BASE_URL}{endpoint}"
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method or ("POST" if body is not None else "GET"),
    )
    try:
        with _DIRECT_OPENER.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        message = detail or f"Ollama returned HTTP {exc.code}."
        raise OllamaResponseError(message) from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        raise OllamaConnectionError(
            "Could not connect to Ollama. Open Ollama, wait for it to start, "
            "then select Check status."
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OllamaResponseError("Ollama returned an unreadable response.") from exc
    if isinstance(data, dict) and data.get("error"):
        raise OllamaResponseError(str(data["error"]))
    if not isinstance(data, dict):
        raise OllamaResponseError("Ollama returned an unexpected response.")
    return data


def validate_pdf_path(file_path: str | Path) -> Path:
    """Resolve and validate a user-selected PDF."""

    path = Path(file_path).expanduser().resolve()
    if path.suffix.lower() != ".pdf":
        raise PDFProcessingError("Please select a PDF file.")
    if not path.is_file():
        raise PDFProcessingError("The selected PDF could not be found.")
    if path.stat().st_size == 0:
        raise PDFProcessingError("The selected PDF is empty.")
    return path


def clean_pdf_text(text: str) -> str:
    """Normalize extraction artifacts while keeping useful paragraph breaks."""

    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(
    text: str,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping, word-aware chunks."""

    if overlap < 0 or chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    normalized = clean_pdf_text(text)
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    length = len(normalized)
    while start < length:
        proposed_end = min(start + chunk_size, length)
        end = proposed_end
        if proposed_end < length:
            search_floor = start + int(chunk_size * 0.62)
            candidates = [
                normalized.rfind("\n\n", search_floor, proposed_end),
                normalized.rfind(". ", search_floor, proposed_end),
                normalized.rfind(" ", search_floor, proposed_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (1 if normalized[boundary] == "." else 0)

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break

        next_start = max(end - overlap, start + 1)
        whitespace = normalized.find(" ", next_start, min(end, next_start + 80))
        start = whitespace + 1 if whitespace != -1 else next_start

    return chunks


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object even if a model wrapped it in Markdown fences."""

    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, flags=re.S)
        if not match:
            raise OllamaResponseError("The chat model returned an invalid answer.")
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise OllamaResponseError(
                "The chat model returned an invalid answer. Please try again."
            ) from exc
    if not isinstance(parsed, dict):
        raise OllamaResponseError("The chat model returned an invalid answer.")
    return parsed


def resource_path(relative_name: str) -> Path:
    """Resolve a bundled resource in source and PyInstaller builds."""

    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative_name
