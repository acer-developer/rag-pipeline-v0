# Rag Pipeline - V0 (ChromaDB + OpenRouter)

A minimal, fully local Retrieval-Augmented Generation pipeline.

- **Vector store:** ChromaDB, persistent on disk (`chroma_db/`) — no server to run.
- **Embeddings:** ChromaDB's built-in `all-MiniLM-L6-v2` model — runs locally, no API key.
- **Generation:** Claude (`claude-opus-4-8`) via the Anthropic SDK. Optional —
  retrieval works without it.

## Files
| File | Purpose |
|------|---------|
| `config.py` | All settings (paths, chunk size, top-k, model). |
| `ingest.py` | Read `data/*.md,*.txt` → chunk → embed → store in Chroma. |
| `rag.py` | Retrieve relevant chunks → ask Claude to answer with citations. |
| `data/` | Your source documents. Two demo docs are included. |

## Setup (already done once)
The environment lives in `.venv` (Python 3.11, created with `uv`):
```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
```

## Usage
Run everything with the venv's Python:
```powershell
# 1. Index the documents in data/ (re-run any time you add/edit files)
.venv\Scripts\python.exe ingest.py

# 2a. Ask a one-off question
.venv\Scripts\python.exe rag.py "What is a RAG pipeline?"

# 2b. Or interactive mode
.venv\Scripts\python.exe rag.py
```

## Enabling generated answers (Claude)
Retrieval works out of the box. To get Claude to *write the answer* from the
retrieved context, set your API key first:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # current session only
# permanent: setx ANTHROPIC_API_KEY "sk-ant-..."  (then open a new terminal)
.venv\Scripts\python.exe rag.py "What is a RAG pipeline?"
```

## Using your own documents
Drop `.txt` or `.md` files into `data/` and re-run `ingest.py`. To support other
formats (PDF, DOCX, HTML), extend `load_documents()` in `ingest.py` to extract
their text. Tune `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `TOP_K` in `config.py`.
