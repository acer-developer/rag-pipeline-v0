from __future__ import annotations

import base64
import sys
from pathlib import Path

import fitz
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


MIN_TEXT_CHARS = 100
RENDER_DPI = 200

INPUT_DIR = config.PROJECT_DIR / "input"
STAGE1_DIR = config.PROJECT_DIR / "stage1"


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
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
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


def run() -> list[Path]:
    STAGE1_DIR.mkdir(exist_ok=True)
    INPUT_DIR.mkdir(exist_ok=True)
    vision_client = make_vision_client()
    if vision_client is None:
        print(f"LLM provider '{config.LLM_PROVIDER}' has no key — text-only extraction (no vision).")

    produced: list[Path] = []
    for path in sorted(INPUT_DIR.glob("**/*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        out_path = STAGE1_DIR / f"{path.stem}.md"

        if ext == ".pdf":
            print(f"  [stage1] extracting {path.name} -> stage1/{out_path.name}")
            md = extract_pdf_to_markdown(path, vision_client)
            out_path.write_text(md, encoding="utf-8")
            produced.append(out_path)
        elif ext in (".md", ".txt"):
            print(f"  [stage1] copying {path.name} -> stage1/{out_path.name}")
            out_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            produced.append(out_path)
    return produced


if __name__ == "__main__":
    files = run()
    print(f"Done. {len(files)} file(s) written to stage1/")
