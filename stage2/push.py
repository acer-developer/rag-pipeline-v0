from __future__ import annotations

import sys
from pathlib import Path

import chromadb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webapp"))
import config


STAGE1_DIR = config.PROJECT_DIR / "stage1"
BATCH = 250


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def run(md_files: list[Path] | None = None) -> None:
    if not (config.CHROMA_API_KEY and config.CHROMA_TENANT and config.CHROMA_DATABASE):
        raise RuntimeError("Chroma Cloud credentials missing in .env")

    if md_files is None:
        md_files = sorted(STAGE1_DIR.glob("*.md"))
    if not md_files:
        print("  [stage2] no .md files found in stage1/ - nothing to push.")
        return

    client = chromadb.CloudClient(
        api_key=config.CHROMA_API_KEY,
        tenant=config.CHROMA_TENANT,
        database=config.CHROMA_DATABASE,
    )
    collection = client.get_or_create_collection(name=config.COLLECTION_NAME)
    print(f"  [stage2] connected to Chroma Cloud / {config.CHROMA_DATABASE} / {config.COLLECTION_NAME}")

    ids, texts, metadatas = [], [], []
    for md_path in md_files:
        content = md_path.read_text(encoding="utf-8")
        chunks = chunk_text(content, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        for idx, chunk in enumerate(chunks):
            ids.append(f"{md_path.name}::chunk-{idx}")
            texts.append(chunk)
            metadatas.append({"source": md_path.name, "chunk": idx})

    total = len(ids)
    for start in range(0, total, BATCH):
        end = min(start + BATCH, total)
        collection.upsert(ids=ids[start:end], documents=texts[start:end], metadatas=metadatas[start:end])
        print(f"  [stage2] upserted {end}/{total}")
    print(f"  [stage2] pushed {total} chunks from {len(md_files)} file(s).")
    print(f"  [stage2] collection now holds {collection.count()} chunks.")


if __name__ == "__main__":
    run()
