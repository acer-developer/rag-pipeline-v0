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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_collection():
    if config.CHROMA_API_KEY and config.CHROMA_TENANT and config.CHROMA_DATABASE:
        client = chromadb.CloudClient(
            api_key=config.CHROMA_API_KEY,
            tenant=config.CHROMA_TENANT,
            database=config.CHROMA_DATABASE,
        )
    else:
        client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        return client.get_collection(name=config.COLLECTION_NAME)
    except Exception:
        sys.exit("No collection found. Run `python ingest.py` first.")


STOPWORDS = {
    "what","is","the","a","an","of","in","on","to","for","and","or","by","with","how","why","does",
    "do","are","be","was","were","this","that","it","as","at","from","i","you","we","they","but",
    "if","then","than","there","here","which","who","whom","whose","when","where","into","about",
}


def extract_keywords(question: str, max_terms: int = 4) -> list[str]:
    tokens = [t.strip(".,?!:;()[]\"'").lower() for t in question.split()]
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if len(t) > 2 and t not in STOPWORDS and t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= max_terms:
            break
    return out


def retrieve(collection, question: str, k: int, mode: str = "hybrid"):
    results: dict[str, tuple[str, dict, float, str]] = {}

    if mode in ("semantic", "hybrid"):
        vec_hits = collection.query(query_texts=[question], n_results=k)
        for doc, meta, dist, _id in zip(
            vec_hits["documents"][0],
            vec_hits["metadatas"][0],
            vec_hits["distances"][0],
            vec_hits["ids"][0],
        ):
            results[_id] = (doc, meta, dist, "vector")

    if mode in ("keyword", "hybrid"):
        for kw in extract_keywords(question):
            try:
                kw_hits = collection.query(
                    query_texts=[question],
                    n_results=k,
                    where_document={"$contains": kw},
                )
            except Exception:
                continue
            for doc, meta, dist, _id in zip(
                kw_hits["documents"][0],
                kw_hits["metadatas"][0],
                kw_hits["distances"][0],
                kw_hits["ids"][0],
            ):
                if _id in results:
                    d0, m0, dist0, src0 = results[_id]
                    results[_id] = (d0, m0, dist0, src0 + "+keyword")
                else:
                    results[_id] = (doc, meta, dist, f"keyword:{kw}")

    ranked = sorted(results.values(), key=lambda r: r[2])[:k]
    return [(doc, meta, dist, src) for doc, meta, dist, src in ranked]


def build_prompt(question: str, hits) -> str:
    blocks = []
    for i, (doc, meta, _dist, _src) in enumerate(hits, 1):
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

    client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
    resp = client.chat.completions.create(
        model=config.TEXT_MODEL,
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


def answer(collection, question: str) -> None:
    hits = retrieve(collection, question, config.TOP_K)
    if not hits:
        print("No relevant chunks found.")
        return

    if config.LLM_API_KEY:
        print("\n" + generate(build_prompt(question, hits)) + "\n")
    else:
        print(f"\n[LLM provider '{config.LLM_PROVIDER}' not configured - showing retrieved context only]\n")

    print("--- sources ---")
    for i, (doc, meta, dist, src) in enumerate(hits, 1):
        snippet = doc[:140].replace("\n", " ")
        print(f"[{i}] {meta['source']} (d={dist:.3f}, via {src}): {snippet}...")


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
