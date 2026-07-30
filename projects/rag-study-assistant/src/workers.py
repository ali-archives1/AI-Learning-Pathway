"""Reusable Qt thread-pool worker for blocking PDF and Ollama operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(int, str)
    finished = Signal()


class TaskWorker(QRunnable):
    """Run a callable in QThreadPool and deliver results back to the UI thread."""

    def __init__(
        self,
        function: Callable[..., Any],
        *args: Any,
        report_progress: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.report_progress = report_progress
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            kwargs = dict(self.kwargs)
            if self.report_progress:
                kwargs["progress_callback"] = self.signals.progress.emit
            result = self.function(*self.args, **kwargs)
        except Exception as exc:
            message = str(exc).strip() or "An unexpected error occurred."
            self.signals.error.emit(message)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
