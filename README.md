# ChinaXiv → English Translation Static Site (V1)

High-fidelity English translations of ChinaXiv preprints with exact LaTeX/math preservation. Single integration via OpenRouter (default DeepSeek; optional Z.AI GLM). Static site output with client-side search, Markdown, and PDF downloads.

- PRD: `docs/PRD.md`
- Planned structure: `src/`, `data/`, `assets/`, `site/`
- Deploy target: Cloudflare Pages (nightly CI)

## Quick Start

- Python version: 3.11+ recommended (CI uses 3.11). 3.9 may work locally but is not guaranteed long-term.
- Create and activate a Python env, then install deps:
  - `python3 -m pip install -r requirements.txt`
  - Or: `make setup`
- Run tests
  - `python3 -m pytest -q`
  - Or: `make test`
- Local smoke (no external API calls)
  - Harvest from Internet Archive (10 papers): `python -m src.harvest_ia --limit 10`
  - Select & fetch (limit 2): `python -m src.select_and_fetch --records data/records/<latest>.json --limit 2`
  - Translate dry-run (preserves math; no API): `python -m src.translate --selected data/selected.json --dry-run`
  - Render + index: `python -m src.render && python -m src.search_index`
  - Optional PDFs (needs `pandoc`): `python -m src.make_pdf`
  - One-shot pipeline: `python -m src.pipeline --limit 2 --dry-run`
  - Automated smoke: `scripts/smoke.sh` or `make smoke`

**Note:** We harvest from Internet Archive's ChinaXiv mirror (30,817+ papers) instead of the blocked ChinaXiv OAI-PMH endpoint. See `docs/INTERNET_ARCHIVE_PLAN.md` for details.

## Configuration

- `OPENROUTER_API_KEY` must be set in CI secrets for translation
- `config.yaml` controls OAI harvest window, model slugs, glossary, and license mapping

Cost tracking is estimated via crude token counts and `config.yaml` pricing.

## Health Checks

- Quick checks: `python -m src.health --skip-openrouter` or `scripts/health.sh`
- OpenRouter check requires `OPENROUTER_API_KEY`.

## Preview

- `python -m http.server -d site 8000`
- Or: `make serve`

## Dev (live translation)

- Requires Python 3.11+ available as `python3.11` and `OPENROUTER_API_KEY`.
- One-liner: `make dev DEV_LIMIT=5`
- This creates `.venv` with Python 3.11, installs deps, runs tests + health, processes up to 5 new items live, builds site, and serves at `http://localhost:8000`.

### Installing Python 3.11 (macOS options)
- Homebrew: `brew install python@3.11` (then ensure `python3.11` is on PATH)
- pyenv: `brew install pyenv && pyenv install 3.11.9 && pyenv global 3.11.9`

## Production Deploy (Cloudflare Pages)

- Add GitHub repository secrets:
  - `OPENROUTER_API_KEY`: your OpenRouter key (rotate if exposed).
  - `CLOUDFLARE_ACCOUNT_ID`: from Cloudflare dashboard.
  - `CF_API_TOKEN`: API token with Pages:Edit permission.
- CI builds nightly at 03:00 UTC and deploys `site/` to Cloudflare Pages using `cloudflare/pages-action`.
- First-time project creation happens on deploy (project name: `chinaxiv-english`).
- Map a custom domain in Cloudflare Pages → Custom domains.

Batch translation (future option)
- Some providers offer asynchronous batch endpoints with longer SLAs (e.g., 12–24h) at significantly lower cost (~50%).
- DeepSeek and Z.AI GLM on OpenRouter do not currently expose batch endpoints; keep an eye on provider updates.
- If adopted later, the pipeline can submit segment batches on day N and collect results on day N+1 without major structural changes.

## Legal

- "Source: ChinaXiv" attribution and original link must be shown on every item page
- Respect article-level license; if derivatives are disallowed, publish title+abstract only

## Status

V1 pipeline and tests implemented per PRD. Nightly CI builds with dry-run translation and deploys `site/` to Pages.
