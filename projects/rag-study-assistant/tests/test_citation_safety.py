"""Regression checks for citation validation, using simulated model replies.

These tests do not measure real-model accuracy or semantic groundedness.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT if SOURCE_ROOT.is_dir() else PROJECT_ROOT))

import rag_engine
from config import NOT_FOUND_RESPONSE


class CitationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.engine = rag_engine.RAGEngine()
        self.engine._chunks = (
            rag_engine.DocumentChunk(index=1, page=2, text="Motor A operates at 12 V."),
        )
        self.engine._matrix = np.array([[1.0, 0.0]], dtype=np.float32)

    def ask_with_reply(self, reply):
        with (
            patch.object(
                self.engine,
                "_embed_texts",
                return_value=np.array([[1.0, 0.0]], dtype=np.float32),
            ),
            patch.object(
                rag_engine,
                "ollama_request",
                return_value={"message": {"content": json.dumps(reply)}},
            ),
        ):
            return self.engine.ask("What voltage does Motor A use?")

    def assert_refused(self, result):
        self.assertFalse(result.found)
        self.assertEqual(result.answer, NOT_FOUND_RESPONSE)
        self.assertEqual(result.source_pages, ())

    def test_accepts_valid_retrieved_page(self):
        result = self.ask_with_reply({"found": True, "answer": "12 V", "supporting_pages": [2]})
        self.assertTrue(result.found)
        self.assertEqual(result.answer, "12 V")
        self.assertEqual(result.source_pages, (2,))

    def test_refuses_missing_citation(self):
        self.assert_refused(self.ask_with_reply({"found": True, "answer": "99 V", "supporting_pages": []}))

    def test_refuses_invented_page(self):
        self.assert_refused(self.ask_with_reply({"found": True, "answer": "99 V", "supporting_pages": [999]}))

    def test_refuses_absent_citation_field(self):
        self.assert_refused(self.ask_with_reply({"found": True, "answer": "99 V"}))

    def test_refuses_wrong_citation_container(self):
        self.assert_refused(self.ask_with_reply({"found": True, "answer": "99 V", "supporting_pages": "2"}))

    def test_preserves_explicit_refusal(self):
        self.assert_refused(self.ask_with_reply({"found": False, "answer": "No evidence", "supporting_pages": [2]}))

    def test_refuses_empty_answer(self):
        self.assert_refused(self.ask_with_reply({"found": True, "answer": " ", "supporting_pages": [2]}))

    def test_removes_invalid_pages_without_inventing_replacements(self):
        result = self.ask_with_reply({"found": True, "answer": "12 V", "supporting_pages": [999, 2, 2]})
        self.assertTrue(result.found)
        self.assertEqual(result.source_pages, (2,))

    def test_empty_question_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.ask("  ")

    def test_question_without_document_is_rejected(self):
        with self.assertRaises(rag_engine.PDFProcessingError):
            rag_engine.RAGEngine().ask("What voltage does Motor A use?")


if __name__ == "__main__":
    unittest.main()
