"""Controller regressions: prevent citations from stale documents/questions.

Uses simulated embeddings, not model-accuracy claims. Real-model UI checks
are recorded separately in docs/verification/source-ui-e2e.json.
"""

import os
import sys
import unittest
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

import numpy as np
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel
from engineering_window import EngineeringWindow
from manual_project import sample_path
from manual_engine import ManualAnswer
from styles import load_preferred_font


@unittest.skipUnless(sample_path().is_file(),"Download the public fixture first")
class WorkspaceStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setFont(QFont(load_preferred_font(),10))

    def setUp(self):
        self.window=EngineeringWindow(check_status_on_start=False)
        self.embedding=patch.object(self.window.engine,"_embed_texts",side_effect=lambda texts,**_:np.tile([[1.,0.]],(len(texts),1)))
        self.embedding.start()
        self.summary=self.window.engine.process_pdf(sample_path())
        self.window._manual_loaded(self.summary)
        self.window._controls()

    def tearDown(self):
        self.embedding.stop()
        self.window.close()
        self.app.processEvents()

    def test_loading_a_manual_clears_old_answer_history(self):
        self.window._history=[object()]
        self.window._manual_loaded(self.summary)
        self.assertEqual(self.window._history,[])

    def test_editing_question_invalidates_previous_evidence(self):
        self.window.question.setPlainText("Original question")
        packet=self.window.engine.retrieve("Original question")
        self.window._evidence_ready(packet)
        self.assertTrue(self.window.generate_button.isEnabled())
        self.window.question.setPlainText("A different question")
        self.assertIsNone(self.window.packet)
        self.assertFalse(self.window.generate_button.isEnabled())

    def test_replaying_old_answer_restores_its_own_question_and_evidence(self):
        old_chunk=self.window.engine._chunks[0]
        answer=ManualAnswer("Earlier question","",False,(),(old_chunk,),"not_found",0)
        self.window.question.setPlainText("Newer question")
        self.window._show_previous(answer)
        self.assertEqual(self.window.question.toPlainText(),answer.question)
        self.assertEqual(self.window.evidence_count.text(),"1 passages")
        labels=self.window.inspector_stack.findChildren(QLabel)
        self.assertTrue(any(old_chunk.chunk_id == label.text() for label in labels))

    def test_failed_reindex_preserves_working_engine_and_setting(self):
        original=self.window.engine
        with patch("engineering_window.ManualEngine._embed_texts",side_effect=RuntimeError("Simulated offline embedding failure")):
            self.window.chunking.setCurrentIndex(1)
            deadline=time.monotonic()+5
            while self.window._busy and time.monotonic()<deadline:
                self.app.processEvents()
                QTest.qWait(20)
        self.assertFalse(self.window._busy)
        self.assertIs(self.window.engine,original)
        self.assertEqual(self.window.chunking.currentData(),900)
        self.assertIn("Simulated offline",self.window._last_error)


if __name__=="__main__":
    unittest.main()
