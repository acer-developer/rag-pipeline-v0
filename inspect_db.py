"""
Peek inside the Chroma vector store: list collections, count chunks,
and dump each stored chunk with its id, source metadata, and a preview.

Run:  python inspect_db.py
"""
import chromadb

import config

client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))

print(f"Store path : {config.CHROMA_DIR}")
print(f"Collections: {[c.name for c in client.list_collections()]}\n")

col = client.get_collection(config.COLLECTION_NAME)
print(f"Collection '{col.name}' holds {col.count()} chunk(s).\n")

data = col.get(include=["documents", "metadatas"])
for cid, meta, doc in zip(data["ids"], data["metadatas"], data["documents"]):
    preview = doc[:80].replace("\n", " ")
    print(f"- {cid}")
    print(f"    source={meta['source']} chunk={meta['chunk']} chars={len(doc)}")
    print(f"    text: {preview}...")
