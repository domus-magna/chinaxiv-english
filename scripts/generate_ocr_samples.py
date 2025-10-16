#!/usr/bin/env python3
"""Generate simple OCR benchmark sample PDFs and ground-truth text."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "tests/fixtures/ocr"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

NATIVE_TEXT = "Sample OCR benchmark text with digits 12345."
SCANNED_TEXT = "Scanned OCR benchmark text for evaluation."  # same complexity
CHINESE_TEXT = "这是一个用于 OCR 基准测试的中文样例。"


def write_native_pdf(path: Path, text: str) -> None:
    # Minimal PDF with embedded text operators (Helvetica)
    content = f"BT /F1 18 Tf 72 720 Td ({text}) Tj ET"
    pdf = f"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n" \
          f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 612 792] >> endobj\n" \
          f"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n" \
          f"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n" \
          f"5 0 obj << /Length {len(content)} >> stream\n{content}\nendstream\nendobj\n" \
          f"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000144 00000 n \n0000000241 00000 n \n0000000303 00000 n \ntrailer << /Size 6 /Root 1 0 R >>\nstartxref\n{303 + len(content) + 20}\n%%EOF\n"
    path.write_bytes(pdf.encode("utf-8"))


def write_scanned_pdf(path: Path, text: str) -> None:
    img = Image.new("RGB", (1200, 400), color="white")
    draw = ImageDraw.Draw(img)
    font = load_font(48, prefers_cjk="测试" in text)
    draw.text((60, 150), text, fill="black", font=font)
    img.save(path, "PDF")


def load_font(size: int, prefers_cjk: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Find a font that supports the desired glyphs. When prefers_cjk is True,
    try common CJK fonts before falling back to the default bitmap font.
    """
    candidates = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB W3.ttc",
        # Debian/Ubuntu
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    if not prefers_cjk:
        candidates.insert(0, "DejaVuSans.ttf")

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue

    # Best-effort fallback
    return ImageFont.load_default()


def main() -> None:
    write_native_pdf(FIXTURE_DIR / "native_text.pdf", NATIVE_TEXT)
    write_scanned_pdf(FIXTURE_DIR / "scanned_text.pdf", SCANNED_TEXT)
    write_scanned_pdf(FIXTURE_DIR / "chinese_scanned.pdf", CHINESE_TEXT)
    (FIXTURE_DIR / "native_truth.txt").write_text(NATIVE_TEXT, encoding="utf-8")
    (FIXTURE_DIR / "scanned_truth.txt").write_text(SCANNED_TEXT, encoding="utf-8")
    (FIXTURE_DIR / "chinese_truth.txt").write_text(CHINESE_TEXT, encoding="utf-8")
    print("Generated OCR sample PDFs and ground truth.")


if __name__ == "__main__":
    main()
