from __future__ import annotations

import time
from collections import Counter

import streamlit as st

import config
import rag


st.set_page_config(page_title="Annual Report RAG - V0", page_icon="📊", layout="wide")


@st.cache_resource
def get_collection():
    return rag.get_collection()


collection = get_collection()

st.title("Annual Report RAG — V0")
st.caption(f"Provider: `{config.LLM_PROVIDER}` · Model: `{config.TEXT_MODEL}` · Vector store: Chroma Cloud / `{config.CHROMA_DATABASE}`")

chat_tab, analytics_tab = st.tabs(["💬 Chat", "📈 Analytics"])


with chat_tab:
    if "history" not in st.session_state:
        st.session_state.history = []

    for turn in st.session_state.history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn["role"] == "assistant" and turn.get("hits"):
                with st.expander(f"Sources ({len(turn['hits'])})"):
                    for i, (doc, meta, dist, src) in enumerate(turn["hits"], 1):
                        st.markdown(
                            f"**[{i}] {meta['source']}** · chunk {meta['chunk']} · "
                            f"distance `{dist:.3f}` · via `{src}`"
                        )
                        st.text(doc[:600] + ("..." if len(doc) > 600 else ""))

    question = st.chat_input("Ask anything about the annual report…")
    if question:
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving + generating…"):
                t0 = time.time()
                hits = rag.retrieve(collection, question, config.TOP_K)
                if not hits:
                    answer = "_No relevant chunks found in the indexed documents._"
                elif config.LLM_API_KEY:
                    answer = rag.generate(rag.build_prompt(question, hits))
                else:
                    answer = f"_LLM provider `{config.LLM_PROVIDER}` not configured._"
                elapsed = time.time() - t0

            st.markdown(answer)
            st.caption(f"⏱ {elapsed:.1f}s · {len(hits)} chunks")
            if hits:
                with st.expander(f"Sources ({len(hits)})"):
                    for i, (doc, meta, dist, src) in enumerate(hits, 1):
                        st.markdown(
                            f"**[{i}] {meta['source']}** · chunk {meta['chunk']} · "
                            f"distance `{dist:.3f}` · via `{src}`"
                        )
                        st.text(doc[:600] + ("..." if len(doc) > 600 else ""))

        st.session_state.history.append({"role": "assistant", "content": answer, "hits": hits})


with analytics_tab:
    total = collection.count()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total chunks", f"{total:,}")
    c2.metric("LLM provider", config.LLM_PROVIDER)
    c3.metric("Text model", config.TEXT_MODEL)

    st.divider()
    st.subheader("Configuration")
    st.json({
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "top_k": config.TOP_K,
        "vision_model": config.VISION_MODEL,
        "llm_base_url": config.LLM_BASE_URL,
        "chroma_collection": config.COLLECTION_NAME,
        "chroma_database": config.CHROMA_DATABASE,
    })

    st.divider()
    st.subheader("Sources breakdown")
    SAMPLE_LIMIT = 300
    sample = collection.get(limit=min(total, SAMPLE_LIMIT), include=["metadatas"])
    counts = Counter(m["source"] for m in sample["metadatas"])
    if counts:
        st.caption(f"Sampled {min(total, SAMPLE_LIMIT):,} of {total:,} chunks (Chroma Cloud free-tier cap).")
        st.dataframe(
            [{"source": k, "chunks_in_sample": v} for k, v in counts.most_common()],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No documents indexed yet. Run `ingest.py` first.")
