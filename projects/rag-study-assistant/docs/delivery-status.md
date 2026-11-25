# Build 5A delivery status — 2026-11-25

The source application implements page-aware chunking, local embeddings, retrieval, visible evidence before answering, source-validated quotations, clickable PDF citations, two chunking settings, and a controlled evaluation view. The original study application remains available.

## Verified evidence

- 47 deterministic tests: backend boundaries, citations, source identity, evaluation metrics, and interface state.
- 50 real local-model benchmark cases: 25 fixed questions per chunking setting. All failures and earlier pilots are retained.
- 10 actual Qt interface checks: indexing, evidence before answering, answer/page validation, clickable PDF citation, missing-answer refusal, error recovery, and saved evaluation navigation.
- Five source-release checks: model availability, indexing, PDF loading, a supported USB-B answer with page 8, and refusal of the missing weight answer. See the actual JSON record for the outcome.
- Fresh source-export verification using the pinned requirements. This is not a clean Git clone.
- The delivered local launcher passed the same five real-model/PDF checks from the prepared installation. See verification/local-launcher-check.json.
- Published implementation commit ee7a46b806c5013d34302ce79cecb8e3fd49a7ba was downloaded in a fresh GitHub clone on 2026-11-25. A new environment installed from requirements.txt passed all 47 tests and the source-UI smoke test. The official manual download/hash, six screenshots, and 25 relative documentation links also passed. See verification/clean-clone-check.json and clean-clone-tests.txt. Later publication-status edits change documentation only.

The 900-character setting passed 18/20 expected-answer checks; the 450-character setting passed 14/20. Both refused 5/5 missing-answer questions. These are development-set results, not universal accuracy figures. See failure-cases.md for a real relevance error and a reference-page coverage error.

## Release limitation

The Windows executable was built, but Windows Application Control prevented it from starting. Both attempted packaged checks were blocked before application code ran. No packaged-runtime success is claimed and no security setting was changed. A prepared source installation and launcher provide the tested app on Ali's computer.

## Still pending

Ali needs to review the reference answers, add two independently chosen questions, write his own reflection, explain the implementation, and record a short demo. GitHub publication and the clean-clone software check are verified; they do not complete the learner's reflection or defense. Overall Module 5 mastery remains unassessed.
