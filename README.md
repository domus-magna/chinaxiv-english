# ChinaXiv → English Translation Static Site (V1)

High-fidelity English translations of ChinaXiv preprints with exact LaTeX/math preservation. Single integration via OpenRouter (default DeepSeek; optional Z.AI GLM). Static site output with client-side search, Markdown, and PDF downloads.

- PRD: `docs/PRD.md`
- Planned structure: `src/`, `data/`, `assets/`, `site/`
- Deploy target: GitHub Pages (nightly CI)

## Quick Start (skeleton)

- Create and activate a Python env
- Pin deps (Jinja2, lxml, requests, pyyaml, pandoc/tectonic) in `requirements.txt`
- Implement pipeline scripts in `src/` as outlined in the PRD

## Configuration

- `OPENROUTER_API_KEY` must be set in CI secrets for translation
- `config.yaml` controls OAI harvest window, model slugs, glossary, and license mapping

## Legal

- "Source: ChinaXiv" attribution and original link must be shown on every item page
- Respect article-level license; if derivatives are disallowed, publish title+abstract only

## Status

Initial repo scaffold with PRD. Code to follow.
