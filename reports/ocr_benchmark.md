# OCR Benchmark (Proof of Concept)

Date: 2025-10-16

## Samples
- `native_text.pdf`: text-based document with embedded font.
- `scanned_text.pdf`: rasterized image containing the same message.
- `chinese_scanned.pdf`: rasterized Simplified Chinese paragraph drawn with STHeiti.

Ground-truth text is stored alongside each sample in `tests/fixtures/ocr/`.

## Execution
```
python scripts/run_ocr_benchmark.py
```

## Results (local run)
| Sample          | Status | Similarity | Coverage |
|-----------------|--------|------------|----------|
| native          | ok     | 1.000      | 1.000    |
| scanned         | ok     | 1.000      | 1.000    |
| chinese_scanned | ok     | 1.000      | 1.000    |

All three samples now succeed after installing Ghostscript, qpdf, and the `tesseract-ocr-chi-sim` language pack locally. The Chinese raster sample validates end-to-end recognition in the `chi_sim+eng` mode we use in the pipeline.

## Next Steps
- Keep Ghostscript, qpdf, and `tesseract-ocr-chi-sim` provisioned in Stage 2 workflows so CI runs match local success.
- Add additional Chinese fixtures sourced from real ChinaXiv PDFs to catch layout edge cases (tables, multi-column).
- Hook the harness into the Stage 2 gate once accuracy thresholds are defined.
