# Engineering Manual Q&A architecture

## Responsibilities

- manual_project.py resolves paths and identifies the exact public PDF by its SHA-256. A different file is not mislabelled as the verified public source.
- ManualEngine reuses the existing RAGEngine's local embedding and model-status utilities. The general study backend and its original behavior remain separate from the new engineering flow.
- process_pdf extracts text page by page, normalizes ligatures, creates overlapping chunks, adds source/page/section identity, embeds the chunks, and atomically installs the new index only after successful processing.
- retrieve embeds an independent question and returns an immutable EvidencePacket. No chat model runs during retrieval. The caller can inspect this packet before generation.
- answer_from_evidence checks the packet's index identity and source chunk text, then asks the language model to propose one short quotation.
- resolve_quote matches that quotation against the retrieved source text, recovers the original text, and derives its source/page/chunk identity. validate_evidence_selection checks membership and provenance. Generated paraphrases are not used as facts.
- EngineeringWindow performs slow work using the existing Qt thread-pool worker. It shows evidence before enabling generation and opens citation pages using Qt's PDF viewer.
- run_evaluation executes independent questions under two chunk settings and records raw evidence plus separately defined metrics.

## Trust boundaries

PDF content and questions are untrusted data, not executable instructions. This application does not execute tools, write files requested by a document, or access URLs extracted from a manual. Model selections must reference the actual retrieved packet. An old packet cannot be used after replacing the document index. Page validity alone is not treated as proof of a factual claim.

Exact source containment limits invented factual prose, but it cannot prove that a quote answers a question, that the source is internally consistent, or that the engineering advice is correct. Those are distinct checks and are not hidden behind a confidence percentage.

Early pilots asked the model to copy long chunk IDs and, later, select numbered line ranges. Actual runs exposed wrong IDs, inaccurate copies, and irrelevant line selections. Those pilot results are retained; the simpler final protocol derives provenance from matching the quote itself. It does not automatically attach a page to an unmatched answer.

## Retrieval and context

The two controlled settings are 900/150 and 450/75 characters/overlap. Chunks do not cross PDF-page boundaries. Stored text preserves the source, with normalization of whitespace and PDF ligatures; a title and verified section label are added only to the embedding input. The Nomic model receives its documented search_document: and search_query: task prefixes. See https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 .

Cosine similarity ranks five candidates. The index is a NumPy matrix in memory, deliberately reusing the existing project rather than introducing an unnecessary database requirement into Build 5A. Build 5B separately demonstrates a real vector database.

## Evaluation

The benchmark checks relevant page plus anchor, not page identity alone. It reports quotation containment among answered cases, answer-reference pattern checks among 20 answerable cases, and refusal among five missing cases. Errors count as failures and are preserved. No judge model is used to claim objective semantic correctness. The development set is not independent held-out evidence.

## Earlier application

src/app.py and src/main_window.py preserve the original study UI. src/manual_app.py launches the engineering extension. The small citation-fallback repair also applies to the original backend. Neither the earlier binary nor its old screenshots are presented as proof of the new behavior.
