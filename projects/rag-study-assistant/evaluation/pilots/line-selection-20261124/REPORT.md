# Engineering Manual Q&A evaluation

Run: 2026-11-24T19:25:26.301897+00:00

20 answerable + 5 unanswerable questions, run independently for each setting. Top-k = 5.

| Chunking | Hit@1 | Hit@5 | Quotation support | Expected-answer check | Missing-answer refusal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 900 chars / 150 overlap | 50% | 100% | 100% | 50% | 0% |

## Metric meaning

Hit@k requires a declared relevant page AND evidence anchor in a retrieved chunk. Denominator: 20 answerable questions.
Quotation support checks that the displayed factual answer is assembled only from quotations in the retrieved text. Denominator: non-refused answers; it does not prove answer relevance, source truth, or semantic correctness.
Expected-answer check requires declared text patterns and an expected citation page. This is a narrow deterministic reference check, not a semantic accuracy estimate.
Refusal success is measured separately over the five questions whose answers are missing, including a numeric placeholder.
The initial test set is AI-assisted and small. These are development-set results, not an independently held-out generalization benchmark.

## Failures and raw cases

### 900 chars / 150 overlap

Failure IDs: A01, A02

- A01 FAIL: Which main microcontroller is the Arduino UNO R3 equipped with?
  Retrieved pages: [2, 4, 7, 1, 6]; reason: verified_quotations
- A02 FAIL: How many digital input/output pins does the UNO R3 have?
  Retrieved pages: [4, 10, 2, 6, 9]; reason: verified_quotations
- A03 PASS: How many analog inputs are listed for the UNO R3 board?
  Retrieved pages: [4, 2, 6, 10, 4]; reason: verified_quotations
- A04 PASS: How much Flash memory is listed for the ATmega328P processor?
  Retrieved pages: [7, 2, 1, 4, 5]; reason: verified_quotations

## Source limitations

The source contains conflicting 16 MHz/20 MHz processor statements and an xx mA power-consumption placeholder. Do not treat quotations as engineering approval. Diagrams are not OCR'd or interpreted.
See results.json for all retrieved chunks, model outputs, exact source hashes, timing, settings, and per-case scores.
