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
.venv\Scripts\python.exe webapp\ingest.py

# Launch the app (Streamlit + ngrok tunnel)
start.bat
```

Browser opens automatically to http://localhost:8501. Public URL (if ngrok is set up)
prints in the launcher window.

To stop: close the launcher window OR run `stop.bat`.

## Project layout

```
.
|-- start.bat          One-click launch (calls webapp/launcher.py)
|-- stop.bat           Kill streamlit + ngrok
|-- setup.bat          One-time deps + Ollama model install
|-- README.md
|-- .env.example       Template for secrets - copy to .env (kept at project root)
|-- .gitignore
|
|-- input/             Drop your .pdf / .md / .txt source files here
|
|-- stage1/            Stage 1 module + its output markdowns
|   |-- extract.py     PDF -> markdown (PyMuPDF text + Ollama vision)
|   `-- *.md           One markdown per input file (output of stage 1)
|
|-- stage2/            Stage 2 module
|   `-- push.py        Chunk markdowns + upsert to Chroma Cloud
|
`-- webapp/            Web app + orchestrator
    |-- app.py         Streamlit chat UI (chat + analytics tabs, mode selector)
    |-- launcher.py    Auto-finds ngrok/ollama, kills stale processes, opens browser
    |-- ingest.py      Orchestrator: calls stage1 then stage2
    |-- rag.py         Hybrid retrieval: vector + keyword + merge
    |-- config.py      Reads .env (from project root), exposes settings
    `-- requirements.txt
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

### Stage 1 - `stage1/extract.py`
Reads everything in `input/`:
- `.pdf` -> PyMuPDF text extraction; image-heavy pages rendered to PNG and
  captioned by Ollama vision model
- `.md` / `.txt` -> copied through

Output: one `.md` file per source written into `stage1/`. You can also drop a
pre-made `.md` directly into `stage1/` and skip stage 1 entirely.

Run stage 1 alone:
```powershell
.venv\Scripts\python.exe stage1\extract.py
```

### Stage 2 - `stage2/push.py`
- Reads every `.md` from `stage1/`
- Chunks at 1000 chars with 150 overlap
- Upserts to Chroma Cloud in batches of 250 (free-tier cap is 300/op)

Run stage 2 alone:
```powershell
.venv\Scripts\python.exe stage2\push.py
```

Run both via `ingest.py` (orchestrator) for the full pipeline.

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
