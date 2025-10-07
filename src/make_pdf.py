from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess

from .utils import log


def has_binary(name: str) -> bool:
    return shutil.which(name) is not None


def md_to_pdf(md_path: str, pdf_path: str) -> bool:
    try:
        subprocess.run(["pandoc", md_path, "-o", pdf_path], check=True)
        return True
    except Exception:
        return False


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PDFs from rendered Markdown using pandoc if available."
    )
    args = parser.parse_args()

    if not has_binary("pandoc"):
        log("pandoc not found; skipping PDF generation")
        return
    count = 0
    for md in glob.glob(os.path.join("site", "items", "*", "*.md")):
        base = os.path.splitext(md)[0]
        pdf_path = base + ".pdf"
        ok = md_to_pdf(md, pdf_path)
        if ok:
            count += 1
    log(f"Generated {count} PDFs")


if __name__ == "__main__":
    run_cli()
