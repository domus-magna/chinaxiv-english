# Repository Guidelines

## Project Structure & Module Organization
- Root: docs/PRD.md (product spec), README.md.
- Source: `src/` (e.g., `harvest_oai.py`, `licenses.py`, `translate.py`, `render.py`, `search_index.py`, `utils.py`).
- Data: `data/` (e.g., `raw_xml/`, `seen.json`). Do not commit secrets or large artifacts.
- Site output: `site/` (static HTML, assets, search-index.json).
- Assets: `assets/` (CSS, JS, logos, MathJax, MiniSearch/Lunr).

## Build, Test, and Development Commands
- Setup env: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run pipeline (local smoke):
  - Harvest: `python -m src.harvest_ia --limit 10` (or `--all` for full harvest)
  - Translate: `python -m src.translate --dry-run`
  - Render + index: `python -m src.render && python -m src.search_index`
- Preview site: `python -m http.server -d site 8000`
- CI: Nightly GitHub Actions builds and deploys `site/` to Pages (see PRD).
- Note: `src/harvest_oai.py` is deprecated (ChinaXiv OAI-PMH blocked); use `src/harvest_ia.py` instead.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indent, PEP 8 + type hints.
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Formatting: prefer Black (line length 88) + Ruff + isort. Example: `ruff check src && black src`.
- Keep functions small; pure helpers in `utils.py`.
- Preserve math/LaTeX tokens exactly (see PRD “Math/LaTeX preservation”).

## Testing Guidelines
- Framework: pytest (+ pytest-cov).
- Location/pattern: `tests/test_*.py`; mirror module names.
- Targets: unit tests for parsing, masking/unmasking, license gate; smoke test for end-to-end build on 1–2 items.
- Coverage: aim ≥80% on core text/masking utilities.

### Test Commands
- **Run all tests**: `python -m pytest tests/ -v --tb=short`
- **Run specific test file**: `python -m pytest tests/test_translate.py -v`
- **Run with coverage**: `python -m pytest tests/ --cov=src --cov-report=term-missing`
- **Run E2E tests**: `python -m pytest tests/test_e2e_simple.py -v`
- **Run core tests only**: `python -m pytest tests/test_translate.py tests/test_tex_guard.py tests/test_format_translation.py tests/test_job_queue.py tests/test_harvest_ia.py tests/test_e2e_simple.py -v`
- **Quick test run**: `python -m pytest tests/ -q`

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). Example: `feat(translate): mask inline math tokens`.
- PRs: concise description, linked issue/PRD section, before/after screenshots for HTML changes, notes on perf/cost impact, and manual test steps.
- Keep PRs small and focused; include `requirements.txt`/config updates when relevant.

## Security & Configuration Tips
- Secrets: set `OPENROUTER_API_KEY` in CI; never commit keys.
- Config: `src/config.yaml` defines Internet Archive endpoints, model slugs, glossary, license mappings.
- Data hygiene: limit `data/raw_xml/` retention; avoid large diffs in VCS.
- Note: `BRIGHTDATA_API_KEY` is in `.env` but not needed for IA approach (kept for potential future use).

## Data Source: Internet Archive (NOT ChinaXiv OAI-PMH)
- **Issue**: ChinaXiv OAI-PMH endpoint (`https://chinaxiv.org/oai/OAIHandler`) returns "Sorry!You have no right to access this web" - hard-blocked at application level.
- **Solution**: We harvest from **Internet Archive's ChinaXiv mirror** collection instead.
- **Benefits**:
  - ✅ 30,817+ papers with full metadata (title, authors, abstract, subjects, date)
  - ✅ Full PDFs downloadable
  - ✅ No authentication, no geo-blocking, no bot detection
  - ✅ Simple JSON API with cursor pagination
  - ✅ Zero proxy costs (Bright Data not needed!)
- **API Endpoints**:
  - Collection: `https://archive.org/details/chinaxivmirror`
  - Scraping API: `https://archive.org/services/search/v1/scrape?q=collection:chinaxivmirror`
  - Metadata: `https://archive.org/metadata/{identifier}`
  - Download: `https://archive.org/download/{identifier}/{filename}`
- **Implementation**: See `docs/INTERNET_ARCHIVE_PLAN.md` for detailed migration plan
- **Deprecated**: Proxy setup docs (`docs/PROXY_SETUP.md`, `docs/PROXY_REVIEW.md`) archived - not needed for IA approach

