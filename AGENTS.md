# 🚨 CRITICAL: USE BD AT START OF EVERY TASK! 🚨
#
# BEFORE YOU DO ANYTHING ELSE - STOP AND RUN: `bd ready`
# This shows you EXACTLY what to work on next. Dependencies matter!
# Don't guess - let bd tell you what's actually ready. This prevents:
# ❌ Wasted time on blocked tasks
# ❌ Missing critical dependencies
# ❌ Context switching chaos
# ✅ Crystal clear priorities
# ✅ Smooth dependency flow
# ✅ Organized, predictable progress
#
# Make this your unbreakable habit: TASK → `bd ready` → WORK → `bd update`
# ======================================================================
#
# 📣 Non-negotiable BD Workflow (no exceptions)
# - Run `bd ready` before touching any file. If it reports a block, stop—pushing forward creates rework.
# - Run `bd update` the moment you finish so the next agent inherits fresh context.
# - We log BD misses; repeat offenders trigger remediation because they break dependency planning and waste API credits.
#
# Repository Guidelines

## 🎯 Critical Development Philosophy (Read First!)

### Simplicity-First Design Philosophy (Critical)

**Always seek out the simplest and most maintainable implementation first.** This is a core principle that must guide all technical decisions and proposals.

**Overengineering Prevention Checklist:**
- Before proposing any solution, ask: "What is the simplest approach that solves this problem?"
- Challenge every component: "Is this really necessary, or can we achieve the same result with less complexity?"
- Prefer in-place modifications over new services, classes, or modules
- Choose hardcoded values over configuration when the complexity isn't justified
- Use basic error handling over sophisticated retry mechanisms unless proven necessary
- Implement monitoring and alerting only when the problem justifies the infrastructure

**Complexity Red Flags to Avoid:**
- Separate services for single-purpose functionality
- Multiple configuration parameters for simple features
- Sophisticated state management for straightforward operations
- Circuit breakers, retry mechanisms, or monitoring for basic functionality
- Context-aware logic when simple rules suffice
- Multiple validation layers when one is sufficient

**When Complexity is Justified:**
- The problem genuinely requires sophisticated solutions (e.g., distributed systems, high availability)
- The complexity provides measurable value that outweighs maintenance costs
- The solution is proven to be necessary through real-world usage
- The complexity is isolated and doesn't affect other parts of the system

## 📋 Essential Commands (Quick Reference)

### Daily Development Workflow
- **Start work**: `bd ready` (check what tasks are unblocked)
- **Environment**: `python -m venv .venv && source .venv/bin/activate`
- **Install deps**: `pip install -r requirements.txt`
- **Run tests**: `python -m pytest tests/ -v`
- **Self-review**: `make self-review` (run before marking tasks complete)
- **Local preview**: `python -m http.server -d site 8001`

### Pipeline Operations
- **Harvest**: `python -m src.harvest_chinaxiv_optimized --month $(date -u +"%Y%m")`
- **Translate**: `python -m src.translate --dry-run`
- **Render**: `python -m src.render && python -m src.search_index`
- **Background tasks**: `nohup command &` (see Background Task Guidelines)
- **Seed validation fixtures**: `python scripts/prepare_gate_fixtures.py` (populates sample harvest/translation artifacts when `data/` is empty so the CI gates never pass on empty input)

### Troubleshooting
- **API keys**: `python -m src.tools.env_diagnose --check`
- **Check status**: `python scripts/monitor.py`
- **View logs**: `tail -f data/*.log`

## 🏗️ Project Structure & Module Organization
- Root: docs/PRD.md (product spec), README.md.
- Source: `src/` (e.g., `harvest_oai.py`, `licenses.py`, `translate.py`, `render.py`, `search_index.py`, `utils.py`).
- Data: `data/` (e.g., `raw_xml/`, `seen.json`). Do not commit secrets or large artifacts.
- Site output: `site/` (static HTML, assets, search-index.json).
- Assets: `assets/` (CSS, JS, logos, MathJax, MiniSearch/Lunr).

## Agent Communication Standards

### Response Style & Depth (Required)

This project requires agents to communicate in full, detailed prose that prioritizes clarity over brevity. Use complete sentences and cohesive paragraphs to explain decisions, call out assumptions, and describe tradeoffs with practical impact. Bulleted summaries are welcome for scanability, but they must be supported by descriptive prose. The goal is for a teammate to understand not only what will be done, but why it is the right choice given our constraints.

**Implementation Guidelines:**
- Start with the simplest possible solution
- Add complexity only when the simple solution fails
- Document why each piece of complexity is necessary
- Provide clear rollback paths for any complex features
- Test simple solutions thoroughly before considering complexity

**Self-Review Process (Required):**
Before marking any task as complete, run `make self-review` to apply structured overengineering prevention:
- Review solutions for unnecessary complexity
- Identify simpler approaches that solve 90% of the problem
- Check for potential bugs and edge cases
- Look for optimization opportunities
- Validate against simplicity principles

**Automatic Trigger:**
The self-review process is automatically enforced via git pre-push hooks:
- Runs before `git push` if self-review hasn't been completed in the last hour
- Prompts to run self-review if needed, or allows skipping for CI/CD
- Use `make self-review-status` to check if review is current
- Use `make self-review-skip` for manual override when needed

**CI/CD Integration:**
For automated systems, use: `./scripts/git-push-ci.sh` to skip self-review checks

This process catches overengineering before it becomes technical debt.

**What to include in most responses:**

1) **Context and assumptions** - Briefly restate the problem in your own words and list any assumptions, constraints, or prerequisites that shape the solution (e.g., cost ceilings, CI limits, data availability, external API quotas).

2) **Options considered with tradeoff analysis** - Present realistic alternatives (including "do nothing" when applicable). For each option, explain pros and cons across: correctness/completeness, performance, cost, reliability, maintainability, operational complexity, and risk. Call out edge cases, failure modes, and how we would monitor/mitigate them.

3) **Clear recommendation and rationale** - State your recommended option and why it best fits our goals. Note what would change the decision (decision gates) and how to reverse it (rollback/escape hatch) if needed.

4) **Concrete next steps** - Provide specific commands, files to edit, and checkpoints for verification. For any long-running activity, explicitly run it in the background and show how to monitor it (see Background Task Guidelines).

**When to be brief:** If the user explicitly requests a short or one-line answer, comply but include a single sentence acknowledging key tradeoffs or note that no material tradeoffs exist for the action.

**Formatting guidance:**
- Prefer paragraphs for explanation; use bullets to summarize or enumerate choices.
- Reference concrete file paths, scripts, and commands (e.g., `src/harvest_chinaxiv_optimized.py`, `make dev`).
- Avoid unexplained jargon and shorthand. If you introduce a term (e.g., "smart mode"), define it and explain why it exists.
- If you're changing defaults or behavior, describe impacts on CI, cost, and developer workflow.


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
- **Quick test run**: `python -m pytest tests/ -q`

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). Example: `feat(translate): mask inline math tokens`.
- PRs: concise description, linked issue/PRD section, before/after screenshots for HTML changes, notes on perf/cost impact, and manual test steps.
- Keep PRs small and focused; include `requirements.txt`/config updates when relevant.

## Security & Configuration Tips
- Secrets: set `OPENROUTER_API_KEY` and BrightData creds (`BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`) in CI; never commit keys.
- Config: `src/config.yaml` defines model slugs, glossary, and optional proxy settings. BrightData creds are read from `.env` or CI env.
- Data hygiene: limit `data/raw_xml/` retention; avoid large diffs in VCS.

### LLM API Key Troubleshooting (Agents)
- Symptoms:
  - `OPENROUTER_API_KEY not set` raised by code, or OpenRouter `401 User not found` in responses.
- **NEW: Automatic Environment Resolution**
  - The system now automatically detects and resolves shell/.env mismatches
  - Use `python -m src.tools.env_diagnose --check` to detect mismatches
  - Use `python -m src.tools.env_diagnose --resolve` to fix mismatches
  - Use `python -m src.tools.env_diagnose --validate` to test API keys
- **Manual Troubleshooting** (if automatic resolution fails):
  - Shell: `echo $OPENROUTER_API_KEY` should print a non-empty value.
  - Python (within the same shell): `python3 -c "import os; print(os.getenv('OPENROUTER_API_KEY'))"`.
  - If empty, load `.env` or export the key: `export OPENROUTER_API_KEY=...`.
  - Our client auto-loads `.env` via `openrouter_headers()`; ensure you are running from repo root where `.env` resides.
- CI/GitHub Actions:
  - Confirm `OPENROUTER_API_KEY` secret is configured and passed to the job environment.
- If using a proxy or different shells/terminals, make sure the key is present in the active session before running any `src.translate` or `src.tools.formatting_compare` commands.

## Data Source
- Direct ChinaXiv scraping via BrightData is the default. OAI-PMH remains blocked; Internet Archive removed.

## Live Configuration & Deployment

### Current Status
- **Translation Pipeline**: ✅ Working (fixed API key bug in workers)
- **GitHub Actions**: ✅ Configured for Cloudflare Pages deployment
- **Batch Translation**: ✅ Ready for parallel processing
- **Donation System**: ✅ Crypto donation page implemented
- **UI Improvements**: ✅ Cleaner navigation and layout

### GitHub Actions Workflows
- **Daily Build** (`.github/workflows/build.yml`): Runs at 3 AM UTC, harvests current + previous month (optimized), selects unseen items, translates all newly selected items in parallel, and deploys to Cloudflare Pages
- **Configurable Backfill** (`.github/workflows/backfill.yml`): Configurable parallel processing via inputs (1-10 jobs, 1-100 workers per job)
  - Both workflows persist `data/seen.json` by committing it back to the repository, ensuring cross-job deduplication.

### Manual Backfill (On Demand)
- **Harvester**: `python -m src.harvest_chinaxiv_optimized --month YYYYMM --resume` (run newest→oldest across months; background long runs with `nohup ... &`).
- **Select**: Merge harvested months to a single records file, then `python -m src.select_and_fetch --records <merged>.json --output data/selected.json`.
- **Translate (parallel)**: `jq -r '.[].id' data/selected.json | xargs -n1 -P 20 -I {} sh -c 'python -m src.translate "{}" || true'`.
- **Render + Index + PDFs**: `python -m src.render && python -m src.search_index && python -m src.make_pdf`.
 - **Persist dedupe**: Commit `data/seen.json` after successful runs to avoid reprocessing in subsequent jobs.

### Required GitHub Secrets
- `CF_API_TOKEN`: Cloudflare API token with Pages:Edit permission
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare Account ID
- `OPENROUTER_API_KEY`: OpenRouter API key for translations
- `BRIGHTDATA_API_KEY`: BrightData API key (harvest)
- `BRIGHTDATA_ZONE`: BrightData zone name (harvest)
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
- **Nightly Intake**: All newly harvested items (current + previous month)
- **Parallel Translation**: Tunable; typical 10–30 concurrent workers
- **Backfill Throughput**: 100–2,000 papers/hour depending on concurrency and content
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
