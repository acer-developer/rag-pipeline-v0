from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "stage1"))
sys.path.insert(0, str(Path(__file__).parent / "stage2"))

import extract
import push


def main() -> None:
    print("=== STAGE 1: input/ -> stage1/*.md ===")
    md_files = extract.run()
    if not md_files:
        print("No source files found in input/. Drop .pdf/.md/.txt files and re-run.")
        return

    print("\n=== STAGE 2: stage1/*.md -> Chroma Cloud ===")
    push.run(md_files)
    print(f"\nDone.")


if __name__ == "__main__":
    main()
