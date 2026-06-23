# ChromaDB

ChromaDB is an open-source vector database designed for storing and querying
embeddings. It is the vector store used in this pipeline.

## Persistence
A `PersistentClient` writes the collection to disk, so embeddings survive between
runs and do not need to be recomputed every time the program starts. In this
project the data is stored in the local `chroma_db/` folder.

## Collections
Data lives in a named collection. Each entry has an id, the original document
text, an embedding, and optional metadata (here: the source filename and chunk
number). Calling `upsert` instead of `add` makes re-ingestion safe — existing ids
are replaced rather than duplicated.

## Built-in embeddings
By default ChromaDB embeds text with the all-MiniLM-L6-v2 model running locally
through onnxruntime, so no external API key is required for the retrieval step.
Querying returns the closest chunks ranked by embedding distance — a smaller
distance means a closer semantic match.
