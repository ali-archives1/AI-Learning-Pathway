"""Evidence safety, metadata, chunking, and document-state regression tests."""

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" if (ROOT / "src").is_dir() else ROOT))

import manual_engine
from manual_engine import EvidencePacket, ManualChunk, ManualEngine, normalize
from utils import PDFProcessingError


def fake_embeddings(texts, **_kwargs):
    return np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (len(texts), 1))


class EvidenceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = ManualEngine()
        self.chunk = ManualChunk(1, 4, "Motor A operates at 12 V. Weight is not specified.", "doc-p4-c1", "doc", "Operating limits")
        self.engine._chunks = (self.chunk,)
        self.engine._matrix = fake_embeddings([""])
        self.engine._index_id = "index-one"
        self.packet = EvidencePacket("What voltage does Motor A use?", (replace(self.chunk, score=0.8),), "index-one", 0.1)

    def reply(self, value):
        with patch.object(manual_engine, "ollama_request", return_value={"message":{"content":json.dumps(value)}}):
            return self.engine.answer_from_evidence(self.packet)

    def selected(self, quote="Motor A operates at 12 V.", chunk_id="doc-p4-c1"):
        return {"found":True, "evidence":[{"chunk_id":chunk_id,"quote":quote}]}

    def test_answer_consists_of_exact_supported_quote(self):
        answer = self.reply(self.selected())
        self.assertTrue(answer.found)
        self.assertEqual(answer.answer, "Motor A operates at 12 V.")
        self.assertEqual(answer.source_pages, (4,))

    def test_generated_paraphrase_is_never_used_as_fact(self):
        data = self.selected()
        data["answer"] = "Motor A weighs 500 grams."
        self.assertNotIn("500", self.reply(data).answer)

    def test_invented_quote_is_rejected_even_on_real_page(self):
        self.assertFalse(self.reply(self.selected("Motor A operates at 99 V.")).found)

    def test_unknown_chunk_id_is_rejected(self):
        self.assertFalse(self.reply(self.selected(chunk_id="invented")).found)

    def test_no_citations_never_gets_automatic_page(self):
        answer = self.reply({"found":True,"evidence":[]})
        self.assertFalse(answer.found)
        self.assertEqual(answer.source_pages, ())

    def test_non_boolean_found_is_rejected(self):
        data = self.selected()
        data["found"] = "true"
        self.assertFalse(self.reply(data).found)

    def test_malformed_entry_is_rejected(self):
        self.assertFalse(self.reply({"found":True,"evidence":["not a citation"]}).found)

    def test_all_evidence_must_validate(self):
        data = self.selected()
        data["evidence"].append({"chunk_id":"invented","quote":"A bad quote."})
        self.assertFalse(self.reply(data).found)

    def test_explicit_missing_answer_has_no_citations(self):
        self.assertFalse(self.reply({"found":False,"evidence":[]}).found)

    def test_whitespace_normalization_preserves_quote_support(self):
        self.assertTrue(self.reply(self.selected("Motor A  operates\nat 12 V.")).found)

    def test_single_number_is_not_sufficient_context(self):
        self.assertFalse(self.reply(self.selected("12")).found)

    def test_stale_packet_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "manual changed"):
            self.engine.answer_from_evidence(replace(self.packet,index_id="old"))

    def test_tampered_packet_is_rejected(self):
        altered = replace(self.chunk,text="Motor A operates at 99 V.")
        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.engine.answer_from_evidence(replace(self.packet,chunks=(altered,)))

    def test_placeholder_is_not_a_numeric_answer(self):
        chunk = replace(self.chunk,text="PMax Maximum Power Consumption - - xx mA")
        packet = replace(self.packet,chunks=(chunk,))
        citations, reason = ManualEngine.validate_evidence_selection(self.selected(chunk.text),packet)
        self.assertEqual(citations, ())
        self.assertEqual(reason, "source_placeholder")

    def test_invalid_model_json_fails_closed(self):
        with patch.object(manual_engine,"ollama_request",return_value={"message":{"content":"broken"}}):
            self.assertFalse(self.engine.answer_from_evidence(self.packet).found)

    def test_retrieval_does_not_generate_or_use_history(self):
        self.engine._history = [("old irrelevant question", "untrusted earlier answer")]
        with patch.object(self.engine,"_embed_texts",side_effect=fake_embeddings) as embed:
            packet = self.engine.retrieve("Current question")
        self.assertEqual(embed.call_args.args[0], ["search_query: Current question"])
        self.assertEqual(packet.chunks[0].page, 4)

    def test_quote_citation_is_derived_from_the_actual_source(self):
        data={"found":True,"quote":"Motor A operates at 12 V.","answer":"99 V"}
        answer=self.reply(data)
        self.assertTrue(answer.found)
        self.assertEqual(answer.answer,"Motor A operates at 12 V.")
        self.assertEqual(answer.source_pages,(4,))

    def test_invalid_quote_selection_is_rejected(self):
        for quote in (None,{},"","12","Motor A operates at 99 V."):
            answer=self.reply({"found":True,"quote":quote})
            self.assertFalse(answer.found)

    def test_model_case_changes_do_not_invent_source_text(self):
        answer=self.reply({"found":True,"quote":"motor a OPERATES at 12 v."})
        self.assertTrue(answer.found)
        self.assertEqual(answer.answer,"Motor A operates at 12 V.")

    def test_query_dimension_mismatch_is_rejected(self):
        with patch.object(self.engine,"_embed_texts",return_value=np.ones((1,3))):
            with self.assertRaisesRegex(ValueError,"does not match"):
                self.engine.retrieve("Voltage?")


class IngestionTests(unittest.TestCase):
    def make_pdf(self, directory):
        path = Path(directory)/"public-test.pdf"
        pdf = canvas.Canvas(str(path))
        for page in range(1,3):
            pdf.drawString(50,750,f"Section {page}: Motor limits")
            for line in range(12):
                pdf.drawString(50,720-line*20,f"Motor A operates at 12 V. Source line {line} on page {page}.")
            pdf.showPage()
        pdf.save()
        return path

    def test_source_metadata_and_page_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_pdf(temporary)
            engine = ManualEngine(450,75)
            with patch.object(engine,"_embed_texts",side_effect=fake_embeddings):
                summary = engine.process_pdf(path)
            self.assertEqual(summary.page_count,2)
            self.assertTrue(summary.sha256)
            self.assertTrue(all(c.source_id == summary.source_id for c in engine._chunks))
            self.assertEqual({c.page for c in engine._chunks},{1,2})
            self.assertTrue(all(c.section for c in engine._chunks))
            self.assertEqual(len({c.chunk_id for c in engine._chunks}),len(engine._chunks))

    def test_two_strategies_produce_different_chunk_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.make_pdf(temporary)
            counts=[]
            for size in (900,450):
                engine=ManualEngine(size,size//6)
                with patch.object(engine,"_embed_texts",side_effect=fake_embeddings):
                    counts.append(engine.process_pdf(path).chunk_count)
            self.assertGreater(counts[1],counts[0])

    def test_failed_load_preserves_previous_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=self.make_pdf(temporary)
            engine=ManualEngine()
            with patch.object(engine,"_embed_texts",side_effect=fake_embeddings):
                original=engine.process_pdf(path)
                with self.assertRaises(PDFProcessingError):
                    engine.process_pdf(Path(temporary)/"missing.pdf")
            self.assertEqual(engine.summary,original)

    def test_invalid_chunk_configuration_is_rejected(self):
        for size,overlap in ((0,0),(100,100),(100,-1)):
            with self.assertRaises(ValueError):
                ManualEngine(size,overlap)

    def test_empty_or_overlong_query_is_rejected(self):
        engine=ManualEngine()
        for question in ("  ","x"*2001):
            with self.assertRaises(ValueError):
                engine.retrieve(question)

    def test_unicode_ligature_normalization(self):
        self.assertEqual(normalize("ofﬂine\n  manual"),"offline manual")


if __name__ == "__main__":
    unittest.main()
