# RAG Study Assistant Build Report

## Release

- Build date: July 30, 2026
- Application version: 1.0.0
- Packaging: PyInstaller one-file, windowed
- Release file: `release/RAG Study Assistant.exe`
- Release size: 65,303,936 bytes
- SHA-256: `435CC909C7D02281C27D9504E1813C902E029823EC37BD9A43EBFDB6960369A6`
- Chat model: `llama3.2:3b`
- Embedding model: `nomic-embed-text:latest`
- Observed embedding size: 768 dimensions

The executable is under GitHub's 100 MB per-file limit. It was included because it is useful for a Windows portfolio demonstration, contains no Ollama model data, and passed a binary scan for local home paths and common credential markers.

## Verified Results

- Source compilation: passed
- Application startup and clean shutdown: passed
- Final packaged UI render: passed
- PDF load: passed
- Text extraction: 4 of 4 fixture pages
- Chunk creation: 4 chunks
- Embedding generation: passed
- Similarity retrieval: passed
- Direct question: passed, `Mitochondria`, page 2
- Missing-information question: passed, exact not-found response with no source page
- Follow-up memory question: passed, `cristae`, page 2
- Ollama service check: passed
- `llama3.2:3b` availability: passed
- `nomic-embed-text:latest` availability: passed
- Deterministic unit tests: 3 passed
- Packaged executable integration test: passed

## Test Questions

```text
Direct:
Which organelle generates most of a cell's ATP?

Missing information:
According to this document, who painted the Mona Lisa?

Follow-up:
What are its inner membrane folds called?
```

## Included Files

- Desktop source under `src/`
- Preserved Streamlit prototype under `prototype/`
- Deterministic and Ollama integration tests under `tests/`
- Safe biology-fixture generator under `test_data/`
- Public screenshots under `assets/`
- Pinned dependencies
- PyInstaller spec
- PowerShell build helper
- Launch instructions
- Verified Windows release executable

## Deliberately Excluded

- Virtual environments
- PyInstaller build intermediates
- Python bytecode and caches
- Generated fixture PDF
- Generated JSON results containing local test paths
- Personal study PDFs
- Ollama models and model data
- Logs and temporary files
- Credentials, tokens, and private configuration

## Privacy and Safety Checks

- No GitHub token or API key is present.
- No Google OAuth credential is present.
- No password or model file is present.
- No local home-directory path is present in public documentation.
- The release binary scan found no home path, OneDrive marker, GitHub token prefix, OpenAI key prefix, or Google `client_secret` marker.
- Screenshot review found no token, credential, hidden URL, or local file path.
- The test fixture contains synthetic biology notes rather than a personal document.

## Notes

The final desktop runtime uses direct Ollama HTTP calls, PyPDF, a custom 900-character splitter with 150-character overlap, and an in-memory normalized NumPy matrix. LangChain remains only in the preserved historical Streamlit prototype.
