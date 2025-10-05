from __future__ import annotations

import io
import os
import re
import tarfile
import zipfile
from typing import List, Optional

from .utils import log


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _find_main_tex(files: List[str], read_file) -> Optional[str]:
    # Prefer files with \documentclass and \begin{document}
    candidates = []
    for name in files:
        if not name.lower().endswith(".tex"):
            continue
        try:
            txt = read_file(name)
        except Exception:
            continue
        if "\\documentclass" in txt and "\\begin{document}" in txt:
            candidates.append((name, len(txt)))
    if candidates:
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0]
    # Fallback: largest .tex
    texes = [n for n in files if n.lower().endswith(".tex")]
    if texes:
        # Cannot measure size here reliably; pick first
        return texes[0]
    return None


def _extract_tex_content(tex: str) -> str:
    # Keep content strictly inside document body
    m = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, flags=re.DOTALL)
    body = m.group(1) if m else tex
    # Strip full-line comments
    lines = []
    for line in body.splitlines():
        if line.strip().startswith("%"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _split_paragraphs(text: str) -> List[str]:
    # Split on blank lines; normalize whitespace
    paras = []
    for block in re.split(r"\n\s*\n", text):
        t = re.sub(r"\s+", " ", block).strip()
        if len(t) >= 2:
            paras.append(t)
    return paras


def extract_from_latex(archive_path: str) -> Optional[List[str]]:
    if not archive_path or not os.path.exists(archive_path):
        return None
    try:
        if archive_path.lower().endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zf:
                names = zf.namelist()
                def read_file(n):
                    with zf.open(n) as f:
                        return f.read().decode("utf-8", errors="ignore")
                main = _find_main_tex(names, read_file)
                if not main:
                    return None
                tex = read_file(main)
        else:
            with tarfile.open(archive_path, "r:gz") as tf:
                names = [m.name for m in tf.getmembers() if m.isfile()]
                def read_file(n):
                    member = tf.getmember(n)
                    with tf.extractfile(member) as f:
                        return f.read().decode("utf-8", errors="ignore")
                main = _find_main_tex(names, read_file)
                if not main:
                    return None
                tex = read_file(main)
    except Exception as e:
        log(f"latex extract failed: {e}")
        return None
    content = _extract_tex_content(tex)
    return _split_paragraphs(content)


def extract_from_pdf(pdf_path: str) -> Optional[List[str]]:
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    try:
        from pdfminer.high_level import extract_text
        txt = extract_text(pdf_path) or ""
    except Exception as e:
        log(f"pdf extract failed: {e}")
        return None
    # Coalesce into paragraphs using blank lines
    # pdfminer might insert many newlines; compact multiple newlines
    txt = re.sub(r"\n{2,}", "\n\n", txt)
    return _split_paragraphs(txt)


def extract_body_paragraphs(rec: dict) -> List[str]:
    files = rec.get("files") or {}
    # Prefer LaTeX
    paras = extract_from_latex(files.get("latex_source_path"))
    if paras:
        return paras
    paras = extract_from_pdf(files.get("pdf_path"))
    if paras:
        return paras
    return []

