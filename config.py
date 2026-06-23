"""Shared configuration for the RAG pipeline."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent
GLOBAL_ENV = Path.home() / ".env"
LOCAL_ENV = PROJECT_DIR / ".env"

if GLOBAL_ENV.exists():
    load_dotenv(GLOBAL_ENV)
if LOCAL_ENV.exists():
    load_dotenv(LOCAL_ENV, override=True)

# --- Chroma Cloud credentials (read from .env; blank if you stay local) ---
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "")
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
VISION_MODEL = "anthropic/claude-sonnet-4.5"
TEXT_MODEL = "anthropic/claude-sonnet-4.5"
DATA_DIR = PROJECT_DIR / "data"          # source documents (.txt / .md) live here
CHROMA_DIR = PROJECT_DIR / "chroma_db"   # persistent on-disk vector store

# --- Vector store ---
COLLECTION_NAME = "knowledge_base"
# ChromaDB's built-in embedding model (all-MiniLM-L6-v2). Runs locally via
# onnxruntime; downloads ~80MB the first time, then works fully offline.

# --- Chunking ---
CHUNK_SIZE = 1000      # characters per chunk
CHUNK_OVERLAP = 150    # characters shared between consecutive chunks

# --- Retrieval ---
TOP_K = 4              # how many chunks to retrieve per query

MODEL = TEXT_MODEL
MAX_TOKENS = 1024
