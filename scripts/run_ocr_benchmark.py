#!/usr/bin/env python3
"""Proof-of-concept OCR benchmark comparing ocrmypdf output against ground truth."""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pdfminer.high_level import extract_text

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "tests/fixtures/ocr"
OCRMYPDF = "ocrmypdf"


@dataclass
class Sample:
    name: str
    pdf: Path
    truth: Path
    needs_ocr: bool = True


SAMPLES = [
    Sample(
        name="native",
        pdf=FIXTURE_DIR / "native_text.pdf",
        truth=FIXTURE_DIR / "native_truth.txt",
        needs_ocr=False,
    ),
    Sample(
        name="scanned",
        pdf=FIXTURE_DIR / "scanned_text.pdf",
        truth=FIXTURE_DIR / "scanned_truth.txt",
        needs_ocr=True,
    ),
]


def normalize(text: str) -> str:
    return "".join(ch.lower() for ch in text if not ch.isspace())


def run_ocr(sample: Sample) -> tuple[str, float, float]:
    truth = sample.truth.read_text(encoding="utf-8")
    truth_norm = normalize(truth)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = Path(tmpdir) / "input.pdf"
        output_pdf = Path(tmpdir) / "ocr.pdf"
        input_pdf.write_bytes(sample.pdf.read_bytes())

        if sample.needs_ocr:
            cmd = [
                OCRMYPDF,
                "--skip-text",
                "--language",
                "eng",
                str(input_pdf),
                str(output_pdf),
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"ocrmypdf failed for {sample.name}: {exc.stderr.decode('utf-8', 'ignore')}"
                ) from exc
        else:
            output_pdf = input_pdf

        extracted = extract_text(str(output_pdf))
        extracted_norm = normalize(extracted)

    lcs_ratio = SequenceMatcher(None, truth_norm, extracted_norm).ratio()
    coverage = len(extracted_norm) / len(truth_norm) if truth_norm else 0.0
    return extracted, lcs_ratio, coverage


def main() -> None:
    rows = []
    for sample in SAMPLES:
        try:
            text, similarity, coverage = run_ocr(sample)
            rows.append((sample.name, "ok", similarity, coverage, text.strip()))
        except Exception as exc:  # pylint: disable=broad-except
            rows.append((sample.name, f"error: {exc}", 0.0, 0.0, ""))

    print("OCR Benchmark Results")
    print("----------------------")
    for name, status, sim, cov, text in rows:
        print(f"Sample: {name}")
        print(f"  Status:     {status}")
        if status == "ok":
            print(f"  Similarity: {sim:.3f}")
            print(f"  Coverage:   {cov:.3f}")
            print(f"  Extracted:  {text[:120]}" + ("..." if len(text) > 120 else ""))
        print()


if __name__ == "__main__":
    main()
