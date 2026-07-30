"""Application-wide configuration for the RAG Study Assistant."""

from __future__ import annotations

APP_NAME = "RAG Study Assistant"
APP_VERSION = "1.0.0"

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
CHAT_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text:latest"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
EMBEDDING_BATCH_SIZE = 16
TOP_K = 5
MEMORY_TURNS = 4

NOT_FOUND_RESPONSE = "I could not find that in the provided PDF."

SYSTEM_PROMPT = f"""You are a careful study assistant.

Answer using only the supplied PDF excerpts. Conversation history may clarify
pronouns or follow-up questions, but it is not evidence. Do not use outside
knowledge, fill gaps, or make assumptions.

Return one JSON object with exactly these fields:
- "found": true when the excerpts directly support an answer, otherwise false
- "answer": a clear, concise answer, or "{NOT_FOUND_RESPONSE}" when found is false
- "supporting_pages": a list of PDF page numbers that directly support the answer

If found is true, every factual statement must be supported by the listed pages.
If the excerpts do not contain the answer, set found to false, use the exact
not-found sentence above, and return an empty supporting_pages list.
"""
