# Retrieval-Augmented Generation (RAG)

RAG is a technique for grounding a large language model's answers in an external
knowledge source instead of relying only on what the model memorized during
training. A RAG pipeline has two phases.

## Indexing (offline)
Source documents are split into smaller chunks. Each chunk is converted into a
vector embedding — a list of numbers that captures its meaning — and stored in a
vector database. This only needs to happen once per document, or whenever a
document changes.

## Retrieval + Generation (per query)
When a user asks a question, the question is embedded with the same model and the
vector database returns the chunks whose embeddings are most similar to it. Those
chunks are placed into the model's prompt as context, and the model is asked to
answer using that context. Because the answer is built from retrieved text, RAG
reduces hallucination and lets the model cite its sources.

## Why teams use it
RAG keeps answers current without retraining the model, works over private data
the model never saw, and makes answers auditable through citations.
