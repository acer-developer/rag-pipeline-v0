from __future__ import annotations

import base64
from pathlib import Path

import chromadb
import fitz
from openai import OpenAI

import config


MIN_TEXT_CHARS = 100
RENDER_DPI = 200
STAGE1_DIR = config.PROJECT_DIR / "stage1_output"


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def make_vision_client() -> OpenAI | None:
    if not config.LLM_API_KEY:
        return None
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


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


def extract_pdf_to_markdown(path: Path, vision_client: OpenAI | None) -> str:
    doc = fitz.open(path)
    lines: list[str] = [f"# {path.stem}", ""]
    for page in doc:
        page_no = page.number + 1
        text = page.get_text().strip()
        has_images = bool(page.get_images())
        needs_vision = has_images and len(text) < MIN_TEXT_CHARS * 5

        lines.append(f"## Page {page_no}")
        lines.append("")
        if text:
            lines.append(text)
            lines.append("")
        if needs_vision and vision_client is not None:
            pix = page.get_pixmap(dpi=RENDER_DPI)
            try:
                caption = describe_page_image(vision_client, pix.tobytes("png"))
                if caption:
                    lines.append(f"**[VISION]** {caption}")
                    lines.append("")
            except Exception as exc:
                print(f"  vision failed on page {page_no}: {exc}")
    doc.close()
    return "\n".join(lines)


def stage1_extract() -> list[Path]:
    STAGE1_DIR.mkdir(exist_ok=True)
    vision_client = make_vision_client()
    if vision_client is None:
        print(f"LLM provider '{config.LLM_PROVIDER}' has no key — text-only extraction (no vision).")

    produced: list[Path] = []
    for path in sorted(config.DATA_DIR.glob("**/*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        out_path = STAGE1_DIR / f"{path.stem}.md"

        if ext == ".pdf":
            print(f"  [stage1] extracting {path.name} -> {out_path.name}")
            md = extract_pdf_to_markdown(path, vision_client)
            out_path.write_text(md, encoding="utf-8")
            produced.append(out_path)
        elif ext in (".md", ".txt"):
            print(f"  [stage1] copying {path.name} -> {out_path.name}")
            out_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            produced.append(out_path)
    return produced


def stage2_chunk_and_push(md_files: list[Path]) -> None:
    if not (config.CHROMA_API_KEY and config.CHROMA_TENANT and config.CHROMA_DATABASE):
        raise RuntimeError("Chroma Cloud credentials missing in ~/.env")

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

    if not ids:
        print("  [stage2] no chunks to push.")
        return

    BATCH = 250
    total = len(ids)
    for start in range(0, total, BATCH):
        end = min(start + BATCH, total)
        collection.upsert(ids=ids[start:end], documents=texts[start:end], metadatas=metadatas[start:end])
        print(f"  [stage2] upserted {end}/{total}")
    print(f"  [stage2] pushed {total} chunks from {len(md_files)} file(s).")
    print(f"  [stage2] collection now holds {collection.count()} chunks.")


def main() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    print("=== STAGE 1: extract source documents -> markdown ===")
    md_files = stage1_extract()
    if not md_files:
        print(f"No source files found in {config.DATA_DIR}. Drop .pdf/.md/.txt files and re-run.")
        return

    print(f"\n=== STAGE 2: chunk markdown -> push to Chroma Cloud ===")
    stage2_chunk_and_push(md_files)
    print(f"\nDone. Stage 1 markdown saved to: {STAGE1_DIR}")


if __name__ == "__main__":
    main()
