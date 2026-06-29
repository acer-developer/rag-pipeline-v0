"""Shared configuration for the RAG pipeline."""
import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).parent
PROJECT_DIR = APP_DIR.parent
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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = "ollama"

if LLM_PROVIDER == "ollama":
    LLM_BASE_URL = OLLAMA_BASE_URL
    LLM_API_KEY = OLLAMA_API_KEY
    TEXT_MODEL = os.getenv("TEXT_MODEL", "llama3.1:8b")
    VISION_MODEL = os.getenv("VISION_MODEL", "llama3.2-vision:11b")
else:
    LLM_BASE_URL = OPENROUTER_BASE_URL
    LLM_API_KEY = OPENROUTER_API_KEY
    TEXT_MODEL = os.getenv("TEXT_MODEL", "anthropic/claude-sonnet-4.5")
    VISION_MODEL = os.getenv("VISION_MODEL", "anthropic/claude-sonnet-4.5")
INPUT_DIR = PROJECT_DIR / "input"
STAGE1_DIR = PROJECT_DIR / "stage1"
CHROMA_DIR = PROJECT_DIR / "chroma_db"

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
MAX_TOKENS = 400
