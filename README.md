# Rag Pipeline - V0

Two-stage Retrieval-Augmented Generation pipeline for annual reports.
ChromaDB Cloud for vector storage, Ollama (local, free) for the LLM,
Streamlit frontend for chat.

## Architecture

```
┌──────────────┐   ┌──────────────────┐   ┌─────────────────┐   ┌────────────┐
│ data/*.pdf   │ → │ STAGE 1          │ → │ STAGE 2         │ → │ Chroma     │
│ data/*.md    │   │ extract_pdf()    │   │ chunk + upsert  │   │ Cloud      │
│ data/*.txt   │   │ + Ollama vision  │   │ (250/batch)     │   │ 2150 chunks│
└──────────────┘   └────────┬─────────┘   └─────────────────┘   └─────┬──────┘
                            ↓                                          ↑
                   stage1_output/*.md                                  │
                   (one .md per source                                 │
                    + vision captions)                                 │
                                                                       │
                                          ┌────────────────────────────┘
                                          │
                                          ↓
                                   ┌──────────────┐   ┌──────────────┐
                                   │ rag.py       │ → │ Ollama LLM   │
                                   │ hybrid       │   │ llama3.1:8b  │
                                   │ retrieve     │   │ (local)      │
                                   └──────┬───────┘   └──────────────┘
                                          ↓
                                   ┌──────────────┐
                                   │ app.py       │
                                   │ Streamlit UI │
                                   │ localhost:   │
                                   │ 8501         │
                                   └──────────────┘
```

## Folder layout

| Folder | What goes in | Who writes here |
|---|---|---|
| `data/` | **Drop your PDFs / .md / .txt source files here.** This is the only input folder. | You (manually) |
| `stage1_output/` | Per-source markdown files produced by Stage 1 (text + vision captions). | `ingest.py` Stage 1 |
| `chroma_db/` | Used only if you fall back to local Chroma (unused in cloud mode). | `ingest.py` Stage 2 (local mode only) |

## Setup

```powershell
# 1. Create venv (one-time)
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt

# 2. Install Ollama and pull the model
irm https://ollama.com/install.ps1 | iex
ollama pull llama3.1:8b
# optional vision model for chart pages:
ollama pull llama3.2-vision:11b

# 3. Put your secrets in C:\Users\<you>\.env  (NOT in this folder)
#    See .env.example for the required keys.
```

`.env` lives at `~/.env` (user home). The project's `config.py` loads it from there so secrets never enter the repo.

## How to run end-to-end

### Step 1 — Drop your source documents

Put your source files in **`data/`**. Examples:

```
data/
  TATA annual report.pdf      ← put your PDF here
  some_other_doc.md
```

Supported: `.pdf`, `.md`, `.txt`.

### Step 2 — Run ingest (both stages)

```powershell
.venv\Scripts\python.exe ingest.py
```

What happens:

- **Stage 1** (`ingest.py:88` — `stage1_extract()`)
  - For every file in `data/`:
    - PDF → PyMuPDF reads the text layer. If a page has images + little text, the page is rendered to PNG and sent to the Ollama vision model (`llama3.2-vision:11b`) for caption.
    - .md / .txt → copied through unchanged.
  - Output written to **`stage1_output/<filename>.md`** (one .md per source file).

- **Stage 2** (`ingest.py:115` — `stage2_chunk_and_push()`)
  - Reads all `.md` files from `stage1_output/`.
  - Chunks each one (1000 chars, 150 overlap — see `config.py:CHUNK_SIZE`).
  - Upserts to Chroma Cloud in batches of 250 (free-tier cap is 300/request).

### Step 2b — Already have a stage-1 markdown? Skip stage 1 entirely

If you've already extracted the markdown elsewhere (e.g. from another tool, or this pipeline produced it earlier), **drop the .md file directly into `stage1_output/`** and run only stage 2:

```powershell
.venv\Scripts\python.exe -c "from pathlib import Path; import ingest; ingest.stage2_chunk_and_push(sorted(ingest.STAGE1_DIR.glob('*.md')))"
```

The exact loading code is in **`ingest.py:115-141`** — it reads every `.md` in `stage1_output/`, chunks via `chunk_text()` (`ingest.py:21`), and upserts.

### Step 3 — Launch the frontend

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Opens at **http://localhost:8501**.

- **💬 Chat tab** — ask anything. Sources hidden behind an expander.
- **📈 Analytics tab** — chunk count, model info, sources breakdown (sampled to 300 due to Chroma free-tier limit).

## Configuration knobs

All in `config.py`:

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Switch to `openrouter` to use a cloud LLM instead |
| `TEXT_MODEL` | `llama3.1:8b` | Generation model |
| `VISION_MODEL` | `llama3.2-vision:11b` | Used in stage 1 for image-heavy pages |
| `CHUNK_SIZE` | `1000` chars | Chunk window |
| `CHUNK_OVERLAP` | `150` chars | Overlap between consecutive chunks |
| `TOP_K` | `4` | Chunks retrieved per query |

## Retrieval mode

Hybrid (`rag.py:retrieve`):

1. Vector similarity (Chroma embedding search) — top K
2. For each non-stopword keyword in the question: Chroma `where_document={"$contains": kw}` filtered search — top K
3. Merge by id, rank by vector distance, return top K

Each surfaced chunk is tagged in the UI with `via vector`, `via vector+keyword`, etc. so you can see why it came back.

## Public access (testing from another location)

GitHub Pages won't work (it's static-only). Two options to expose your local Streamlit:

```powershell
# ngrok (easiest)
ngrok http 8501
# Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8501
```

Your laptop must stay on; Ollama must be running.

## Cost

Zero. Chroma Cloud free tier (300 records/op, plenty for a single report) + Ollama running locally on your CPU/GPU.
