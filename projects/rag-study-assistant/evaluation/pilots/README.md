# Retained development pilots

These are unsuccessful or interrupted development runs, not final completed benchmark results.

- baseline-20261124: quote copying plus model-supplied long chunk IDs. Completed all 25 cases for 900-character chunks and 6 cases for 450-character chunks before interruption. The run was stopped after identifying systematic wrong-ID/copy failures; complete remains false in raw JSON. The 900-character variant refused all five missing questions but missed several valid answers.
- line-selection-20261124: numbered-line selection pilot. Four questions completed before interruption because the model selected genuine but irrelevant lines on the core example questions. It used Nomic task prefixes but still failed answer relevance. complete remains false.
- line-selection-ui: actual Qt/local-model interaction results for the numbered-line pilot. The UI loaded and retrieved evidence correctly, but the answer, expected citation, and missing-answer checks failed.

The final protocol is simpler: propose a short quote, find its original source text, and derive the citation in code. It was selected after a focused prompt probe and then subjected to the full versioned two-setting comparison. Do not combine results from different protocols or describe interrupted pilot percentages as complete-test scores.

All development-set failures are retained. These experiments informed implementation choices, so the final benchmark is development evidence rather than an independent held-out evaluation.
