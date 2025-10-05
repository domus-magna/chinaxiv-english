# ChinaXiv → English: V1 Test Plan

This plan validates the end-to-end pipeline on a small slice, proves math fidelity and license handling, and exercises deploy to production (Cloudflare Pages). It keeps V1 simple (client-side search on recent items; archives for discovery). Server-side search is out of scope for V1.

## Goals
- Prove the harvest → license → fetch → translate → render → index → deploy pipeline.
- Guarantee math/LaTeX placeholder parity = 100% (no corruption).
- Verify license gate: derivatives allowed vs. title+abstract only.
- Validate cost logging and nightly idempotency.
- Confirm local (dev) and CI (production) flows.

## Prerequisites
- Python 3.11+ installed (`python3.11`).
- Repo dependencies installed: `make setup` or `python3 -m pip install -r requirements.txt`.
- Local `.env` at repo root with your key:
  - `OPENROUTER_API_KEY=sk-or-v1-...` (no quotes or trailing spaces)
- Working OAI endpoint(s):
  - Primary: `http://www.chinaxiv.org/oai2` (note: http)
  - Test Identify: `curl 'http://www.chinaxiv.org/oai2?verb=Identify'`
- For CI deploy (Cloudflare Pages): repo secrets set
  - `OPENROUTER_API_KEY` (rotated key)
  - `CLOUDFLARE_ACCOUNT_ID`
  - `CF_API_TOKEN` (Pages:Edit)

## Test Matrix (Overview)
- Dry-run (local): no API usage; verifies masking/unmasking, rendering, search index.
- Live (local small slice): up to N items; exercise full translation, costs, license gate.
- Harvest fallback: known date window; OAI fallback base URL.
- Failure modes: OAI down; invalid key; non-PDF downloads; license unknown.
- CI deploy: dry-run first, then live; verify Cloudflare URL + custom domain.

## A. Dry-Run Pipeline (Local)
Purpose: validate plumbing with zero API cost.

1) Run smoke build
- `make clean setup test health smoke`
- Or manual:
  - `python -m src.translate --selected data/selected.json --dry-run`
  - `python -m src.render && python -m src.search_index`

2) Verify artifacts
- `ls -la site/index.html`
- `ls -la site/items/*/index.html`
- `ls -la site/search-index.json`

3) Verify behavior
- Open local preview: `make serve` (http://localhost:8000)
- Confirm: item page shows title + abstract; MathJax renders math; footer shows source + license badge.
- Search bar returns matches against the small index.

4) Acceptance
- Pages render without errors; math displays; no external API used; tests pass (`pytest -q`).

## B. Live Pipeline (Local, Small Slice)
Purpose: end-to-end validation of translation and license handling.

1) Health check
- `python -m src.health` (loads `.env` automatically)
- OK if OAI fails locally; OpenRouter must be OK.

2) Harvest small date window
- Preferred with working base URL: `python -m src.harvest_oai --base-url http://www.chinaxiv.org/oai2 --from YYYY-MM-DD --until YYYY-MM-DD`
- If unavailable, proceed (the dev target seeds a sample).

3) Run dev pipeline (serves at the end)
- Default model: `make dev DEV_LIMIT=5 PORT=8001`
- Alternate model (if access issues): `make dev DEV_LIMIT=5 MODEL=z-ai/glm-4.5-air PORT=8001`
- Falls back to dry-run automatically if translation fails; still serves a site.

4) Verify artifacts and behavior
- Data:
  - `data/raw_xml/YYYY-MM-DD/part_*.xml` (harvest pages)
  - `data/records/*.json` (normalized records)
  - `data/selected.json` (selected IDs)
  - `data/translated/<id>.json` (translated fields + license)
  - `data/costs/YYYY-MM-DD.json` (cost log entries)
- Site:
  - `site/index.html` lists recent items
  - `site/items/<id>/index.html` shows title, abstract, license badge, links to original PDF/Markdown
  - Optional: `site/items/<id>/<id>.pdf` if `pandoc` installed

5) License gate spot checks
- If `license.derivatives_allowed == true`: body paragraphs may be present (when LaTeX/PDF extraction succeeded).
- If false/unknown: only title + abstract appear; “Machine translation” banner shown.

6) Math parity spot checks
- Inspect translated JSON (e.g., `data/translated/<id>.json`): ensure formulas (e.g., `$...$`, `$$...$$`) preserved.
- Our checks raise on token parity mismatch; no exceptions should occur.

7) Cost checks
- Inspect `data/costs/YYYY-MM-DD.json`: each item has input/output token estimates and cost per configured pricing.
- Confirm totals are within expected budget for the slice.

8) Acceptance
- Site renders; math intact; license rules applied; cost logs present; no unhandled exceptions.

## C. Harvest Fallback (Backfill a Known Day)
Purpose: ensure harvest/normalize works on a day with content.

1) Identify a date with items (e.g., `2024-11-01`).
2) Harvest: `python -m src.harvest_oai --base-url http://www.chinaxiv.org/oai2 --from 2024-11-01 --until 2024-11-01`
3) Select + translate:
- `python -m src.select_and_fetch --records data/records/<file>.json --limit 5 --output data/selected.json`
- `python -m src.translate --selected data/selected.json` (or add `--model z-ai/glm-4.5-air`)
4) Render + index + serve:
- `python -m src.render && python -m src.search_index`
- `python -m http.server -d site 8001`
5) Acceptance: same as section B.

## D. Failure Modes (Local) and Expected Behavior
- OAI Identify returns 404/timeout: dev pipeline seeds a sample record; proceed; site still builds.
- Invalid OpenRouter key (401): dev pipeline falls back to `--dry-run`; site builds; replace key and rerun for live.
- Non-PDF downloads (HTML error saved as .pdf): fetcher validates magic bytes/headers; skips bad content and continues.
- License unknown/ND: site renders title+abstract only; badge/banners shown.

## E. CI/CD to Production (Cloudflare Pages)
Purpose: nightly live runs and deploy to a real domain.

1) Ensure repo secrets
- `OPENROUTER_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, `CF_API_TOKEN` set in GitHub → Settings → Secrets and variables → Actions.

2) Keep CI dry-run initially (default in `build.yml`)
- Validates site publish nightly without incurring translation costs.

3) Flip CI to live translation (when ready)
- In `.github/workflows/build.yml`, change:
  - `python -m src.translate --selected data/selected.json --dry-run`
  - to: `python -m src.translate --selected data/selected.json`
- Keep selection limit conservative (e.g., `--limit 5`) initially.

4) Trigger a manual run
- GitHub UI: Actions → “build-and-deploy” → Run workflow.
- After success: check `*.pages.dev` URL and mapped custom domain in Cloudflare Pages.

5) Acceptance
- Cloudflare URL serves the same site built locally; pages load; math renders; search works; license badges present.

## F. Idempotency & Reprocessing
- `data/seen.json` prevents reprocessing previously handled IDs in nightly runs.
- To reprocess an item: remove its ID from `data/seen.json` and delete `data/translated/<id>.json`, then rerun translation/render.
- Outputs are written atomically; reruns are deterministic for the same inputs and model.

## G. Non-Goals (V1) and What’s Next
- No server-side search in V1. Discovery via recent items + archives; client-side index for recent content.
- If client index grows too large: shard by time or alphabet and lazy-load shards (V1.1).
- Consider server-side search later (V2): Cloudflare Workers + D1 (SQLite FTS), or Typesense/Meilisearch.
- Batch endpoints: if a provider offers 12–24h batch translation at lower cost, we can adapt the pipeline to submit on day N and collect on day N+1.

## H. Troubleshooting
- Key not picked up: ensure `.env` exists at repo root; line is `OPENROUTER_API_KEY=...`; no quotes. Health: `python -m src.health`.
- Port busy: `make serve PORT=8001` or `lsof -i :8000 && kill -9 <PID>`.
- No harvested records: use backfill window (section C), or rely on seed record behavior in `make dev`.
- Pandoc not installed: PDF generation logs a warning and continues; optional in V1.

## I. Quick Command Cheat Sheet
- Dry-run end-to-end: `make clean setup test health smoke serve`
- Live (local) small slice: `make dev DEV_LIMIT=5 PORT=8001`
- Live with alternate model: `make dev DEV_LIMIT=5 MODEL=z-ai/glm-4.5-air PORT=8001`
- Manual harvest (backfill): `python -m src.harvest_oai --base-url http://www.chinaxiv.org/oai2 --from 2024-11-01 --until 2024-11-01`
- Manual render/index: `python -m src.render && python -m src.search_index`
- Serve: `make serve PORT=8001`

## J. Acceptance Criteria (Checklist)
- [ ] Local dry-run build renders index and at least one item page.
- [ ] Local live slice completes; translated JSONs written; cost logs present.
- [ ] Math fidelity validated on several paragraphs; no parity errors.
- [ ] License gate enforced: ND/unknown → title+abstract only.
- [ ] Search index loads instantly for recent items; results appear under 100ms locally.
- [ ] CI nightly build deploys to Cloudflare Pages (dry-run), site accessible.
- [ ] After enabling live translate in CI, production site shows new items next day.
