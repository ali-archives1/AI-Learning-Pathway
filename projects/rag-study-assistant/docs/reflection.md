# Ali's project reflection

Status: learner review and personal reflection pending. This file is not an AI-written claim that Ali independently implemented or defended every component.

## Ali's initial design

Ali wrote: "Split the manual into chunks, embed them, retrieve relevant chunks, then have the model answer with page citations. Test known answers and questions not in the manual to make sure it says not found."

His separate written Module 5 concept check scored 93/100. Project implementation, evaluation interpretation, and defense are separate evidence.

## Implementation decisions to review

1. Reuse the existing desktop app and local models.
2. Show retrieved evidence before generation.
3. Keep factual answers extractive: the model proposes a short quote; code finds the original text and derives its citation.
4. Compare two chunking settings using the same versioned questions.
5. Keep retrieval hits separate from quotation support and answer relevance.
6. Preserve failures, source contradictions, and the original study application.

## Ali should complete in his own words

- What did I personally choose or change, and why?
- Which chunking setting worked better on the measured questions, and what tradeoff did I observe?
- Why did valid page citations alone fail to prevent unsupported answers?
- Why did the numbered-line pilot fail, and how does deriving citations from matched quotations help?
- Which failure surprised me, and how would I investigate it?
- What is the difference between a source quote, a relevant answer, and an engineering fact I can trust?
- What did AI help me produce, and which functions can I explain without assistance?

## AI assistance disclosure

AI assisted with code, interface design, initial benchmark cases, tests, source inspection, and documentation. Benchmark figures must come from retained execution results. This scaffold must not be presented as a completed personal reflection.
