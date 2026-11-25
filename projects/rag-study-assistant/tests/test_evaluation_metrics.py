"""Verify benchmark denominators, expected sources, and evidence-hit checks."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))

from evaluation.run_evaluation import load_cases, retrieval_hit, summarize
from manual_engine import normalize
from manual_project import file_sha256, sample_path
from pypdf import PdfReader


class EvaluationTests(unittest.TestCase):
    def test_evaluation_set_has_20_answerable_and_5_missing(self):
        truth,digest=load_cases()
        self.assertEqual(len(truth["questions"]),25)
        self.assertEqual(sum(q["answerable"] for q in truth["questions"]),20)
        self.assertEqual(len(digest),64)

    def test_top_k_requires_content_and_correct_page(self):
        case={"expected_evidence":[{"page":4,"anchor":"14 digital input/output"}]}
        irrelevant=SimpleNamespace(page=4,text="Other information")
        relevant=SimpleNamespace(page=4,text="14 digital input/output pins")
        self.assertFalse(retrieval_hit(case,[irrelevant,relevant],1))
        self.assertTrue(retrieval_hit(case,[irrelevant,relevant],5))
        self.assertFalse(retrieval_hit(case,[SimpleNamespace(page=2,text=relevant.text)],5))

    def test_no_answered_cases_do_not_report_perfect_groundedness(self):
        cases=[{"id":"A","answerable":True,"expected_answer_pass":False},
               {"id":"U","answerable":False,"expected_answer_pass":True}]
        result=summarize(cases)
        self.assertIsNone(result["quotation_groundedness"])
        self.assertEqual(result["answerable_pattern_pass"],0)
        self.assertEqual(result["unanswerable_refusal_pass"],1)

    @unittest.skipUnless(sample_path().is_file(),"Download the public fixture first")
    def test_ground_truth_anchors_exist_in_the_versioned_pdf(self):
        truth,_=load_cases()
        self.assertEqual(file_sha256(sample_path()),truth["source_sha256"])
        pages=[normalize(p.extract_text() or "").casefold() for p in PdfReader(sample_path()).pages]
        for case in truth["questions"]:
            for expected in case["expected_evidence"]:
                with self.subTest(case=case["id"],page=expected["page"]):
                    self.assertIn(normalize(expected["anchor"]).casefold(),pages[expected["page"]-1])


if __name__ == "__main__":
    unittest.main()
