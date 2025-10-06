# ChinaXiv Translations

English translations of Chinese academic papers from ChinaXiv.

## Features
- Automated translation pipeline
- Search functionality
- PDF generation
- Responsive web interface
- API access
- Monitoring dashboard
- Batch processing

## Quick Start
1. Clone repository
2. Install dependencies
3. Configure environment
4. Run pipeline

See [SETUP.md](docs/SETUP.md) for detailed instructions.

## Documentation
- [Setup Guide](docs/SETUP.md) - Complete setup instructions
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [API Documentation](docs/API.md) - API reference
- [Contributing Guide](docs/CONTRIBUTING.md) - Development guide
- [Workflows](docs/WORKFLOWS.md) - GitHub Actions workflows
- [PRD](docs/PRD.md) - Product requirements document

## Architecture
- **Harvesting**: Internet Archive ChinaXiv mirror collection
- **Translation**: OpenRouter API with DeepSeek V3.2-Exp model
- **Deployment**: Cloudflare Pages with GitHub Actions
- **Monitoring**: Consolidated monitoring service with alerts, analytics, and performance metrics

## Support ChinaXiv Translations

Help us continue translating Chinese academic papers to English! Your donations support:

- 💰 OpenRouter API costs for translations
- 🖥️ Server hosting and infrastructure
- 🔧 Ongoing development and improvements
- 📚 Keeping the service free and accessible

### Cryptocurrency Donations

We accept donations in multiple cryptocurrencies:

- **Bitcoin (BTC)**: `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`
- **Ethereum (ETH)**: `0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6`
- **Solana (SOL)**: `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM`
- **USD Coin (USDC)**: `0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6`
- **Tether (USDT)**: `0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6`
- **Stacks (STX)**: `SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7`

Visit our [donation page](https://chinaxiv-english.pages.dev/donation.html) for QR codes and detailed instructions.

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
- **Papers Translated**: 3,096 / 3,461 (89.5%)
- **Site**: https://chinaxiv-english.pages.dev
- **Monitoring**: https://chinaxiv-english.pages.dev/monitor

## Contributing
See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for contribution guidelines.

## License
MIT License - see [LICENSE](LICENSE) for details.
