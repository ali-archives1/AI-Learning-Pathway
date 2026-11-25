"""Controlled two-chunking comparison over 20 answerable and 5 missing cases.

Groundedness here means deterministic quotation containment, not a semantic
judge score. Expected-answer checks are simple declared patterns, not a claim
of general answer correctness. Raw outputs and failures are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config import CHAT_MODEL, EMBEDDING_MODEL
from manual_engine import ManualEngine, normalize
from manual_project import file_sha256, project_root, sample_path, writable_root
from utils import ollama_request


def load_cases():
    path = project_root() / "evaluation" / "questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["questions"]
    if len(cases) != 25 or sum(c["answerable"] for c in cases) != 20:
        raise ValueError("The benchmark must contain 20 answerable and 5 unanswerable cases.")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate evaluation IDs.")
    return data, hashlib.sha256(path.read_bytes()).hexdigest()


def retrieval_hit(case, chunks, k):
    return any(c.page == expected["page"] and normalize(expected["anchor"]).casefold() in normalize(c.text).casefold()
               for expected in case["expected_evidence"] for c in chunks[:k])


def score_answer(case, answer):
    if not case["answerable"]:
        return not answer.found and not answer.citations
    return answer.found and all(re.search(pattern, normalize(answer.answer), re.IGNORECASE)
                                for pattern in case["expected_patterns"]) and any(
        citation.page == expected["page"] for citation in answer.citations for expected in case["expected_evidence"])


def quotation_supported(answer):
    chunks = {c.chunk_id: c for c in answer.chunks}
    return bool(answer.citations) and answer.answer == "\n\n".join(c.quote for c in answer.citations) and all(
        c.chunk_id in chunks and c.page == chunks[c.chunk_id].page and
        normalize(c.quote) in normalize(chunks[c.chunk_id].text) for c in answer.citations)


def summarize(cases):
    answerable = [c for c in cases if c["answerable"]]
    missing = [c for c in cases if not c["answerable"]]
    answered = [c for c in cases if c.get("answer", {}).get("found")]
    return {
        "answerable_cases": len(answerable), "unanswerable_cases": len(missing),
        "hit_at_1": sum(c.get("retrieval_hit_at_1", False) for c in answerable) / max(len(answerable), 1),
        "hit_at_5": sum(c.get("retrieval_hit_at_5", False) for c in answerable) / max(len(answerable), 1),
        "answered_count": len(answered),
        "quotation_groundedness": sum(c.get("quotation_supported", False) for c in answered) / len(answered) if answered else None,
        "answerable_pattern_pass": sum(c.get("expected_answer_pass", False) for c in answerable) / max(len(answerable), 1),
        "unanswerable_refusal_pass": sum(c.get("expected_answer_pass", False) for c in missing) / max(len(missing), 1),
        "errors": sum("error" in c for c in cases),
        "failure_ids": [c["id"] for c in cases if not c.get("expected_answer_pass", False) or
                        (c["answerable"] and not c.get("retrieval_hit_at_5", False))],
    }


def write_outputs(payload, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Engineering Manual Q&A evaluation", "", f"Run: {payload['started_at']}", "",
             "20 answerable + 5 unanswerable questions, run independently for each setting. Top-k = 5.", "",
             "| Chunking | Hit@1 | Hit@5 | Quotation support | Expected-answer check | Missing-answer refusal |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for variant in payload["variants"]:
        s = variant["summary"]
        q = "N/A (no answers)" if s["quotation_groundedness"] is None else f"{s['quotation_groundedness']:.0%}"
        lines.append(f"| {variant['label']} | {s['hit_at_1']:.0%} | {s['hit_at_5']:.0%} | {q} | {s['answerable_pattern_pass']:.0%} | {s['unanswerable_refusal_pass']:.0%} |")
    lines += ["", "## Metric meaning", "",
              "Hit@k requires a declared relevant page AND evidence anchor in a retrieved chunk. Denominator: 20 answerable questions.",
              "Quotation support checks that the displayed factual answer is assembled only from quotations in the retrieved text. Denominator: non-refused answers; it does not prove answer relevance, source truth, or semantic correctness.",
              "Expected-answer check requires declared text patterns and an expected citation page. This is a narrow deterministic reference check, not a semantic accuracy estimate.",
              "Refusal success is measured separately over the five questions whose answers are missing, including a numeric placeholder.",
              "The initial test set is AI-assisted and small. These are development-set results, not an independently held-out generalization benchmark.", "", "## Failures and raw cases", ""]
    for variant in payload["variants"]:
        lines += [f"### {variant['label']}", "", f"Failure IDs: {', '.join(variant['summary']['failure_ids']) or 'None under the declared checks'}", ""]
        for case in variant["cases"]:
            status = "PASS" if case.get("expected_answer_pass") else "FAIL"
            lines += [f"- {case['id']} {status}: {case['question']}",
                      f"  Retrieved pages: {case.get('retrieved_pages', [])}; reason: {case.get('answer', {}).get('reason', case.get('error', ''))}"]
    lines += ["", "## Source limitations", "",
              "The source contains conflicting 16 MHz/20 MHz processor statements and an xx mA power-consumption placeholder. Do not treat quotations as engineering approval. Diagrams are not OCR'd or interpreted.",
              "See results.json for all retrieved chunks, model outputs, exact source hashes, timing, settings, and per-case scores."]
    (directory / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_comparison(output=None, *, progress_callback=None, sizes=(900, 450)):
    report = progress_callback or (lambda value, text: print(f"{value:3d}% {text}", flush=True))
    truth, questions_hash = load_cases()
    path = sample_path()
    if not path.is_file() or file_sha256(path) != truth["source_sha256"]:
        raise ValueError("The versioned public manual is missing or changed. Run scripts/download_manual.py first.")
    timestamp = datetime.now(timezone.utc)
    output = Path(output) if output else writable_root() / "evaluation" / "runs" / timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    if (output / "results.json").exists():
        raise FileExistsError("Choose a fresh run directory; previous results are preserved.")
    tags = ollama_request("/api/tags", timeout=10)
    models = [{key: m.get(key) for key in ("name", "digest", "details")} for m in tags.get("models", [])
              if m.get("name") in {CHAT_MODEL, EMBEDDING_MODEL}]
    payload = {"started_at": timestamp.isoformat(), "questions_sha256": questions_hash,
               "source_sha256": truth["source_sha256"], "models": models,
               "settings": {"top_k": 5, "temperature": 0, "seed": 7, "num_ctx": 8192,
                            "num_predict": 180, "selection_protocol": "short quotation with deterministic source resolution v3",
                            "embedding_prefixes": {"documents":"search_document:","queries":"search_query:"},
                            "answer_mode": "verified extractive quotations; no generated factual paraphrase"},
               "variants": [], "complete": False}
    total = len(sizes) * len(truth["questions"])
    completed = 0
    for size in sizes:
        engine = ManualEngine(size, size//6)
        report(int(completed/total*100), f"Indexing {size}-character chunks")
        summary = engine.process_pdf(path)
        variant = {"label": f"{size} chars / {size//6} overlap", "source": {k:v for k,v in asdict(summary).items() if k != "path"}, "cases": []}
        payload["variants"].append(variant)
        for case in truth["questions"]:
            row = {"id": case["id"], "question": case["question"], "answerable": case["answerable"]}
            try:
                packet = engine.retrieve(case["question"])
                answer = engine.answer_from_evidence(packet)
                row.update({"retrieval_hit_at_1": retrieval_hit(case, packet.chunks, 1),
                            "retrieval_hit_at_5": retrieval_hit(case, packet.chunks, 5),
                            "retrieved_pages": [c.page for c in packet.chunks],
                            "retrieval_seconds": packet.retrieval_seconds,
                            "answer": asdict(answer), "quotation_supported": quotation_supported(answer),
                            "expected_answer_pass": bool(score_answer(case, answer))})
            except Exception as exc:
                row.update({"error": str(exc), "expected_answer_pass": False})
            variant["cases"].append(row)
            variant["summary"] = summarize(variant["cases"])
            write_outputs(payload, output)
            completed += 1
            report(int(completed/total*100), f"{size} chars: {case['id']} {'PASS' if row.get('expected_answer_pass') else 'FAIL'} ({completed}/{total})")
    payload["complete"] = True
    payload["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_outputs(payload, output)
    payload["output_directory"] = str(output)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=[900, 450])
    args = parser.parse_args()
    result = run_comparison(args.output, sizes=tuple(args.sizes))
    print(json.dumps([{v["label"]: v["summary"]} for v in result["variants"]], indent=2))
