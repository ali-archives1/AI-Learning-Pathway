"""Windows desktop entry point for the RAG Study Assistant."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from config import APP_NAME, APP_VERSION, NOT_FOUND_RESPONSE
from main_window import MainWindow
from rag_engine import RAGEngine
from styles import load_preferred_font, make_app_icon


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--screenshot", type=str, default="")
    parser.add_argument("--integration-test", type=str, default="")
    parser.add_argument("--test-output", type=str, default="")
    return parser.parse_args()


def run_packaged_integration(pdf_path: str, output_path: str) -> int:
    """Exercise the bundled backend; used only by release verification."""

    report: dict[str, object] = {"passed": False}
    try:
        engine = RAGEngine()
        status = engine.check_status()
        if not (
            status.connected
            and status.chat_available
            and status.embedding_available
        ):
            raise RuntimeError(status.error or "Required Ollama models are unavailable.")
        summary = engine.process_pdf(pdf_path)
        direct = engine.ask("Which organelle generates most of a cell's ATP?")
        missing = engine.ask(
            "According to this document, who painted the Mona Lisa?"
        )
        follow_up = engine.ask("What are its inner membrane folds called?")
        checks = {
            "pdf_loaded": summary.page_count == 4 and summary.chunk_count >= 4,
            "direct_answer": (
                direct.found
                and "mitochond" in direct.answer.lower()
                and 2 in direct.source_pages
            ),
            "missing_information": (
                not missing.found
                and missing.answer == NOT_FOUND_RESPONSE
                and not missing.source_pages
            ),
            "follow_up_memory": (
                follow_up.found
                and "cristae" in follow_up.answer.lower()
                and 2 in follow_up.source_pages
            ),
        }
        report = {
            "passed": all(checks.values()),
            "checks": checks,
            "status": asdict(status),
            "pdf_summary": asdict(summary),
            "direct_question": asdict(direct),
            "missing_information_question": asdict(missing),
            "follow_up_question": asdict(follow_up),
        }
    except Exception as exc:
        report["error"] = str(exc)

    destination = (
        Path(output_path).expanduser().resolve()
        if output_path
        else Path(pdf_path).with_name("packaged_integration_results.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report.get("passed") is True else 1


def run() -> int:
    args = parse_arguments()
    if args.integration_test:
        return run_packaged_integration(args.integration_test, args.test_output)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Local Study Tools")
    app.setWindowIcon(make_app_icon())
    app.setStyle("Fusion")
    font_family = load_preferred_font()
    app.setFont(QFont(font_family, 10))

    window = MainWindow(check_status_on_start=not (args.smoke_test or args.screenshot))
    window.show()

    if args.screenshot:
        output = Path(args.screenshot).expanduser().resolve()

        def save_screenshot() -> None:
            window.seed_visual_demo()
            QApplication.processEvents()
            output.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(output), "PNG")
            window.close()
            app.quit()

        QTimer.singleShot(700, save_screenshot)
    elif args.smoke_test:
        QTimer.singleShot(900, window.close)
        QTimer.singleShot(1000, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
