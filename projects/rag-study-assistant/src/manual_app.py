"""Launch the engineering-manual extension; the original study app is preserved."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from engineering_window import EngineeringWindow
from styles import load_preferred_font, make_app_icon


def main():
    parser = argparse.ArgumentParser(description="Engineering Manual Q&A")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--pdf", help="Optional local PDF to load")
    parser.add_argument("--verify-backend", type=Path, help="Save an actual local-model release check to this JSON path")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("Engineering Manual Q&A")
    app.setOrganizationName("Ali Engineering Lab")
    app.setWindowIcon(make_app_icon())
    app.setStyle("Fusion")
    app.setFont(QFont(load_preferred_font(), 10))
    if args.verify_backend:
        from manual_engine import ManualEngine
        from manual_project import sample_path
        from PySide6.QtPdf import QPdfDocument
        checks, result = {}, {}
        try:
            engine = ManualEngine()
            status = engine.check_status()
            checks["models_ready"] = status.connected and status.chat_available and status.embedding_available
            if not checks["models_ready"]:
                raise RuntimeError("Required local models are unavailable.")
            summary = engine.process_pdf(sample_path())
            checks["public_manual_indexed"] = summary.page_count == 14
            document = QPdfDocument()
            checks["qt_pdf_viewer_resource"] = document.load(str(sample_path())) == QPdfDocument.Error.None_ and document.pageCount() == 14
            answer = engine.ask("What type of USB cable does the manual say is needed to connect the UNO R3 to a computer?")
            missing = engine.ask("How much does the UNO R3 board weigh in grams?")
            checks["supported_answer"] = answer.found and "usb-b" in answer.answer.lower() and 8 in answer.source_pages
            checks["missing_answer_refused"] = not missing.found and not missing.source_pages
            result.update({"checks": checks, "answer": asdict(answer), "missing": asdict(missing)})
        except Exception as exc:
            result.update({"checks": checks, "error": str(exc)})
        result["passed"] = len(checks) == 5 and all(checks.values())
        args.verify_backend.parent.mkdir(parents=True, exist_ok=True)
        args.verify_backend.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
        return 0 if result["passed"] else 1
    window = EngineeringWindow(check_status_on_start=not args.smoke_test)
    window.show()
    if args.pdf:
        QTimer.singleShot(400, lambda: window.load_manual(args.pdf))
    if args.smoke_test:
        QTimer.singleShot(1200, window.close)
        QTimer.singleShot(1500, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
