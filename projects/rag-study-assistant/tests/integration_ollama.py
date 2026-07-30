"""End-to-end checks against the installed local Ollama models."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from config import NOT_FOUND_RESPONSE  # noqa: E402
from rag_engine import RAGEngine  # noqa: E402
from test_data.create_biology_pdf import create_test_pdf  # noqa: E402


def compact_result(result: object) -> dict[str, object]:
    data = asdict(result)
    data["chunks"] = [
        {
            "page": chunk["page"],
            "score": round(chunk["score"], 4),
            "text_preview": chunk["text"][:140],
        }
        for chunk in data["chunks"]
    ]
    return data


def run() -> int:
    pdf_path = create_test_pdf(PROJECT_ROOT / "test_data" / "biology_test.pdf")
    engine = RAGEngine()
    status = engine.check_status()
    assert status.connected, status.error
    assert status.chat_available, "Required chat model is missing."
    assert status.embedding_available, "Required embedding model is missing."

    progress_log: list[tuple[int, str]] = []
    summary = engine.process_pdf(
        pdf_path,
        progress_callback=lambda value, message: progress_log.append((value, message)),
    )
    assert summary.page_count == 4
    assert summary.chunk_count >= 4

    direct = engine.ask("Which organelle generates most of a cell's ATP?")
    assert direct.found, direct.answer
    assert "mitochond" in direct.answer.lower(), direct.answer
    assert 2 in direct.source_pages, direct.source_pages

    missing = engine.ask("According to this document, who painted the Mona Lisa?")
    assert not missing.found, missing.answer
    assert missing.answer == NOT_FOUND_RESPONSE, missing.answer
    assert missing.source_pages == (), missing.source_pages

    follow_up = engine.ask("What are its inner membrane folds called?")
    assert follow_up.found, follow_up.answer
    assert "cristae" in follow_up.answer.lower(), follow_up.answer
    assert 2 in follow_up.source_pages, follow_up.source_pages

    output = {
        "status": asdict(status),
        "pdf_summary": asdict(summary),
        "progress_events": len(progress_log),
        "direct_question": compact_result(direct),
        "missing_information_question": compact_result(missing),
        "follow_up_question": compact_result(follow_up),
    }
    result_path = PROJECT_ROOT / "test_data" / "integration_results.json"
    result_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
