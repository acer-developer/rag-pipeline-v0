# Rag Pipeline - V0

Two-stage Retrieval-Augmented Generation pipeline for annual reports.
ChromaDB Cloud for the vector store, Ollama (local, free) for the LLM,
Streamlit for the chat UI. Includes a sample TATA annual report.

## Quick start (3 prerequisites, ~10 min one-time)

Install these once, then any clone-and-run after is two clicks:

1. **uv** (Python package manager) -
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. **Ollama** (local LLM runtime) - https://ollama.com/download
3. **ngrok** (optional, only if you want a public URL) - https://ngrok.com/download
   then sign up free and run: `ngrok config add-authtoken <your-token>`

## Clone and run

```powershell
git clone https://github.com/acer-developer/rag-pipeline-v0.git
cd rag-pipeline-v0

# One-time setup (creates venv, installs deps, pulls Ollama model)
setup.bat

# Edit .env and fill in your Chroma Cloud keys (or skip - falls back to local Chroma)
notepad .env

# Index the sample TATA annual report into Chroma
.venv\Scripts\python.exe ingest.py

# Launch the app (Streamlit + ngrok tunnel)
start.bat
```

Browser opens automatically to http://localhost:8501. Public URL (if ngrok is set up)
prints in the launcher window.

To stop: close the launcher window OR run `stop.bat`.

## Project layout

```
.
|-- app.py            Streamlit chat UI (chat + analytics tabs, mode selector)
|-- launcher.py       Auto-finds ngrok/ollama, kills stale processes, opens browser
|-- ingest.py         Stage 1 (PDF -> markdown) + Stage 2 (chunk -> Chroma)
|-- rag.py            Hybrid retrieval: vector + keyword + merge
|-- config.py         Reads .env, exposes settings (LLM provider, chunk sizes, etc.)
|-- start.bat         One-click launch (calls launcher.py)
|-- stop.bat          Kill streamlit + ngrok
|-- setup.bat         One-time deps + Ollama model install
|-- requirements.txt  Python deps (chromadb, openai, streamlit, pymupdf, dotenv)
|-- .env.example      Template for secrets - copy to .env
|-- data/             Source documents (.pdf, .md, .txt) - drop your inputs here
|-- stage1_output/    Per-source markdown from stage 1 (text + vision captions)
```

## Configuration

Settings live in `config.py`. Override via environment variables or `.env`:

| Setting | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openrouter` |
| `TEXT_MODEL` | `llama3.1:8b` | Generation model |
| `VISION_MODEL` | `llama3.2-vision:11b` | For chart/image pages in stage 1 |
| `CHUNK_SIZE` | 1000 chars | Edit in config.py |
| `CHUNK_OVERLAP` | 150 chars | Edit in config.py |
| `TOP_K` | 4 | Chunks retrieved per query |
| `MAX_TOKENS` | 400 | LLM response length cap |

## Retrieval modes

Sidebar in the Streamlit app lets you switch:

- **hybrid** (default) - vector similarity + Chroma `$contains` keyword filter, merged
- **semantic** - pure vector similarity only
- **keyword** - chunks must literally contain extracted query terms

Each chunk's source label shows which mode(s) surfaced it:
`via vector`, `via vector+keyword`, `via keyword:foo`, etc.

## Pipeline details

### Stage 1 - extract source documents to markdown
`ingest.py` reads everything in `data/`:
- `.pdf` -> PyMuPDF text extraction; image-heavy pages rendered to PNG and
  captioned by Ollama vision model
- `.md` / `.txt` -> copied through

Output: one `.md` file per source under `stage1_output/`. You can also drop a
pre-made `.md` directly into `stage1_output/` and skip stage 1 entirely.

### Stage 2 - chunk + push to Chroma
- Reads every `.md` from `stage1_output/`
- Chunks at 1000 chars with 150 overlap
- Upserts to Chroma Cloud in batches of 250 (free-tier cap is 300/op)

### Retrieval (rag.py)
1. Vector similarity query (top K)
2. For each extracted keyword: Chroma `$contains` query (top K)
3. Merge by chunk id, sort by vector distance, return top K

## Public URL via ngrok

`launcher.py` auto-starts ngrok if it's on PATH or in common install locations.
Free-tier ngrok gives a stable random URL like `https://xxxx.ngrok-free.dev`.
First-time visitors see a one-click splash screen (ngrok's abuse prevention).

To get a custom name (e.g. `acer-rag.ngrok.app`), upgrade to ngrok Pro
(\$10/mo). For a free permanent custom URL on your own domain, use
Cloudflare Tunnel instead.

## Cost

Zero. Chroma Cloud free tier + Ollama local + ngrok free tier.
