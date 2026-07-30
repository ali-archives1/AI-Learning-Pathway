"""Thread-safe, in-memory PDF retrieval and grounded Ollama answering."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from threading import RLock
from typing import Callable, Sequence

import numpy as np
from pypdf import PdfReader

from config import (
    CHAT_MODEL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    MEMORY_TURNS,
    NOT_FOUND_RESPONSE,
    SYSTEM_PROMPT,
    TOP_K,
)
from utils import (
    OllamaResponseError,
    PDFProcessingError,
    ollama_request,
    parse_json_object,
    split_text,
    validate_pdf_path,
)

ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    page: int
    text: str
    score: float = 0.0


@dataclass(frozen=True)
class PdfSummary:
    file_name: str
    path: str
    page_count: int
    text_page_count: int
    chunk_count: int


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    source_pages: tuple[int, ...]
    chunks: tuple[DocumentChunk, ...]
    found: bool


@dataclass(frozen=True)
class ModelStatus:
    connected: bool
    chat_available: bool
    embedding_available: bool
    available_models: tuple[str, ...] = ()
    error: str = ""


class RAGEngine:
    """Owns the current document index and conversation memory."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._chunks: tuple[DocumentChunk, ...] = ()
        self._matrix: np.ndarray | None = None
        self._summary: PdfSummary | None = None
        self._history: list[tuple[str, str]] = []

    @property
    def summary(self) -> PdfSummary | None:
        with self._lock:
            return self._summary

    @property
    def history(self) -> tuple[tuple[str, str], ...]:
        with self._lock:
            return tuple(self._history)

    def check_status(self) -> ModelStatus:
        """Check Ollama connectivity and required local model availability."""

        try:
            response = ollama_request("/api/tags", timeout=8)
            names = tuple(
                str(item.get("name", ""))
                for item in response.get("models", [])
                if item.get("name")
            )
            return ModelStatus(
                connected=True,
                chat_available=CHAT_MODEL in names,
                embedding_available=EMBEDDING_MODEL in names,
                available_models=names,
            )
        except Exception as exc:
            return ModelStatus(
                connected=False,
                chat_available=False,
                embedding_available=False,
                error=str(exc),
            )

    def process_pdf(
        self,
        file_path: str | Path,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> PdfSummary:
        """Extract, chunk, embed, and atomically install a PDF index."""

        path = validate_pdf_path(file_path)
        report = progress_callback or (lambda _value, _text: None)
        report(5, "Reading PDF pages...")

        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted and not reader.decrypt(""):
                raise PDFProcessingError(
                    "This PDF is password protected. Please choose an unlocked PDF."
                )
        except PDFProcessingError:
            raise
        except Exception as exc:
            raise PDFProcessingError(
                "The PDF could not be opened. It may be damaged or unsupported."
            ) from exc

        chunks: list[DocumentChunk] = []
        text_pages = 0
        page_total = len(reader.pages)
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            page_chunks = split_text(page_text)
            if page_chunks:
                text_pages += 1
            for chunk_text in page_chunks:
                chunks.append(
                    DocumentChunk(
                        index=len(chunks) + 1,
                        page=page_number,
                        text=chunk_text,
                    )
                )
            extraction_progress = 5 + int(20 * page_number / max(page_total, 1))
            report(extraction_progress, f"Reading page {page_number} of {page_total}...")

        if not chunks:
            raise PDFProcessingError(
                "No readable text was found. This may be a scanned PDF; "
                "use a text-based or OCR-processed PDF."
            )

        report(28, f"Creating embeddings for {len(chunks)} sections...")
        matrix = self._embed_texts(
            [chunk.text for chunk in chunks],
            progress_callback=report,
            progress_start=28,
            progress_end=96,
        )
        summary = PdfSummary(
            file_name=path.name,
            path=str(path),
            page_count=page_total,
            text_page_count=text_pages,
            chunk_count=len(chunks),
        )

        with self._lock:
            self._chunks = tuple(chunks)
            self._matrix = matrix
            self._summary = summary
            self._history.clear()
        report(100, "PDF ready")
        return summary

    def ask(
        self,
        question: str,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> AnswerResult:
        """Retrieve relevant sections and answer with grounded conversation context."""

        clean_question = " ".join(question.split())
        if not clean_question:
            raise ValueError("Enter a question about the PDF.")

        with self._lock:
            if self._matrix is None or not self._chunks:
                raise PDFProcessingError("Select and process a PDF before asking a question.")
            matrix = self._matrix
            chunks = self._chunks
            history = tuple(self._history[-MEMORY_TURNS:])

        report = progress_callback or (lambda _value, _text: None)
        report(12, "Searching the PDF...")
        recent_questions = " ".join(item[0] for item in history[-2:])
        retrieval_query = (
            f"Earlier question context: {recent_questions}\n"
            f"Current question: {clean_question}"
            if recent_questions
            else clean_question
        )
        query_vector = self._embed_texts([retrieval_query])[0]
        scores = matrix @ query_vector
        selected_indices = np.argsort(scores)[::-1][: min(TOP_K, len(chunks))]
        retrieved = tuple(
            replace(chunks[int(index)], score=float(scores[int(index)]))
            for index in selected_indices
        )

        report(48, "Reading the most relevant sections...")
        context = "\n\n".join(
            f"[EXCERPT {position} | PDF PAGE {chunk.page}]\n{chunk.text}"
            for position, chunk in enumerate(retrieved, start=1)
        )
        if history:
            conversation = "\n".join(
                f"User: {user}\nAssistant: {assistant}"
                for user, assistant in history
            )
        else:
            conversation = "(No earlier conversation.)"

        user_prompt = f"""CONVERSATION HISTORY (for reference resolution only):
{conversation}

PDF EXCERPTS:
{context}

CURRENT QUESTION:
{clean_question}
"""
        report(62, f"Generating with {CHAT_MODEL}...")
        response = ollama_request(
            "/api/chat",
            {
                "model": CHAT_MODEL,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {"temperature": 0},
                "keep_alive": "10m",
            },
            timeout=300,
        )
        raw_content = str(response.get("message", {}).get("content", ""))
        if not raw_content:
            raise OllamaResponseError("The chat model returned an empty answer.")
        parsed = parse_json_object(raw_content)

        found = parsed.get("found") is True
        answer = str(parsed.get("answer", "")).strip()
        retrieved_pages = {chunk.page for chunk in retrieved}
        raw_pages = parsed.get("supporting_pages", [])
        if not isinstance(raw_pages, list):
            raw_pages = []
        source_pages = tuple(
            sorted(
                {
                    int(page)
                    for page in raw_pages
                    if str(page).isdigit() and int(page) in retrieved_pages
                }
            )
        )

        if not found or not answer or answer == NOT_FOUND_RESPONSE:
            found = False
            answer = NOT_FOUND_RESPONSE
            source_pages = ()
        elif not source_pages:
            # A grounded response must always expose at least one retrieved page.
            source_pages = (retrieved[0].page,)

        result = AnswerResult(
            question=clean_question,
            answer=answer,
            source_pages=source_pages,
            chunks=retrieved,
            found=found,
        )
        with self._lock:
            self._history.append((clean_question, answer))
        report(100, "Answer ready")
        return result

    def clear_chat(self) -> None:
        with self._lock:
            self._history.clear()

    def clear_document(self) -> None:
        with self._lock:
            self._chunks = ()
            self._matrix = None
            self._summary = None
            self._history.clear()

    def _embed_texts(
        self,
        texts: Sequence[str],
        *,
        progress_callback: ProgressCallback | None = None,
        progress_start: int = 0,
        progress_end: int = 100,
    ) -> np.ndarray:
        if not texts:
            raise ValueError("No text was provided for embedding.")

        vectors: list[list[float]] = []
        total_batches = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
        for batch_number, start in enumerate(
            range(0, len(texts), EMBEDDING_BATCH_SIZE),
            start=1,
        ):
            batch = list(texts[start : start + EMBEDDING_BATCH_SIZE])
            response = ollama_request(
                "/api/embed",
                {
                    "model": EMBEDDING_MODEL,
                    "input": batch,
                    "truncate": True,
                    "keep_alive": "10m",
                },
                timeout=300,
            )
            embeddings = response.get("embeddings")
            if not isinstance(embeddings, list) or len(embeddings) != len(batch):
                raise OllamaResponseError(
                    "The embedding model returned an unexpected result."
                )
            vectors.extend(embeddings)
            if progress_callback:
                fraction = batch_number / max(total_batches, 1)
                value = progress_start + int((progress_end - progress_start) * fraction)
                progress_callback(
                    value,
                    f"Embedding section batch {batch_number} of {total_batches}...",
                )

        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(texts):
            raise OllamaResponseError("The embedding model returned invalid vectors.")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms
