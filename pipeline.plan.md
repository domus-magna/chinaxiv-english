<!-- 9aea2a18-a710-4463-bc29-c57ec16a053a 151ab6e4-83ba-46d8-8801-1edda1c46ec8 -->
# ChinaXiv pipeline audit, remediations, run environment, and staged validation gates

## Executive recommendation (run environment recap)

- **Primary execution**: GitHub Actions on `ubuntu-latest` with explicit apt provisioning of Tesseract + OCR dependencies during each workflow run. Container image pinning remains a stretch goal once we wire up registry publishing.
- **Supporting services**: Cloudflare Pages continues to host the static site; Cloudflare R2 remains the preferred durable store for heavy artifacts (OCR’d PDFs, intermediate JSON) once we wire it in.
- **Fallback decision gate**: If OCR/translation throughput hits GitHub’s 6‑hour limit even after batching, spin up a neutral container runner (Fly.io/Railway) triggered from GHA; defer until metrics prove it necessary.

## Work completed to date (2025‑10‑15)

### Containerisation & CI plumbing
- Removed stale `Dockerfile.ci`/build workflow; for now we rely on `ubuntu-latest` runners with per-job apt installs covering Tesseract + OCR dependencies.
- Updated `preflight.yml`, `harvest-gate.yml`, and `translation-gate.yml` to install system packages inline before invoking the Python validators. This removes “missing binary” failures without introducing registry drift.
- Introduced `pipeline-orchestrator.yml` as a top-level dispatcher (workflow_call) that sequences preflight → harvest → OCR → translation → QA → render. Current version triggers stage workflows and sets the stage for matrix parallelism; polling and gating still TODO.

### Environment validation (Stage 0)
- `src/tools/env_diagnose.py`
  - Added `--preflight` command that batches env/secrets/binary/disk checks.
  - Verifies `OPENROUTER_API_KEY`, `BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`; confirms connectivity to Bright Data (200 response) and OpenRouter header availability.
  - Checks binary presence (`tesseract`, `ocrmypdf`, `pandoc`) and disk space headroom.
  - Emits machine JSON+Markdown reports (`reports/preflight_report.json|md`) and mirrors summary to `site/stats/validation/preflight_report.json`.
- `preflight.yml` installs binaries inline on the runner and then runs `python -m src.tools.env_diagnose --preflight`, uploading reports.

### Harvest stabilization & QA (Stage 1)
- `src/harvest_audit.py`
  - New audit CLI: iterates every `data/records/chinaxiv_*.json` and emits per-file stats (schema pass/fail, duplicate IDs, PDF reachability) plus aggregate metrics.
  - Records per-paper issues, resolves redirect PDFs, and reports to `reports/harvest_audit*.json`. Used to diagnose legacy IA data vs. new BrightData harvests.
- `src/file_service.py`
  - `write_json` now supports `Path` objects (fixes atomic write failures when scrapers passed `Path`).
- `src/harvest_chinaxiv_optimized.py`
  - Added exponential backoff and retry for 429/5xx/timeouts and log clarity for Bright Data responses.
- `src/pdf_pipeline.py`
  - PDF downloads now validate content-type or `%PDF-` magic, enforce ≥1 KB size, and remove bogus files.
  - OCR detection heuristics persisted to `reports/ocr_detection_report.json` (foundation for Stage 2 gate).
- `src/validators/harvest_gate.py`
  - Enforces strict schema (`id/title/abstract/creators/subjects/date/source_url/pdf_url`) with explicit error messaging.
  - Automatically resolves PDFs from landing pages when the saved URL fails (`BeautifulSoup` + relative link handling).
  - Streams PDF head bytes to confirm validity and records resolved URLs and issue lists per paper.
  - Outputs structured `reports/harvest_report.json|md` and mirrors summary to `site/stats/validation/harvest_report.json`.
- `harvest-gate.yml`
  - Runner-based job triggers `python -m src.validators.harvest_gate` (optional `records_path` input) after installing OCR tooling, then uploads artifacts.
- **Outcome**: Latest audits for 2025-02 BrightData harvest show 0% PDF failures; remaining schema misses are limited to old IA identifiers lacking full metadata.

### Translation gating groundwork (Stage 3)
- `translation-gate.yml`
  - Extended with workflow inputs (`batch_size`, `workers`, `matrix_index`) and provisions OCR tooling directly on the runner prior to executing the validator.
  - Currently reruns validator on the runner; gating thresholds to be tightened once queue hardening completes.
- Translation queue hardening is WIP: `data/cloud_jobs.json` inspected; need resumable workers + cost tracking adjustments.

### Reporting & artifacts
- Reports stored under `reports/` and mirrored to `site/stats/validation/` (preflight + harvest). Need to add similar mirroring for OCR/translation/render once complete.
- Added `reports/harvest_audit_202502.json` + aggregate `reports/harvest_audit.json` for dashboards.

## Outstanding work by stage

### Stage 0 – Preflight
- [x] Containerised check
- [ ] Hook report surfacing into `site/monitor.html` auto-refresh

### Stage 1 – Harvest & PDF
- [x] Schema validator + PDF verification
- [ ] Implement Bright Data retry policy in `harvest_chinaxiv.py` (legacy path)
- [ ] Persist harvest audit summaries to R2 for cross-run comparison

### Stage 2 – OCR detection & execution
- [x] Need detection + report scaffold (in `src/pdf_pipeline.py`)
- [ ] Wire gate module (`src/validators/ocr_gate.py`) to assert coverage improvements
- [ ] Add OCR execution retry metrics + fallback API (stored credentials TBD)

### Stage 3 – Translation queue, backoff, idempotency
- [ ] Upgrade `cloud_job_queue` to durable DB or R2 + lock semantics
- [ ] Introduce worker heartbeats, stuck-job auto retry, JSONL logs per job
- [ ] Track per-job cost via `cost_tracker`; emit `reports/costs_summary.json`
- [ ] Harden `_call_openrouter` fallback list + jitter backoff once queue fails after multiple attempts

### Stage 4 – Translation QA & completeness
- [ ] Implement English-language detection (fastText/CLD3 snippet) and length checks
- [ ] Emit `reports/translation_qa_report.{json,md}` and attach to CI
- [ ] Update gate workflow to fail on QA regression and block downstream stages

### Stage 5 – Render & index
- [ ] Gate render/index workflows on QA PASS artifact
- [ ] Validate `search-index.json` schema + counts vs QA pass count
- [ ] Surface site preview comparisons (before/after) for flagged items

### Stage 6 – Observability & ops hygiene
- [ ] Structured JSON logging (stage, record_id, attempt, latency, error)
- [ ] Discord alert pipeline for repeated failures / nightly summary
- [ ] Dashboard synthesis (R2 + Cloudflare Pages) for stage metrics

### Cross-cutting items
- [ ] Unit tests for harvest parser variants, OCR detection, translation QA heuristics
- [ ] Smoke E2E harness translating 2 papers end-to-end inside container
- [ ] Documentation updates (README + developer guide for new workflows)
- [ ] Revisit container pinning only if runner provisioning proves flaky; reintroduce image build pipeline at that point

## Change log (chronological)

1. **System deps on runners** – inline apt installs in translation/harvest/preflight workflows while container publishing remains pending.
2. **Preflight gate** – `src/tools/env_diagnose.py`, `.github/workflows/preflight.yml`, reports + site mirror.
3. **Harvest audit tooling** – `src/harvest_audit.py`, `reports/harvest_audit*.json`.
4. **Write JSON Path fix** – `src/file_service.py` Path support.
5. **Harvest scraper resiliency** – `src/harvest_chinaxiv_optimized.py` retry/backoff.
6. **PDF download hardening** – `src/pdf_pipeline.py` validation + detection telemetry.
7. **Harvest gate rewrite** – `src/validators/harvest_gate.py`, `.github/workflows/harvest-gate.yml`, site mirroring.
8. **Translation gate containerisation** – `.github/workflows/translation-gate.yml` matrix inputs.
9. **Pipeline orchestrator scaffold** – `.github/workflows/pipeline-orchestrator.yml` (needs polling updates).
10. **Reports mirrored to site** – `site/stats/validation/harvest_report.json` etc.

## Next sprint priorities

1. Finish Stage 2 OCR gate (execution report + validation metrics) and hook into orchestrator.
2. Harden translation queue (Stage 3): worker idempotency, stuck-job reset, per-job cost reporting.
3. Implement Translation QA gate (Stage 4) with language detection + length thresholds.
4. Wire orchestrator gating logic (halt downstream stages on previous failure; poll for completion) and add Discord notifications.
5. Begin structured logging and dashboard upload (Stage 6).

## Branching & verification strategy

- Work currently resides on feature branch `ci/validation-gates`. For isolation/testing, create a fresh branch (e.g., `feat/pipeline-harden-20251015`) from the latest main commit and cherry-pick the dated commits or push the current state after rebase.
- Always run `python -m src.tools.env_diagnose --preflight` locally before dispatching workflows.
- Validation order (manual):
  1. `python -m src.tools.env_diagnose --preflight`
  2. `python -m src.harvest_audit --records data/records/<month>.json`
  3. `python -m src.validators.harvest_gate --records …`
  4. (pending) OCR gate
  5. `python -m src.validators.translation_gate`
  6. Render gate (pending)
- For CI: orchestrator should stop at first failing gate; human inspects reports under `reports/` and site mirrors.

---

_Last updated: 2025‑10‑15 by GPT‑5 Codex (pipeline audit agent)._
