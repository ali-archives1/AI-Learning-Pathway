"""PySide6 interface for the local RAG Study Assistant."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME, CHAT_MODEL, EMBEDDING_MODEL
from rag_engine import AnswerResult, DocumentChunk, ModelStatus, PdfSummary, RAGEngine
from styles import APP_STYLESHEET, COLORS, make_app_icon
from workers import TaskWorker


def label(
    text: str,
    object_name: str = "",
    *,
    word_wrap: bool = False,
) -> QLabel:
    widget = QLabel(text)
    if object_name:
        widget.setObjectName(object_name)
    widget.setWordWrap(word_wrap)
    return widget


class DropZone(QFrame):
    pdf_dropped = Signal(str)
    browse_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(118)
        self.setToolTip("Drop a PDF here or click to browse")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = label("PDF", "Accent")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        icon.setFont(icon_font)
        self.primary = label("Drop a PDF here", "SectionTitle")
        self.primary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        secondary = label("or click to browse", "Muted")
        secondary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(self.primary)
        layout.addWidget(secondary)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].toLocalFile().lower().endswith(".pdf"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            self.pdf_dropped.emit(urls[0].toLocalFile())
            event.acceptProposedAction()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.browse_requested.emit()
        super().mousePressEvent(event)


class QuestionEdit(QPlainTextEdit):
    submit_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submit_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class MessageBubble(QFrame):
    def __init__(self, role: str, text: str, pages: tuple[int, ...] = ()) -> None:
        super().__init__()
        self.role = role
        self.setObjectName("UserBubble" if role == "user" else "AssistantBubble")
        self.setMaximumWidth(740)
        self.setMinimumWidth(260 if role == "user" else 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(8)

        meta_text = "YOU" if role == "user" else "STUDY ASSISTANT"
        self.meta = label(meta_text, "MessageMeta")
        meta_font = QFont("Segoe UI", 8, QFont.Weight.DemiBold)
        self.meta.setFont(meta_font)

        self.body = label(text, word_wrap=True)
        self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.sources = label("", "SourcePill")
        self.sources.setVisible(False)
        self.sources.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.layout.addWidget(self.meta)
        self.layout.addWidget(self.body)
        self.layout.addWidget(self.sources, 0, Qt.AlignmentFlag.AlignLeft)
        self.set_message(text, pages)

    def set_message(self, text: str, pages: tuple[int, ...] = ()) -> None:
        self.body.setText(text)
        if pages:
            page_word = "Page" if len(pages) == 1 else "Pages"
            self.sources.setText(f"{page_word} " + ", ".join(map(str, pages)))
            self.sources.setVisible(True)
        else:
            self.sources.clear()
            self.sources.setVisible(False)


class ChunkCard(QFrame):
    def __init__(self, position: int, chunk: DocumentChunk) -> None:
        super().__init__()
        self.setObjectName("ChunkCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(7)

        header = QHBoxLayout()
        title = label(f"RESULT {position}", "Accent")
        page = label(f"Page {chunk.page}", "SourcePill")
        score = label(f"{max(0.0, chunk.score) * 100:.0f}% match", "Muted")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(score)
        header.addWidget(page)

        excerpt = chunk.text.strip()
        if len(excerpt) > 560:
            excerpt = excerpt[:557].rstrip() + "..."
        content = label(excerpt, word_wrap=True)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addLayout(header)
        layout.addWidget(content)


class MainWindow(QMainWindow):
    def __init__(self, *, check_status_on_start: bool = True) -> None:
        super().__init__()
        self.engine = RAGEngine()
        self.thread_pool = QThreadPool.globalInstance()
        self._workers: set[TaskWorker] = set()
        self._busy = False
        self._pending_bubble: MessageBubble | None = None
        self._current_pdf_directory = str(Path.home() / "Documents")

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(make_app_icon())
        self.resize(1380, 860)
        self.setMinimumSize(1040, 700)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()
        self._show_welcome()

        if check_status_on_start:
            QTimer.singleShot(150, self.check_model_status)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        root_layout.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_inspector())
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([760, 380])
        body.addWidget(splitter, 1)
        root_layout.addLayout(body, 1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(78)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(13)

        icon = QLabel()
        icon.setPixmap(make_app_icon(48).pixmap(48, 48))
        icon.setFixedSize(48, 48)
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.addWidget(label(APP_NAME, "Title"))
        title_box.addWidget(
            label("Private, local answers from your PDF", "Muted")
        )
        layout.addWidget(icon)
        layout.addLayout(title_box)
        layout.addStretch(1)

        self.header_status = label("Checking Ollama...", "Warning")
        self.header_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.header_status)
        return header

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(292)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(14)

        layout.addWidget(label("DOCUMENT", "SectionTitle"))
        self.drop_zone = DropZone()
        self.drop_zone.pdf_dropped.connect(self.load_pdf)
        self.drop_zone.browse_requested.connect(self.choose_pdf)
        layout.addWidget(self.drop_zone)

        self.select_button = QPushButton("Select PDF")
        self.select_button.setObjectName("PrimaryButton")
        self.select_button.clicked.connect(self.choose_pdf)
        layout.addWidget(self.select_button)

        self.document_card = QFrame()
        self.document_card.setObjectName("Card")
        document_layout = QVBoxLayout(self.document_card)
        document_layout.setContentsMargins(12, 11, 12, 11)
        document_layout.setSpacing(4)
        self.document_name = label("No PDF selected", "Muted", word_wrap=True)
        self.document_details = label("Drag a file above to begin.", "Muted", word_wrap=True)
        document_layout.addWidget(self.document_name)
        document_layout.addWidget(self.document_details)
        layout.addWidget(self.document_card)

        actions = QHBoxLayout()
        self.change_button = QPushButton("Change PDF")
        self.change_button.clicked.connect(self.choose_pdf)
        self.change_button.setEnabled(False)
        self.clear_button = QPushButton("Clear chat")
        self.clear_button.clicked.connect(self.clear_chat)
        self.clear_button.setEnabled(False)
        actions.addWidget(self.change_button)
        actions.addWidget(self.clear_button)
        layout.addLayout(actions)

        layout.addSpacing(8)
        layout.addWidget(label("LOCAL AI STATUS", "SectionTitle"))
        status_card = QFrame()
        status_card.setObjectName("Card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(7)
        self.ollama_status = label("Ollama: checking...", "Warning", word_wrap=True)
        self.chat_status = label(f"Chat: {CHAT_MODEL}", "Muted", word_wrap=True)
        self.embedding_status = label(
            f"Embeddings: {EMBEDDING_MODEL}",
            "Muted",
            word_wrap=True,
        )
        self.status_button = QPushButton("Check status")
        self.status_button.clicked.connect(self.check_model_status)
        status_layout.addWidget(self.ollama_status)
        status_layout.addWidget(self.chat_status)
        status_layout.addWidget(self.embedding_status)
        status_layout.addWidget(self.status_button)
        layout.addWidget(status_card)

        layout.addStretch(1)
        privacy = label(
            "Your PDF and questions stay on this computer and are sent only "
            "to your local Ollama service.",
            "Muted",
            word_wrap=True,
        )
        layout.addWidget(privacy)
        return sidebar

    def _build_chat_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(label("Ask your document", "Title"))
        self.chat_subtitle = label("Select a PDF to start studying.", "Muted")
        title_box.addWidget(self.chat_subtitle)
        top.addLayout(title_box)
        top.addStretch(1)
        layout.addLayout(top)

        self.error_banner = QFrame()
        self.error_banner.setObjectName("ErrorBanner")
        error_layout = QHBoxLayout(self.error_banner)
        error_layout.setContentsMargins(12, 8, 12, 8)
        self.error_text = label("", word_wrap=True)
        dismiss = QPushButton("Dismiss")
        dismiss.setFixedWidth(82)
        dismiss.clicked.connect(self.error_banner.hide)
        error_layout.addWidget(self.error_text, 1)
        error_layout.addWidget(dismiss)
        self.error_banner.hide()
        layout.addWidget(self.error_banner)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(4, 6, 4, 6)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_scroll.setWidget(self.messages_widget)
        layout.addWidget(self.chat_scroll, 1)

        self.activity_label = label("", "Accent")
        self.activity_label.hide()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.activity_label)
        layout.addWidget(self.progress)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.question_input = QuestionEdit()
        self.question_input.setPlaceholderText(
            "Ask a question about the PDF...  (Shift+Enter for a new line)"
        )
        self.question_input.setFixedHeight(76)
        self.question_input.setEnabled(False)
        self.question_input.submit_requested.connect(self.submit_question)
        self.send_button = QPushButton("Ask")
        self.send_button.setObjectName("PrimaryButton")
        self.send_button.setFixedSize(94, 76)
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.submit_question)
        input_row.addWidget(self.question_input, 1)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)
        return panel

    def _build_inspector(self) -> QFrame:
        inspector = QFrame()
        inspector.setObjectName("Inspector")
        inspector.setMinimumWidth(315)
        layout = QVBoxLayout(inspector)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(8)
        layout.addWidget(label("Retrieved sections", "Title"))
        layout.addWidget(
            label(
                "These are the exact PDF excerpts considered for the latest answer.",
                "Muted",
                word_wrap=True,
            )
        )
        self.chunk_scroll = QScrollArea()
        self.chunk_scroll.setWidgetResizable(True)
        self.chunk_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.chunk_widget = QWidget()
        self.chunk_layout = QVBoxLayout(self.chunk_widget)
        self.chunk_layout.setContentsMargins(0, 10, 0, 0)
        self.chunk_layout.setSpacing(10)
        self.chunk_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chunk_scroll.setWidget(self.chunk_widget)
        layout.addWidget(self.chunk_scroll, 1)
        self._show_empty_chunks()
        return inspector

    def _show_welcome(self) -> None:
        self._clear_layout(self.messages_layout)
        self._append_message(
            "assistant",
            "Choose a PDF to build a private study index. Then ask direct questions "
            "or follow up naturally—the answers will stay grounded in that document.",
        )

    def _show_empty_chunks(self) -> None:
        self._clear_layout(self.chunk_layout)
        placeholder = label(
            "Retrieved sections will appear here after your first question.",
            "Muted",
            word_wrap=True,
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(160)
        self.chunk_layout.addWidget(placeholder)

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _append_message(
        self,
        role: str,
        text: str,
        pages: tuple[int, ...] = (),
    ) -> MessageBubble:
        bubble = MessageBubble(role, text, pages)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        if role == "user":
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)
        self.messages_layout.addWidget(row)
        QTimer.singleShot(0, self._scroll_chat_to_bottom)
        return bubble

    def _scroll_chat_to_bottom(self) -> None:
        bar = self.chat_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def choose_pdf(self) -> None:
        if self._busy:
            return
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select a PDF",
            self._current_pdf_directory,
            "PDF documents (*.pdf)",
        )
        if path:
            self.load_pdf(path)

    def load_pdf(self, path: str) -> None:
        if self._busy:
            return
        if not path.lower().endswith(".pdf"):
            self._show_error("Please select a PDF file.")
            return
        self._current_pdf_directory = str(Path(path).parent)
        self._set_busy(True, "Preparing PDF...", 0)
        self.document_name.setText(Path(path).name)
        self.document_name.setObjectName("Accent")
        self.document_name.style().unpolish(self.document_name)
        self.document_name.style().polish(self.document_name)
        self.document_details.setText("Reading and creating local embeddings...")

        worker = TaskWorker(self.engine.process_pdf, path, report_progress=True)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.result.connect(self._pdf_ready)
        worker.signals.error.connect(self._task_error)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self._start_worker(worker)

    def _pdf_ready(self, summary: PdfSummary) -> None:
        self._show_welcome()
        self._show_empty_chunks()
        self.document_name.setText(summary.file_name)
        self.document_details.setText(
            f"{summary.page_count} pages · {summary.chunk_count} study sections"
        )
        self.chat_subtitle.setText(
            f"{summary.file_name} · {summary.page_count} pages"
        )
        self.drop_zone.primary.setText("PDF ready")
        self.change_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.question_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self._append_message(
            "assistant",
            f"Ready. I indexed {summary.text_page_count} text pages into "
            f"{summary.chunk_count} sections. What would you like to study?",
        )
        self.question_input.setFocus()

    def submit_question(self) -> None:
        if self._busy or self.engine.summary is None:
            return
        question = self.question_input.toPlainText().strip()
        if not question:
            return
        self.question_input.clear()
        self._append_message("user", question)
        self._pending_bubble = self._append_message(
            "assistant",
            "Searching the PDF and preparing a grounded answer...",
        )
        self._set_busy(True, "Searching the PDF...", 0)
        worker = TaskWorker(self.engine.ask, question, report_progress=True)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.result.connect(self._answer_ready)
        worker.signals.error.connect(self._answer_error)
        worker.signals.finished.connect(lambda: self._set_busy(False))
        self._start_worker(worker)

    def _answer_ready(self, result: AnswerResult) -> None:
        if self._pending_bubble:
            self._pending_bubble.set_message(result.answer, result.source_pages)
            if not result.found:
                self._pending_bubble.meta.setText("STUDY ASSISTANT · NOT FOUND")
        self._pending_bubble = None
        self._update_chunks(result.chunks)
        self.question_input.setFocus()
        QTimer.singleShot(0, self._scroll_chat_to_bottom)

    def _answer_error(self, message: str) -> None:
        if self._pending_bubble:
            self._pending_bubble.set_message(
                "I couldn't complete that answer. Review the message above and try again."
            )
            self._pending_bubble.meta.setText("STUDY ASSISTANT · ERROR")
        self._pending_bubble = None
        self._show_error(message)

    def _update_chunks(self, chunks: tuple[DocumentChunk, ...]) -> None:
        self._clear_layout(self.chunk_layout)
        for position, chunk in enumerate(chunks, start=1):
            self.chunk_layout.addWidget(ChunkCard(position, chunk))
        if not chunks:
            self._show_empty_chunks()

    def clear_chat(self) -> None:
        if self._busy:
            return
        self.engine.clear_chat()
        self._show_welcome()
        self._show_empty_chunks()
        if self.engine.summary:
            self._append_message(
                "assistant",
                "Conversation cleared. The current PDF is still ready for questions.",
            )
            self.question_input.setFocus()

    def check_model_status(self) -> None:
        if self.status_button.isEnabled():
            self.status_button.setEnabled(False)
            self.ollama_status.setText("Ollama: checking...")
            self.ollama_status.setObjectName("Warning")
            worker = TaskWorker(self.engine.check_status)
            worker.signals.result.connect(self._status_ready)
            worker.signals.error.connect(self._status_error)
            worker.signals.finished.connect(lambda: self.status_button.setEnabled(True))
            self._start_worker(worker)

    def _status_ready(self, status: ModelStatus) -> None:
        if not status.connected:
            self._status_error(status.error)
            return
        self.ollama_status.setText("Ollama: connected")
        self.ollama_status.setObjectName("Success")
        self.chat_status.setText(
            f"Chat: {CHAT_MODEL} · "
            + ("ready" if status.chat_available else "missing")
        )
        self.chat_status.setObjectName(
            "Success" if status.chat_available else "Danger"
        )
        self.embedding_status.setText(
            f"Embeddings: {EMBEDDING_MODEL} · "
            + ("ready" if status.embedding_available else "missing")
        )
        self.embedding_status.setObjectName(
            "Success" if status.embedding_available else "Danger"
        )
        if status.chat_available and status.embedding_available:
            self.header_status.setText("Local AI ready")
            self.header_status.setObjectName("Success")
        else:
            self.header_status.setText("Required model missing")
            self.header_status.setObjectName("Danger")
        self._repolish_status_labels()

    def _status_error(self, message: str) -> None:
        self.ollama_status.setText("Ollama: not connected")
        self.ollama_status.setObjectName("Danger")
        self.chat_status.setText(f"Chat: {CHAT_MODEL} · unavailable")
        self.chat_status.setObjectName("Muted")
        self.embedding_status.setText(
            f"Embeddings: {EMBEDDING_MODEL} · unavailable"
        )
        self.embedding_status.setObjectName("Muted")
        self.header_status.setText("Ollama offline")
        self.header_status.setObjectName("Danger")
        self._repolish_status_labels()
        if message:
            self.ollama_status.setToolTip(message)

    def _repolish_status_labels(self) -> None:
        for widget in (
            self.ollama_status,
            self.chat_status,
            self.embedding_status,
            self.header_status,
        ):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _start_worker(self, worker: TaskWorker) -> None:
        self._workers.add(worker)
        worker.signals.finished.connect(
            lambda current=worker: self._workers.discard(current)
        )
        self.thread_pool.start(worker)

    def _update_progress(self, value: int, message: str) -> None:
        self.progress.setRange(0, 100)
        self.progress.setValue(max(0, min(100, value)))
        self.activity_label.setText(message)

    def _set_busy(
        self,
        busy: bool,
        message: str = "",
        progress: int = 0,
    ) -> None:
        self._busy = busy
        self.select_button.setEnabled(not busy)
        self.drop_zone.setEnabled(not busy)
        self.change_button.setEnabled(not busy and self.engine.summary is not None)
        self.clear_button.setEnabled(not busy and self.engine.summary is not None)
        self.question_input.setEnabled(not busy and self.engine.summary is not None)
        self.send_button.setEnabled(not busy and self.engine.summary is not None)
        self.activity_label.setVisible(busy)
        self.progress.setVisible(busy)
        if busy:
            self.activity_label.setText(message)
            self.progress.setRange(0, 100)
            self.progress.setValue(progress)

    def _task_error(self, message: str) -> None:
        self.document_details.setText("PDF processing failed. Choose another file.")
        self._show_error(message)

    def _show_error(self, message: str) -> None:
        self.error_text.setText(message)
        self.error_banner.show()

    def seed_visual_demo(self) -> None:
        """Populate representative content for off-screen visual verification."""

        self.header_status.setText("Local AI ready")
        self.header_status.setObjectName("Success")
        self.document_name.setText("biology_study_notes.pdf")
        self.document_name.setObjectName("Accent")
        self.document_details.setText("4 pages · 7 study sections")
        self.chat_subtitle.setText("biology_study_notes.pdf · 4 pages")
        self.ollama_status.setText("Ollama: connected")
        self.ollama_status.setObjectName("Success")
        self.chat_status.setText(f"Chat: {CHAT_MODEL} · ready")
        self.chat_status.setObjectName("Success")
        self.embedding_status.setText(f"Embeddings: {EMBEDDING_MODEL} · ready")
        self.embedding_status.setObjectName("Success")
        self._repolish_status_labels()
        self._clear_layout(self.messages_layout)
        self._append_message(
            "assistant",
            "Ready. I indexed 4 text pages into 7 sections. What would you like to study?",
        )
        self._append_message(
            "user",
            "Which organelle generates most of a cell's ATP?",
        )
        self._append_message(
            "assistant",
            "Mitochondria generate most of the cell's ATP through cellular respiration.",
            (2,),
        )
        demo_chunks = (
            DocumentChunk(
                index=2,
                page=2,
                text=(
                    "Mitochondria generate most of the cell's ATP through cellular "
                    "respiration. Folds of the inner membrane, called cristae, increase "
                    "the surface area available for energy-producing reactions."
                ),
                score=0.87,
            ),
            DocumentChunk(
                index=3,
                page=3,
                text=(
                    "Chloroplasts capture light energy during photosynthesis. "
                    "Chlorophyll is embedded in thylakoid membranes."
                ),
                score=0.43,
            ),
        )
        self._update_chunks(demo_chunks)
