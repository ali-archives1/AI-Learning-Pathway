# Measured failures and limits

The full 50-run comparison is in evaluation/verified_results.json and evaluation/REPORT.md. No failed cases were removed. All questions were declared before the first pilot; implementation was improved using this set, so these are development results, not held-out generalization evidence.

## Final comparison

| Setting | Chunks | Evidence Hit@1 | Evidence Hit@5 | Expected-answer check | Missing-answer refusal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 900 characters / 150 overlap | 24 | 13/20 | 19/20 | 18/20 | 5/5 |
| 450 characters / 75 overlap | 43 | 10/20 | 20/20 | 14/20 | 5/5 |

All 19 non-refused answers in the 900-character setting and all 15 in the 450-character setting passed deterministic quotation containment. This is not 100% answer accuracy. The model can quote a source faithfully while answering the wrong question, and the reference-page/pattern check can also reject an otherwise plausible answer.

The 900-character setting remains the UI default because it performed better on the declared answer-reference checks in this run, while preserving the original project's setting. The smaller setting found the expected evidence in more cases at rank five but provided less surrounding context and had more quote-selection refusals. Chunk size alone changed between the final two settings; model, prompts, source, top-k, and questions were held fixed. Do not attribute the difference to a universal rule about chunk sizes.

## 900-character failures

- **A15, USB connection also supplying power:** the expected page-8 evidence did not occur in the top five under the declared anchor check. The model instead quoted a real page-5 USB-voltage row. The quote is source-supported but does not answer the power-supply question. This is both a retrieval miss and an answer-relevance failure.
- **A18, A4/SDA function:** the relevant evidence was retrieved, but the model copied the table row with the wrong row number. Exact matching rejected the quote and returned not found. This is a conservative false refusal, not missing evidence.

## 450-character failures

- **A01:** the model returned the correct ATmega328P name from page 2, but page 2 was outside the initial expected-page alternatives for this question. The strict reference check marked a failure. This illustrates incomplete reference-page coverage; it must not be casually described as a semantically wrong chip name. A future reference-set revision should review this case, preserve version 1.0 and these results, and rerun comparisons.
- **A04, A05, A12, A16, A17:** the expected evidence was available in the top five, but the selected quotation did not match the retrieved text closely enough for acceptance. The application refused rather than manufacture a corrected quotation or attach an unrelated page. Inspect the raw model replies in verified_results.json to see the copying/selection failures.

## Earlier development failures

- The original backend attached the first retrieved page when the model gave no valid page citation. A simulated unsupported 99 V answer was therefore made to look sourced. That fallback was removed, with regression tests in both source copies.
- A real-model pilot using model-supplied long chunk IDs produced incorrect IDs and copied text inaccurately. Its completed 900-character run and partial 450-character run are retained under evaluation/pilots/baseline-20261124.
- A numbered-line pilot produced genuine but irrelevant source passages, including pin-table rows as the answer to the pin-count question. Its four-case pilot and failed actual-UI checks are retained under evaluation/pilots.
- The final protocol asks for one short quote and derives the citation by matching source text. It improves this development set without turning quotation validity into a relevance guarantee.

## Source problems and limits

The manual says up to 16 MHz on page 2 and up to 20 MHz on page 7. Page 5 gives numeric maximum power consumption as xx mA. These must not be converted into one invented specification. Text extraction also omits information that exists only in drawings or raster images.

Exact source matching is deliberately conservative. Paraphrases, altered row numbers, or formatting differences can lead to refusal. Case, whitespace, and PDF ligature normalization are tolerated, but arbitrary fuzzy matching is not used to conceal changes in specifications.

## Useful next experiments

Ali can investigate query rewriting or hybrid retrieval for A15, table-aware chunking for processor/pin tables, and held-out questions written independently after the implementation is frozen. These are follow-up experiments, not claimed features or results of this build.
