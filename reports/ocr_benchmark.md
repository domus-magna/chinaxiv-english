# OCR Benchmark (Proof of Concept)

Date: 2025-10-16

## Samples
- `native_text.pdf`: text-based document with embedded font.
- `scanned_text.pdf`: rasterized image containing the same message.

Ground-truth text is stored alongside each sample in `tests/fixtures/ocr/`.

## Execution
```
python scripts/run_ocr_benchmark.py
```

## Results (local run)
| Sample  | Status | Similarity | Coverage |
|---------|--------|------------|----------|
| native  | ok     | 1.000      | 1.000    |
| scanned | error  | n/a        | n/a      |

`ocrmypdf` failed on the scanned sample because Ghostscript (`gs`) is absent on the development host. The script reports the missing dependency and recommends installing it (`brew install ghostscript`). Once Ghostscript is available the harness will compute similarity/coverage for the raster sample as well.

## Next Steps
- Install Ghostscript (and qpdf if missing) on CI runners or bake it into the Stage 2 provisioning block so the benchmark can run unattended.
- Expand the fixture set with Chinese-language scans and real pipeline artifacts.
- Hook the harness into the Stage 2 gate once accuracy thresholds are defined.
