from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webapp"))
import config


INPUT_DIR = config.PROJECT_DIR / "input"
STAGE1_DIR = config.PROJECT_DIR / "stage1"


def extract_pdf_to_markdown(path: Path) -> str:
    reader = PdfReader(str(path))
    lines: list[str] = [f"# {path.stem}", ""]
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        lines.append(f"## Page {i}")
        lines.append("")
        if text:
            lines.append(text)
            lines.append("")
    return "\n".join(lines)


def run() -> list[Path]:
    STAGE1_DIR.mkdir(exist_ok=True)
    INPUT_DIR.mkdir(exist_ok=True)

    produced: list[Path] = []
    for path in sorted(INPUT_DIR.glob("**/*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        out_path = STAGE1_DIR / f"{path.stem}.md"

        if ext == ".pdf":
            print(f"  [stage1] extracting {path.name} -> stage1/{out_path.name}")
            md = extract_pdf_to_markdown(path)
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
