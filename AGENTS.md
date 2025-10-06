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
- Preview site: `python -m http.server -d site 8001`
- CI: Nightly GitHub Actions builds and deploys `site/` to Pages (see PRD).
- Note: `src/harvest_oai.py` is deprecated (ChinaXiv OAI-PMH blocked); use `src/harvest_ia.py` instead.

### Background Task Guidelines
- **Always run long-running tasks in the background** to avoid blocking the terminal
- Use `&` to run commands in background: `command &`
- For interactive sessions, use `nohup` for persistent background tasks: `nohup command &`
- Monitor background jobs with `jobs` command
- Bring background jobs to foreground with `fg`
- Examples:
  - Formatting samples: `python -m src.tools.formatting_compare --count 5 &`
  - Translation pipeline: `python -m src.translate &`
  - Site server: `python -m http.server -d site 8001 &`

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

### LLM API Key Troubleshooting (Agents)
- Symptoms:
  - `OPENROUTER_API_KEY not set` raised by code, or OpenRouter `401 User not found` in responses.
- Always verify environment variables when you see these errors:
  - Shell: `echo $OPENROUTER_API_KEY` should print a non-empty value.
  - Python (within the same shell): `python3 -c "import os; print(os.getenv('OPENROUTER_API_KEY'))"`.
  - If empty, load `.env` or export the key: `export OPENROUTER_API_KEY=...`.
  - Our client auto-loads `.env` via `openrouter_headers()`; ensure you are running from repo root where `.env` resides.
- CI/GitHub Actions:
  - Confirm `OPENROUTER_API_KEY` secret is configured and passed to the job environment.
- If using a proxy or different shells/terminals, make sure the key is present in the active session before running any `src.translate` or `src.tools.formatting_compare` commands.

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

## Live Configuration & Deployment

### Current Status
- **Translation Pipeline**: ✅ Working (fixed API key bug in workers)
- **GitHub Actions**: ✅ Configured for Cloudflare Pages deployment
- **Batch Translation**: ✅ Ready for parallel processing
- **Donation System**: ✅ Crypto donation page implemented
- **UI Improvements**: ✅ Cleaner navigation and layout

### GitHub Actions Workflows
- **Daily Build** (`.github/workflows/build.yml`): Runs at 3 AM UTC, processes 5 papers, deploys to Cloudflare Pages
- **Configurable Backfill** (`.github/workflows/backfill.yml`): Configurable parallel processing via inputs (1-10 jobs, 1-100 workers per job)

### Required GitHub Secrets
- `CF_API_TOKEN`: Cloudflare API token with Pages:Edit permission
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare Account ID
- `OPENROUTER_API_KEY`: OpenRouter API key for translations
- `DISCORD_WEBHOOK_URL`: Discord webhook for notifications (optional)

### Cloudflare Pages Configuration
- **Project Name**: `chinaxiv-english`
- **Build Output Directory**: `site`
- **Production Branch**: `main`
- **Build Command**: (empty - GitHub Actions handles building)
- **Environment Variables**: `OPENROUTER_API_KEY`, `DISCORD_WEBHOOK_URL`

### Translation System
- **Model**: DeepSeek V3.2-Exp via OpenRouter
- **Cost**: ~$0.0013 per paper
- **Full Backfill Cost**: ~$45 for 34,237 papers
- **Workers**: Configurable (10-100 per job)
- **Parallelization**: Up to 20 concurrent jobs

### Donation System
- **Supported Cryptocurrencies**: BTC, ETH, SOL, USDC, USDT, STX
- **Donation Page**: `/donation.html`
- **Integration**: Links in main page and footer
- **Features**: Click-to-copy addresses, QR codes, mobile-friendly

### Performance Metrics
- **Current Daily Processing**: 5 papers/day
- **Parallel Processing**: 100-2,000 papers/hour
- **Full Backfill Time**: 3.4 hours (extreme parallel) to 14 days (current)
- **Site Performance**: <3 second load times, global CDN

### Monitoring & Maintenance
- **GitHub Actions**: Built-in workflow monitoring
- **Cloudflare Analytics**: Site performance and traffic
- **OpenRouter Dashboard**: API usage and costs
- **Discord Notifications**: Build success/failure alerts

### Custom Domain Setup (When Purchased)
1. **Purchase Domain**: From any registrar (GoDaddy, Namecheap, etc.)
2. **Add to Cloudflare**: Add site to Cloudflare dashboard
3. **Update Nameservers**: Point domain to Cloudflare nameservers
4. **Connect to Pages**: Add custom domain in Cloudflare Pages
5. **SSL Certificate**: Automatically issued by Cloudflare
6. **DNS Configuration**: Automatic CNAME record creation

### Troubleshooting
- **Build Failures**: Check GitHub Actions logs, verify secrets
- **Translation Failures**: Verify OpenRouter API key, check credits
- **Deployment Issues**: Check Cloudflare API token permissions
- **Site Issues**: Check build output directory, verify DNS

### Documentation
- **Complete Setup Guide**: `docs/archive/old/CLOUDFLARE_COMPLETE_SETUP.md`
- **Wrangler CLI Setup**: `docs/archive/old/WRANGLER_CLI_SETUP.md`
- **Parallelization Strategy**: `docs/archive/old/PARALLELIZATION_STRATEGY.md`
- **Backfill Strategy**: `docs/archive/old/BACKFILL_STRATEGY.md`
- **Donation Setup**: `docs/archive/old/DONATION_SETUP_PLAN.md`

## Pull Request Review Guidelines

### Checking All Review Types
When reviewing pull requests, **ALWAYS check for ALL types of reviews and comments**:

1. **Regular Comments**: `gh pr view --comments` or `gh pr view --json comments`
2. **Review Summaries**: `gh pr view --json reviews` 
3. **Inline Review Comments**: `gh api repos/{owner}/{repo}/pulls/{number}/comments`

### Critical Review Sources
- **mentatbot**: Human-style reviews with detailed analysis
- **chatgpt-codex-connector[bot]**: Codex automated reviews with inline suggestions
- **cursor[bot]**: Cursor IDE automated reviews
- **Manual reviews**: From human contributors

### Review Priority Levels
- **P1 (Critical)**: Fix before merging - causes runtime errors or data corruption
- **Medium**: Significant issues that should be addressed
- **Low**: Minor improvements or style issues

### Common Review Issues
- **Workflow issues**: Hardcoded values, missing setup steps, broken notifications
- **Documentation**: Incorrect paths, references to non-existent files
- **Code quality**: Race conditions, memory issues, API mismatches
- **Security**: Hardcoded secrets, missing validation

### Review Response Process
1. **Check all review types** using the commands above
2. **Prioritize P1 issues** - fix critical problems first
3. **Address documentation issues** - update paths and references
4. **Test fixes** - validate changes work correctly
5. **Add detailed PR comments** explaining what was fixed
6. **Push fixes** and notify reviewers

### GitHub CLI Commands for Reviews
```bash
# Check regular comments
gh pr view --comments

# Check review summaries  
gh pr view --json reviews

# Check inline review comments (CRITICAL - often missed!)
gh api repos/seconds-0/chinaxiv-english/pulls/{number}/comments

# Get all review data
gh pr view --json comments,reviews
```

**Remember**: Inline review comments are separate from regular comments and require the specific API endpoint to access!
