"""
Query the RAG pipeline: retrieve the most relevant chunks from Chroma,
then ask Claude to answer the question grounded in that context.

Run:
    python rag.py "What is a RAG pipeline?"
    python rag.py            # then type questions interactively (blank line / Ctrl-C to quit)

If ANTHROPIC_API_KEY is not set, the script still runs retrieval and prints
the relevant chunks (the "R" of RAG), just without the generated answer.
"""
from __future__ import annotations

import os
import sys

import chromadb

import config


def get_collection():
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        return client.get_collection(name=config.COLLECTION_NAME)
    except Exception:
        sys.exit("No collection found. Run `python ingest.py` first.")


def retrieve(collection, question: str, k: int):
    res = collection.query(query_texts=[question], n_results=k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return list(zip(docs, metas, dists))


def build_prompt(question: str, hits) -> str:
    blocks = []
    for i, (doc, meta, _dist) in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {meta['source']})\n{doc}")
    context = "\n\n".join(blocks)
    return (
        "Answer the question using ONLY the context below. "
        "Cite the sources you use with their bracket numbers, e.g. [1]. "
        "If the context does not contain the answer, say so plainly.\n\n"
        f"=== CONTEXT ===\n{context}\n\n"
        f"=== QUESTION ===\n{question}"
    )


def generate(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENROUTER_API_KEY, base_url=config.OPENROUTER_BASE_URL)
    resp = client.chat.completions.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


def answer(collection, question: str) -> None:
    hits = retrieve(collection, question, config.TOP_K)
    if not hits:
        print("No relevant chunks found.")
        return

    if config.OPENROUTER_API_KEY:
        print("\n" + generate(build_prompt(question, hits)) + "\n")
    else:
        print("\n[OPENROUTER_API_KEY not set - showing retrieved context only]\n")

    print("--- sources ---")
    for i, (doc, meta, dist) in enumerate(hits, 1):
        snippet = doc[:140].replace("\n", " ")
        print(f"[{i}] {meta['source']} (distance {dist:.3f}): {snippet}...")


def main() -> None:
    collection = get_collection()

    if len(sys.argv) > 1:
        answer(collection, " ".join(sys.argv[1:]))
        return

    print("RAG ready. Ask a question (blank line or Ctrl-C to quit).")
    try:
        while True:
            q = input("\n> ").strip()
            if not q:
                break
            answer(collection, q)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
