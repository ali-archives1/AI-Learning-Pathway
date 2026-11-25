"""Native engineering-manual workspace: inspect, answer, verify."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QThreadPool, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QSplitter, QStackedWidget, QTableWidget, QLayout,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from config import CHAT_MODEL, EMBEDDING_MODEL
from manual_engine import EvidencePacket, ManualAnswer, ManualEngine
from manual_project import project_root, sample_path, source_manifest, writable_root
from manual_styles import STYLES
from styles import make_app_icon
from workers import TaskWorker


def text(value, name="", wrap=False):
    widget = QLabel(value)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if name:
        widget.setObjectName(name)
    return widget


def button(value, callback=None, name=""):
    widget = QPushButton(value)
    if name:
        widget.setObjectName(name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if callback:
        widget.clicked.connect(callback)
    return widget


def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


def surface(name="Surface", margin=18):
    frame = QFrame()
    frame.setObjectName(name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(margin, margin, margin, margin)
    layout.setSpacing(12)
    return frame, layout


def scroll_container():
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    body = QWidget()
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 0, 6, 0)
    layout.setSpacing(12)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(body)
    return scroll, layout


class EvidenceCard(QFrame):
    def __init__(self, rank, chunk, open_page):
        super().__init__()
        self.setObjectName("EvidenceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)
        row = QHBoxLayout()
        row.addWidget(text(f"{rank:02d}  SOURCE PASSAGE", "Overline"))
        row.addStretch()
        page = button(f"Page {chunk.page} ↗", lambda: open_page(chunk.page), "Citation")
        page.setAccessibleName(f"Open source page {chunk.page}")
        row.addWidget(page)
        layout.addLayout(row)
        layout.addWidget(text(chunk.section, "Small", True))
        self.full_text = chunk.text.strip()
        self.body = text(self.full_text[:340] + ("…" if len(self.full_text)>340 else ""), "Body", True)
        self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.body)
        footer = QHBoxLayout()
        similarity = text(f"Similarity {chunk.score:.3f}", "Small")
        similarity.setToolTip("Cosine similarity used for retrieval, not answer confidence.")
        footer.addWidget(similarity)
        footer.addStretch()
        if len(self.full_text)>340:
            expand = button("Show full passage", name="Ghost")
            expand.setCheckable(True)
            def toggle(checked):
                self.body.setText(self.full_text if checked else self.full_text[:340]+"…")
                expand.setText("Show less" if checked else "Show full passage")
            expand.toggled.connect(toggle)
            footer.addWidget(expand)
        layout.addLayout(footer)
        identity = text(chunk.chunk_id, "Small")
        identity.setToolTip(f"Stable chunk ID\nSource: {chunk.source_id}")
        layout.addWidget(identity)


class EngineeringWindow(QMainWindow):
    def __init__(self, *, check_status_on_start=True):
        super().__init__()
        self.engine = ManualEngine()
        self.packet = None
        self.last_answer = None
        self._busy = False
        self._workers = set()
        self._last_error = ""
        self._history = []
        self.generate_button = None
        self.thread_pool = QThreadPool.globalInstance()
        self.setWindowTitle("Engineering Manual Q&A")
        self.setWindowIcon(make_app_icon())
        self.resize(1440, 940)
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(STYLES)
        self._build()
        self._welcome()
        self._read_results()
        if check_status_on_start:
            QTimer.singleShot(200, self.check_status)

    def _build(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._rail())
        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main.addWidget(self._topbar())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._workspace())
        self.pages.addWidget(self._evaluation_page())
        main.addWidget(self.pages, 1)
        outer.addLayout(main, 1)

    def _rail(self):
        rail = QFrame()
        rail.setObjectName("Rail")
        layout = QVBoxLayout(rail)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.setContentsMargins(18, 26, 18, 22)
        layout.setSpacing(12)
        brand = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(make_app_icon().pixmap(32, 32))
        brand.addWidget(icon)
        brand.addWidget(text("MANUAL", "Brand"))
        brand.addStretch()
        layout.addLayout(brand)
        layout.addWidget(text("ENGINEERING WORKSPACE", "Overline"))
        layout.addSpacing(23)
        self.workspace_nav = button("◫   Manual Q&A", lambda: self.navigate(0), "Nav")
        self.evaluation_nav = button("▤   Evaluation", lambda: self.navigate(1), "Nav")
        for nav in (self.workspace_nav, self.evaluation_nav):
            nav.setCheckable(True)
            layout.addWidget(nav)
        self.workspace_nav.setChecked(True)
        layout.addSpacing(22)
        layout.addWidget(text("YOUR MANUAL", "Overline"))
        card, card_layout = surface(margin=13)
        card.setMinimumHeight(225)
        card_layout.addWidget(text("PDF", "Teal"))
        self.document_title = text("No manual loaded", "Subheading", True)
        self.document_meta = text("Start with the public example or choose your own PDF.", "Muted", True)
        card_layout.addWidget(self.document_title)
        card_layout.addWidget(self.document_meta)
        self.source_button = button("Source details", self.source_details, "Ghost")
        self.source_button.setEnabled(False)
        card_layout.addWidget(self.source_button)
        layout.addWidget(card)
        self.load_sample_button = button("Open Arduino example", lambda: self.load_manual(str(sample_path())), "Primary")
        self.choose_button = button("Choose another PDF", self.choose_manual, "Ghost")
        layout.addWidget(self.load_sample_button)
        layout.addWidget(self.choose_button)
        layout.addSpacing(12)
        layout.addWidget(text("CHUNKING", "Overline"))
        self.chunking = QComboBox()
        self.chunking.addItem("900 chars · 150 overlap", 900)
        self.chunking.addItem("450 chars · 75 overlap", 450)
        self.chunking.setAccessibleName("Chunking strategy")
        self.chunking.currentIndexChanged.connect(self.change_chunking)
        layout.addWidget(self.chunking)
        layout.addWidget(text("Changing this setting rebuilds the index.", "Small", True))
        layout.addStretch()
        layout.addWidget(text("LOCAL PROCESSING", "Overline"))
        self.model_status = text("Checking local models…", "Muted", True)
        layout.addWidget(self.model_status)
        self.status_button = button("Check models", self.check_status, "Ghost")
        layout.addWidget(self.status_button)
        layout.addSpacing(12)
        layout.addWidget(text("Manuals and questions are processed by Ollama on this computer.", "Small", True))
        rail_scroll = QScrollArea()
        rail_scroll.setWidgetResizable(True)
        rail_scroll.setFixedWidth(214)
        rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rail_scroll.setWidget(rail)
        return rail_scroll

    def _topbar(self):
        header = QFrame()
        header.setObjectName("Topbar")
        header.setFixedHeight(69)
        row = QHBoxLayout(header)
        row.setContentsMargins(28, 12, 26, 12)
        self.breadcrumb = text("WORKSPACE  /  MANUAL Q&A", "Overline")
        row.addWidget(self.breadcrumb)
        row.addStretch()
        row.addWidget(text("ALI'S ENGINEERING LAB", "Small"))
        row.addSpacing(16)
        self.top_status = text("Local workspace", "Badge")
        row.addWidget(self.top_status)
        return header

    def _workspace(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        center = QWidget()
        column = QVBoxLayout(center)
        column.setContentsMargins(28, 26, 25, 22)
        column.setSpacing(14)
        column.addWidget(text("Ask the manual", "Heading"))
        column.addWidget(text("Find the passage. Check the source. Get an answer.", "Muted", True))
        steps = QHBoxLayout()
        for caption in ("01  Index manual", "02  Inspect evidence", "03  Answer"):
            steps.addWidget(text(caption, "Step"))
        column.addLayout(steps)
        self.source_note = text("", "Small", True)
        self.source_note.hide()
        column.addWidget(self.source_note)
        self.error_card, error_layout = surface("ErrorCard", 12)
        self.error_label = text("", "Body", True)
        error_layout.addWidget(self.error_label)
        dismiss = button("Dismiss", self.error_card.hide, "Ghost")
        error_layout.addWidget(dismiss, 0, Qt.AlignmentFlag.AlignRight)
        self.error_card.hide()
        column.addWidget(self.error_card)
        self.answer_scroll, self.answer_layout = scroll_container()
        column.addWidget(self.answer_scroll, 1)
        self.activity = text("", "Teal", True)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.activity.hide()
        self.progress.hide()
        column.addWidget(self.activity)
        column.addWidget(self.progress)
        question_label = QHBoxLayout()
        question_label.addWidget(text("YOUR QUESTION", "Overline"))
        question_label.addStretch()
        self.clear_button = button("New question", self.new_question, "Ghost")
        question_label.addWidget(self.clear_button)
        column.addLayout(question_label)
        self.question = QPlainTextEdit()
        self.question.setPlaceholderText("For example: How many digital I/O pins does the UNO R3 have?")
        self.question.setFixedHeight(94)
        self.question.setAccessibleName("Question about the engineering manual")
        self.question.textChanged.connect(self._question_changed)
        self.question.setEnabled(False)
        column.addWidget(self.question)
        controls = QHBoxLayout()
        controls.addWidget(text("Answers quote the manual; no invented specifications.", "Small", True), 1)
        self.retrieve_button = button("Find evidence  →", self.retrieve, "Primary")
        self.retrieve_button.setEnabled(False)
        controls.addWidget(self.retrieve_button)
        column.addLayout(controls)
        self.splitter.addWidget(center)
        self.splitter.addWidget(self._inspector())
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([680, 480])
        return self.splitter

    def _inspector(self):
        pane = QFrame()
        pane.setObjectName("EvidencePane")
        pane.setMinimumWidth(340)
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(21, 27, 20, 22)
        layout.setSpacing(12)
        heading = QHBoxLayout()
        heading.addWidget(text("Source inspector", "Subheading"))
        heading.addStretch()
        self.evidence_count = text("0 passages", "Small")
        heading.addWidget(self.evidence_count)
        layout.addLayout(heading)
        tabs = QHBoxLayout()
        self.evidence_tab = button("Retrieved evidence", lambda: self.show_inspector(0), "Ghost")
        self.pdf_tab = button("Manual pages", lambda: self.show_inspector(1), "Ghost")
        tabs.addWidget(self.evidence_tab)
        tabs.addWidget(self.pdf_tab)
        layout.addLayout(tabs)
        self.inspector_stack = QStackedWidget()
        evidence_scroll, self.evidence_layout = scroll_container()
        self.inspector_stack.addWidget(evidence_scroll)
        pdf_panel = QWidget()
        pdf_layout = QVBoxLayout(pdf_panel)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(pdf_panel)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        page_controls = QHBoxLayout()
        previous = button("←", lambda: self.open_page(self.page_number.value()-1), "Ghost")
        next_page = button("→", lambda: self.open_page(self.page_number.value()+1), "Ghost")
        self.page_number = QSpinBox()
        self.page_number.setRange(1, 1)
        self.page_number.setAccessibleName("Source PDF page number")
        self.page_number.valueChanged.connect(self.open_page)
        page_controls.addWidget(previous)
        page_controls.addWidget(text("Page", "Small"))
        page_controls.addWidget(self.page_number)
        self.page_total = text("/ 0", "Small")
        page_controls.addWidget(self.page_total)
        page_controls.addStretch()
        page_controls.addWidget(next_page)
        pdf_layout.addLayout(page_controls)
        pdf_layout.addWidget(self.pdf_view, 1)
        self.pdf_view.pageNavigator().currentPageChanged.connect(self._viewer_page_changed)
        self.inspector_stack.addWidget(pdf_panel)
        layout.addWidget(self.inspector_stack, 1)
        layout.addWidget(text("Similarity ranks passages. It is not confidence that an answer is correct.", "Small", True))
        return pane

    def _evaluation_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 26)
        layout.setSpacing(18)
        layout.addWidget(text("Measure the difference", "Heading"))
        layout.addWidget(text("Public Arduino UNO R3 benchmark · 25 fixed questions · two chunking strategies", "Muted", True))
        metrics = QHBoxLayout()
        for big, small in (("20", "Answerable questions"), ("5", "Unanswerable questions"), ("2", "Chunking settings")):
            card, box = surface()
            box.addWidget(text(big, "Heading"))
            box.addWidget(text(small, "Muted"))
            metrics.addWidget(card)
        layout.addLayout(metrics)
        self.eval_table = QTableWidget(0, 6)
        self.eval_table.setHorizontalHeaderLabels(["Chars / overlap", "Hit@1", "Hit@5", "Quote support", "Answer check", "Refusal"])
        self.eval_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.eval_table.verticalHeader().hide()
        self.eval_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.eval_table.setMinimumHeight(150)
        self.eval_table.setMaximumHeight(180)
        layout.addWidget(self.eval_table)
        self.eval_note = text("No completed evaluation loaded. Run the comparison to measure both settings.", "Muted", True)
        layout.addWidget(self.eval_note)
        definitions, definitions_box = surface()
        definitions_box.addWidget(text("What these numbers mean", "Subheading"))
        definitions_box.addWidget(text("Hit@5: expected evidence appears among five retrieved passages.\nQuote support: factual output matches retrieved text; it does not prove relevance.\nAnswer check: expected terms and an expected page match the reference set.\nRefusal: missing answers return 'not found' without invented facts.", "Body", True))
        layout.addWidget(definitions)
        self.eval_details = QPlainTextEdit()
        self.eval_details.setReadOnly(True)
        self.eval_details.setPlaceholderText("Failures and run details will appear here.")
        layout.addWidget(self.eval_details, 1)
        self.eval_activity = text("", "Teal", True)
        self.eval_progress = QProgressBar()
        self.eval_progress.setTextVisible(False)
        self.eval_activity.hide()
        self.eval_progress.hide()
        layout.addWidget(self.eval_activity)
        layout.addWidget(self.eval_progress)
        row = QHBoxLayout()
        row.addWidget(text("Local-model runs may take several minutes. All raw results are retained.", "Small", True), 1)
        self.run_eval_button = button("Run full comparison", self.run_evaluation, "Primary")
        row.addWidget(self.run_eval_button)
        layout.addLayout(row)
        return page

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        self.workspace_nav.setChecked(index == 0)
        self.evaluation_nav.setChecked(index == 1)
        self.breadcrumb.setText("WORKSPACE  /  " + ("MANUAL Q&A" if index == 0 else "EVALUATION"))

    def _welcome(self):
        self.generate_button = None
        clear(self.answer_layout)
        hero, layout = surface(margin=24)
        layout.addWidget(text("ENGINEERING MANUAL Q&A", "Overline"))
        layout.addWidget(text("Understand your\nengineering manual.", "Hero", True))
        layout.addWidget(text("Ask a focused question and inspect the source passages before generating an answer. Every returned fact is quoted from the document.", "Body", True))
        self.answer_layout.addWidget(hero)
        self.answer_layout.addWidget(text("TRY A QUESTION", "Overline"))
        for caption, example in (("Digital input/output pin count", "How many digital input/output pins does the UNO R3 have?"),
                                 ("USB cable and computer connection", "What USB cable is needed to connect it to a computer?"),
                                 ("Try an unspecified value: PMax", "What is the numeric maximum power consumption PMax?")):
            choice = button(caption, name="Example")
            choice.clicked.connect(lambda _checked=False, value=example: self.question.setPlainText(value))
            choice.setToolTip(example)
            self.answer_layout.addWidget(choice)
        self.answer_layout.addWidget(text("The example manual is public Arduino documentation. Your own PDFs are processed locally.", "Small", True))
        clear(self.evidence_layout)
        self.evidence_layout.addSpacing(34)
        self.evidence_layout.addWidget(text("Evidence comes first", "Subheading"))
        self.evidence_layout.addWidget(text("Load a manual and choose Find evidence. Retrieved passages, source pages, and similarity scores will appear here.", "Muted", True))
        self.evidence_count.setText("0 passages")

    def choose_manual(self):
        if self._busy:
            return
        name, _ = QFileDialog.getOpenFileName(self, "Choose a public or approved manual", "", "PDF manuals (*.pdf)")
        if name:
            self.load_manual(name)

    def load_manual(self, path):
        if self._busy:
            return
        if not Path(path).is_file():
            self.show_error("The example PDF is missing. Run scripts/download_manual.py or choose another PDF.")
            return
        self.packet, self.last_answer = None, None
        self._task(self.engine.process_pdf, (path,), self._manual_loaded, "Indexing manual…")

    def _manual_loaded(self, summary):
        self._history.clear()
        self.document_title.setText(summary.title)
        self.document_meta.setText(f"{summary.publisher}\n\n{summary.page_count} pages · {summary.chunk_count} chunks\n{summary.chunk_size} characters per chunk")
        error = self.pdf_document.load(summary.path)
        if error != QPdfDocument.Error.None_:
            self.show_error("Text indexing succeeded, but the PDF preview could not be loaded.")
        self.page_number.setRange(1, summary.page_count)
        self.page_total.setText(f"/ {summary.page_count}")
        self.top_status.setText("Manual indexed")
        known = source_manifest()
        self.source_note.setVisible(summary.sha256 == known["sha256"])
        self.source_note.setText("Source note: this manual has conflicting clock-speed statements and an unspecified power value. See Source details.")
        self.source_button.setEnabled(True)
        self._welcome()
        self.question.setFocus()

    def change_chunking(self):
        if self._busy:
            return
        path = self.engine.summary.path if self.engine.summary else None
        size = self.chunking.currentData()
        replacement = ManualEngine(size, size//6)
        self.packet, self.last_answer = None, None
        if path:
            self._task(replacement.process_pdf, (path,),
                       lambda summary: self._install_engine(replacement, summary), "Rebuilding the manual index…")
        else:
            self.engine = replacement

    def _install_engine(self, engine, summary):
        self.engine = engine
        self._manual_loaded(summary)

    def _question_changed(self):
        self.packet = None
        if self.generate_button is not None:
            self.generate_button.setEnabled(False)
        self._controls()

    def retrieve(self):
        if self._busy:
            return
        self.packet, self.last_answer = None, None
        self._task(self.engine.retrieve, (self.question.toPlainText(),), self._evidence_ready, "Retrieving evidence…")

    def _evidence_ready(self, packet):
        self.packet = packet
        self._populate_evidence(packet.chunks)
        self.show_inspector(0)
        clear(self.answer_layout)
        self.answer_layout.addWidget(text(packet.question, "Subheading", True))
        card, box = surface("AnswerCard", 23)
        box.addWidget(text("EVIDENCE READY", "Overline"))
        box.addWidget(text("Review the passages first.", "Subheading", True))
        box.addWidget(text(f"Found {len(packet.chunks)} candidate passages in {packet.retrieval_seconds:.1f}s. Related text may still be insufficient to answer your question.", "Body", True))
        self.generate_button = button("Answer from these sources  →", self.generate, "Primary")
        box.addWidget(self.generate_button)
        self.answer_layout.addWidget(card)
        self.answer_layout.addWidget(text("The next step selects exact quotations. Missing or unverifiable evidence returns 'not found'.", "Small", True))

    def _populate_evidence(self, chunks):
        clear(self.evidence_layout)
        for rank, chunk in enumerate(chunks, 1):
            self.evidence_layout.addWidget(EvidenceCard(rank, chunk, self.open_page))
        self.evidence_count.setText(f"{len(chunks)} passages")

    def generate(self):
        if self._busy or not self.packet:
            return
        self._task(self.engine.answer_from_evidence, (self.packet,), self._answer_ready, "Checking the answer against source text…")

    def _answer_ready(self, answer):
        self.last_answer = answer
        self._history.append(answer)
        self.generate_button = None
        clear(self.answer_layout)
        self.answer_layout.addWidget(text(answer.question, "Subheading", True))
        card, box = surface("AnswerCard" if answer.found else "Surface", 22)
        header = QHBoxLayout()
        header.addWidget(text("SOURCE-SUPPORTED ANSWER" if answer.found else "NOT FOUND IN THIS MANUAL", "Overline"))
        header.addStretch()
        header.addWidget(text("Quoted evidence" if answer.found else "No guessing", "Badge"))
        box.addLayout(header)
        if answer.found:
            for citation in answer.citations:
                quote_card, quote_box = surface("QuoteCard", 15)
                quote = text(citation.quote, "Body", True)
                quote.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                quote_box.addWidget(quote)
                source_row = QHBoxLayout()
                source_row.addWidget(text(citation.section, "Small", True), 1)
                source_row.addWidget(button(f"Page {citation.page} ↗", lambda _=False, p=citation.page: self.open_page(p), "Citation"))
                quote_box.addLayout(source_row)
                box.addWidget(quote_card)
            box.addWidget(text("Quoted from retrieved text. Check the page for surrounding context and any source contradictions.", "Small", True))
        else:
            box.addWidget(text("The retrieved passages did not provide a verifiable answer.", "Subheading", True))
            box.addWidget(text("Try a more specific question or a manual that contains this information. No outside specifications have been added.", "Body", True))
            box.addWidget(text(f"Verification result: {answer.reason.replace('_',' ')}", "Small", True))
        self.answer_layout.addWidget(card)
        footer = QHBoxLayout()
        footer.addWidget(text(f"{answer.generation_seconds:.1f}s · local processing", "Small"))
        footer.addStretch()
        copy = button("Copy answer", lambda: QApplication.clipboard().setText(answer.answer + ("\nSource pages: " + ", ".join(map(str,answer.source_pages)) if answer.source_pages else "")), "Ghost")
        footer.addWidget(copy)
        self.answer_layout.addLayout(footer)
        if len(self._history)>1:
            self.answer_layout.addWidget(text("RECENT QUESTIONS", "Overline"))
            for previous in self._history[-4:-1]:
                older = button(previous.question, name="Example")
                older.clicked.connect(lambda _=False, value=previous: self._show_previous(value))
                self.answer_layout.addWidget(older)

    def _show_previous(self, answer):
        # Display the saved result without modifying the underlying history.
        history = self._history[:]
        self.question.setPlainText(answer.question)
        self.packet = None
        self._populate_evidence(answer.chunks)
        self._answer_ready(answer)
        self._history = history

    def new_question(self):
        if self._busy:
            return
        self.packet, self.last_answer = None, None
        self.question.clear()
        self._welcome()
        self.question.setFocus()

    def show_inspector(self, index):
        self.inspector_stack.setCurrentIndex(index)
        self.evidence_tab.setObjectName("Primary" if index == 0 else "Ghost")
        self.pdf_tab.setObjectName("Primary" if index == 1 else "Ghost")
        for widget in (self.evidence_tab, self.pdf_tab):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def open_page(self, page):
        count = self.pdf_document.pageCount()
        if not count:
            return
        page = max(1, min(count, int(page)))
        self.page_number.blockSignals(True)
        self.page_number.setValue(page)
        self.page_number.blockSignals(False)
        self.pdf_view.pageNavigator().jump(page-1, QPointF(0, 0))
        self.show_inspector(1)

    def _viewer_page_changed(self, page):
        self.page_number.blockSignals(True)
        self.page_number.setValue(page+1)
        self.page_number.blockSignals(False)

    def source_details(self):
        summary = self.engine.summary
        if not summary:
            return
        known = source_manifest()
        extra = f"\nDownloaded: {known['download_date']}\n{known['usage_basis']}\n\n{known['official_url']}\n\nSource limitations:\n" + "\n".join(known["known_source_limitations"]) if summary.sha256 == known['sha256'] else "\nPublisher and usage permissions have not been verified for this local PDF."
        QMessageBox.information(self, "Manual provenance", f"{summary.title}\n{summary.publisher}\nSource ID: {summary.source_id}\nSHA-256: {summary.sha256}" + extra)

    def check_status(self):
        self.status_button.setEnabled(False)
        worker = TaskWorker(self.engine.check_status)
        worker.signals.result.connect(self._status_ready)
        worker.signals.error.connect(lambda message: self.model_status.setText(message))
        worker.signals.finished.connect(lambda: self.status_button.setEnabled(True))
        self._start(worker)

    def _status_ready(self, status):
        if status.connected and status.chat_available and status.embedding_available:
            self.model_status.setText("●  Local models ready")
        elif not status.connected:
            self.model_status.setText("Ollama is offline. Open Ollama, then check again.")
        else:
            missing = [name for name, ready in ((CHAT_MODEL, status.chat_available), (EMBEDDING_MODEL, status.embedding_available)) if not ready]
            self.model_status.setText("Missing model: " + ", ".join(missing))
        self.model_status.setToolTip(f"Chat: {CHAT_MODEL}\nEmbeddings: {EMBEDDING_MODEL}\n{status.error}")

    def _task(self, function, args, success, message):
        self.error_card.hide()
        self._last_error = ""
        self._busy = True
        self.activity.setText(message)
        self.activity.show()
        self.progress.setValue(0)
        self.progress.show()
        self._controls()
        worker = TaskWorker(function, *args, report_progress=True)
        worker.signals.progress.connect(self._progress)
        worker.signals.result.connect(success)
        worker.signals.error.connect(self.show_error)
        worker.signals.finished.connect(self._finished)
        self._start(worker)

    def _start(self, worker):
        self._workers.add(worker)
        worker.signals.finished.connect(lambda current=worker: self._workers.discard(current))
        self.thread_pool.start(worker)

    def _progress(self, value, message):
        self.progress.setValue(value)
        self.activity.setText(message)
        self.eval_progress.setValue(value)
        self.eval_activity.setText(message)

    def _finished(self):
        self._busy = False
        if self.engine.summary and self.chunking.currentData() != self.engine.chunk_size:
            self.chunking.blockSignals(True)
            self.chunking.setCurrentIndex(self.chunking.findData(self.engine.chunk_size))
            self.chunking.blockSignals(False)
        self.activity.hide()
        self.progress.hide()
        self.eval_activity.hide()
        self.eval_progress.hide()
        self._controls()

    def _controls(self):
        ready = self.engine.summary is not None
        for widget in (self.load_sample_button, self.choose_button, self.chunking, self.clear_button, self.run_eval_button):
            widget.setEnabled(not self._busy)
        self.question.setEnabled(ready and not self._busy)
        self.retrieve_button.setEnabled(ready and bool(self.question.toPlainText().strip()) and not self._busy)
        if self.generate_button is not None:
            try:
                self.generate_button.setEnabled(self.packet is not None and not self._busy)
            except RuntimeError:
                pass  # The earlier evidence panel has been deleted after answering.

    def show_error(self, message):
        self._last_error = message
        self.error_label.setText(message)
        self.error_card.show()
        if self.pages.currentIndex() == 1:
            self.eval_note.setText("Evaluation stopped: " + message)

    def _read_results(self):
        paths = [writable_root() / "evaluation" / "latest.json", writable_root() / "evaluation" / "verified_results.json",
                 project_root() / "evaluation" / "verified_results.json"]
        for path in paths:
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if data.get("complete"):
                        self.show_results(data)
                        break
                except (OSError, ValueError, KeyError):
                    continue

    def show_results(self, payload):
        self.eval_table.setRowCount(len(payload["variants"]))
        notes = []
        for row, variant in enumerate(payload["variants"]):
            score = variant["summary"]
            quoted = "N/A" if score["quotation_groundedness"] is None else f"{score['quotation_groundedness']:.0%}"
            values = [f"{variant['source']['chunk_size']} / {variant['source']['overlap']}", f"{score['hit_at_1']:.0%}", f"{score['hit_at_5']:.0%}", quoted,
                      f"{score['answerable_pattern_pass']:.0%}", f"{score['unanswerable_refusal_pass']:.0%}"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.eval_table.setItem(row, col, item)
            self.eval_table.setRowHeight(row, 47)
            notes.append(f"{variant['label']}\nFailures: {', '.join(score['failure_ids']) or 'None under the declared checks'}\n")
            for case in variant["cases"]:
                if not case.get("expected_answer_pass"):
                    notes.append(f"  {case['id']}: {case['question']}\n  {case.get('answer',{}).get('reason',case.get('error',''))}\n")
        self.eval_note.setText(f"Measured local run: {payload['started_at'][:10]}. These are development-set results; inspect the retained failures.")
        self.eval_details.setPlainText("\n".join(notes) + "\nSource caveats: the manual contains conflicting clock speeds and an unspecified xx mA power value. A quote is evidence of what the manual says, not proof that it is correct.")

    def run_evaluation(self):
        if self._busy:
            return
        sys.path.insert(0, str(project_root()))
        from evaluation.run_evaluation import run_comparison
        self.eval_activity.show()
        self.eval_progress.show()
        self._task(run_comparison, (), self._evaluation_ready, "Running 25 questions for each chunking setting…")

    def _evaluation_ready(self, payload):
        self.show_results(payload)
        target = writable_root() / "evaluation" / "latest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def closeEvent(self, event):
        if self._busy:
            self.show_error("Please wait for the current task to finish before closing the app.")
            event.ignore()
        else:
            event.accept()
