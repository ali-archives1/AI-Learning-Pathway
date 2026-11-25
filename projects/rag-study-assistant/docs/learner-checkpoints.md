# Build 5A learner checkpoints

## Completed learner evidence

Ali provided this implementation outline before the extension was written: chunk the manual, embed it, retrieve relevant chunks, answer with page citations, and test known and missing answers. The earlier written concept check scored 93/100. This does not establish independent project implementation or defense.

## Next working session

1. Launch the app and load the Arduino manual.
2. Ask one answerable question, inspect the passages before generating, and open its cited page.
3. Ask one missing-answer question and explain why related text is insufficient.
4. Switch the chunking setting and predict how the passage boundaries might change.
5. Inspect the measured evaluation report and explain a failure case.
6. Add or improve at least two questions based on your own reading; label any changes to the development set.
7. Complete docs/reflection.md in your own words.
8. Explain process_pdf, retrieve, resolve_quote, and the evaluation denominators without AI answering for you.

## Evidence still requiring learner action or verification

- Personal reflection and independent code explanation.
- A short learner-recorded demo.
- Overall Module 5 scoring across implementation, testing, documentation, and independence.

The assistant must not mark these completed automatically. The software and retained test evidence support the review; they do not replace it.

## Publication verified — 2026-11-25

The implementation and all six screenshots were pushed to the existing GitHub repository. A fresh clone with a new dependency environment passed 47 tests, source-UI startup, manual download/hash, screenshot validity, and documentation-link checks. See verification/clean-clone-check.json. This verifies software reproducibility, not learner independence.
