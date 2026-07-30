"""Fast tests for deterministic RAG utilities."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from utils import parse_json_object, split_text  # noqa: E402


class SplitTextTests(unittest.TestCase):
    def test_short_text_is_one_chunk(self) -> None:
        self.assertEqual(split_text("A short biology note."), ["A short biology note."])

    def test_chunks_overlap_without_exceeding_target_by_much(self) -> None:
        text = " ".join(f"word{index}." for index in range(600))
        chunks = split_text(text, chunk_size=300, overlap=60)
        self.assertGreater(len(chunks), 2)
        self.assertTrue(all(len(chunk) <= 305 for chunk in chunks))


class JsonParsingTests(unittest.TestCase):
    def test_parses_fenced_json(self) -> None:
        payload = {"found": True, "answer": "Mitochondria.", "supporting_pages": [2]}
        parsed = parse_json_object(f"```json\n{json.dumps(payload)}\n```")
        self.assertEqual(parsed, payload)


if __name__ == "__main__":
    unittest.main()
