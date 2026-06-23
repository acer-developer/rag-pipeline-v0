from __future__ import annotations

import base64

import chromadb
import fitz
from openai import OpenAI

import config


MIN_TEXT_CHARS = 100
RENDER_DPI = 200


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def make_vision_client() -> OpenAI | None:
    if not config.OPENROUTER_API_KEY:
        return None
    return OpenAI(api_key=config.OPENROUTER_API_KEY, base_url=config.OPENROUTER_BASE_URL)


def describe_page_image(client: OpenAI, png_bytes: bytes) -> str:
    b64 = base64.standard_b64encode(png_bytes).decode("utf-8")
    resp = client.chat.completions.create(
        model=config.VISION_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a page from an annual report. Extract every number, label, "
                            "axis value, legend entry, and caption from any charts, tables, or "
                            "infographics. Then write a dense factual summary of what the page "
                            "shows. No preamble, no markdown."
                        ),
                    },
                ],
            }
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def extract_pdf(path, vision_client: OpenAI | None) -> str:
    doc = fitz.open(path)
    parts: list[str] = []
    for page in doc:
        text = page.get_text().strip()
        has_images = bool(page.get_images())
        needs_vision = has_images and len(text) < MIN_TEXT_CHARS * 5
        if text:
            parts.append(text)
        if needs_vision and vision_client is not None:
            pix = page.get_pixmap(dpi=RENDER_DPI)
            try:
                caption = describe_page_image(vision_client, pix.tobytes("png"))
                if caption:
                    parts.append(f"[VISION p.{page.number + 1}] {caption}")
            except Exception as exc:
                print(f"  vision failed on page {page.number + 1}: {exc}")
    doc.close()
    return "\n\n".join(parts)


def load_documents() -> list[tuple[str, str]]:
    vision_client = make_vision_client()
    if vision_client is None:
        print("OPENROUTER_API_KEY not set — PDFs will be text-only (no vision pass on images).")

    docs: list[tuple[str, str]] = []
    for path in sorted(config.DATA_DIR.glob("**/*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext in (".txt", ".md"):
            docs.append((path.name, path.read_text(encoding="utf-8")))
        elif ext == ".pdf":
            print(f"  extracting {path.name} ...")
            docs.append((path.name, extract_pdf(path, vision_client)))
    return docs


def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    documents = load_documents()
    if not documents:
        print(f"No .txt/.md/.pdf files found in {config.DATA_DIR}. Add some and re-run.")
        return

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = client.get_or_create_collection(name=config.COLLECTION_NAME)

    ids, texts, metadatas = [], [], []
    for filename, content in documents:
        chunks = chunk_text(content, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        for idx, chunk in enumerate(chunks):
            ids.append(f"{filename}::chunk-{idx}")
            texts.append(chunk)
            metadatas.append({"source": filename, "chunk": idx})

    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    print(f"Ingested {len(documents)} document(s) -> {len(ids)} chunk(s).")
    print(f"Collection '{config.COLLECTION_NAME}' now holds {collection.count()} chunk(s).")
    print(f"Stored at: {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
