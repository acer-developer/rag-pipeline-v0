"""
Follows the YouTube Chroma tutorial step-by-step, on data/policies.txt.

This mirrors the video exactly: ephemeral (in-memory) client, create_collection,
per-line chunking, add() with uuid ids + line-number metadata, peek(), query().

Run:  python tutorial.py

It is independent of ingest.py / rag.py — this is the "learn the basics"
script; those are the persistent pipeline. Being ephemeral, nothing is saved
to disk: every run starts fresh (so re-running never duplicates data here).
"""
import uuid

import chromadb

import config

# --- Step 1: Ephemeral client (in-memory; great for experiments) ---
client = chromadb.EphemeralClient()

# --- Step 2: Create a collection (the index for your data) ---
collection = client.create_collection(name="policies")

# --- Step 3: Read the text file and chunk it (one chunk per non-empty line) ---
lines = (config.DATA_DIR / "policies.txt").read_text(encoding="utf-8").splitlines()

documents, ids, metadatas = [], [], []
for line_no, line in enumerate(lines, start=1):
    line = line.strip()
    if not line:
        continue
    documents.append(line)
    ids.append(str(uuid.uuid4()))            # random unique id, like the video
    metadatas.append({"line": line_no})      # metadata for source citing

# --- Step 4: Add to the collection (Chroma embeds the text automatically) ---
collection.add(documents=documents, ids=ids, metadatas=metadatas)
print(f"Added {collection.count()} documents to collection 'policies'.\n")

# --- Step 5: Peek — view the first records ---
print("=== peek (first records) ===")
peeked = collection.peek(limit=3)
for doc, meta in zip(peeked["documents"], peeked["metadatas"]):
    print(f"  line {meta['line']}: {doc}")

# --- Step 6: Query — semantic similarity search ---
question = "What is the return policy?"
print(f"\n=== query: {question!r} ===")
results = collection.query(query_texts=[question], n_results=2)
for doc, meta, dist in zip(
    results["documents"][0], results["metadatas"][0], results["distances"][0]
):
    print(f"  [line {meta['line']}] (distance {dist:.3f}) {doc}")
