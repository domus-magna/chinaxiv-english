## ChinaXiv → English Translation Static Site (V1) — PRD

### Summary
Translate ChinaXiv preprints to English with high math/LaTeX fidelity and publish as a static site. Integrate once via OpenRouter (default: DeepSeek; optional: Z.AI GLM) to keep costs and complexity low. Harvest via OAI-PMH within license constraints, render HTML with MathJax, and offer Markdown/PDF downloads. A nightly job ingests new records, translates, renders, indexes, and deploys.

### Goals
- High-fidelity English translations of ChinaXiv preprints with exact math preservation
- Single integration via OpenRouter; easily swap model slugs
- Static site: view pages, client-side search, Markdown/PDF downloads
- Simple, cheap, low-ops pipeline (nightly cron)

### Non‑Goals (V1)
- No user accounts, comments, or server-side search
- No multi-source ingestion beyond ChinaXiv
- No human-in-the-loop editing UI

### Users & Use Cases
- Researchers scanning ChinaXiv work in English
- Practitioners seeking fast access to abstracts and math-heavy content
- Librarians/curators wanting compliant, attributed mirrors of metadata and translations

### Legal & Compliance
- Use OAI-PMH endpoints published by ChinaXiv. See ChinaXiv help and OAI references.
  - Identify/ListRecords with `metadataPrefix=oai_eprint` (fallback `oai_dc`)
  - Selective harvest by date using `from`/`until` (UTC)
- Attribution: Prominent "Source: ChinaXiv" with link on every page.
- **LICENSE POLICY: We do not care about licenses.** All papers will be translated in full regardless of license restrictions. License-related code has been commented out.
- Show "Machine translation. Verify with original." banner on item pages.

References:
- ChinaXiv help and OAI endpoint examples: `https://astro.chinaxiv.org` / `http://www.chinaxiv.org`
- OAI-PMH spec: `https://www.openarchives.org/OAI/openarchivesprotocol.html`

### Success Metrics (V1)
- Freshness: ≥95% of yesterday’s eligible records published by 06:00 UTC
- Fidelity: 100% math placeholder count parity pre/post translation
- Cost: ≤$1/day at median volume (tracked via token logs)
- Reliability: Nightly job success rate ≥ 0.95 over 30 days
- UX: Search results render <100ms after keystroke on a modern laptop (client-side index ≤5 MB)

### Scope (Functional Requirements)
1) Harvest
   - ChinaXiv scraping via BrightData (Web Unlocker)
   - Safe rate limits and checkpointing; resume capability
   - Store harvested JSON for traceability (size-capped, rolling retention)
   - Normalize to JSON with fields: `id`, `oai_identifier`, `title`, `creators`, `subjects`, `abstract`, `date`, `pdf_url`, `source_url`, `license`, `setSpec` (if any)

2) License Gate
   - **DISABLED: We do not care about licenses.** All papers translated in full.
   - License-related code commented out in the codebase.

3) Fetch
   - Download original PDF for every item (for user download + fallback reference)
   - If LaTeX source tarball exists, download and note `has_latex_source`

4) Translation
   - Mask LaTeX/math before translation; unmask after
   - Translate title, abstract, and full text (all papers translated in full)
   - Chunk by section/paragraph under token budget; maintain order
   - Glossary support for common ML terms (applied across model routes)

5) Rendering
   - Static HTML pages (arXiv-like layout) with MathJax
   - Markdown output for each item
   - PDF output via Tectonic (LaTeX) or Pandoc (Markdown)
   - Prominent attribution footer + license badge

6) Search (client-only)
   - `search-index.json` with `id`, `title`, `authors`, `abstract`, `subjects`, `date`
   - MiniSearch/Lunr loaded as single JS file; instant results

7) Automation & Deploy
   - GitHub Actions nightly (03:00 UTC): harvest → license gate → fetch → translate → render → index → deploy to Cloudflare Pages
   - Idempotent via `seen.json` cache; only process new IDs
   - Log per-item model slug and token counts for cost tracking

### Out of Scope (for V1)
- Multi-model majority vote, human QA workflows, translation memory database
- Backfilling large historical windows (beyond small smoke tests)
- Non-ChinaXiv sources

### Technical Design

Repository layout
```
repo/
  src/
    # harvesting handled externally; IA removed
    licenses.py            # parse license; decide derivative permission
    select_and_fetch.py    # seen cache, fetch PDF from IA
    tex_guard.py           # mask/unmask math and LaTeX
    translate.py           # OpenRouter adapter (DeepSeek default; Z.AI optional)
    render.py              # Jinja2 → HTML + Markdown
    make_pdf.py            # Tectonic (LaTeX) or Pandoc (MD) to PDF
    search_index.py        # build search-index.json
    utils.py               # shared helpers (http, json, tokens)
    config.yaml            # model slugs, prompts, IA endpoints, license mappings
  data/
    seen.json              # processed IDs cache
    raw_json/              # optional raw responses (if custom harvester used)
  assets/                  # CSS, logo, MathJax, MiniSearch/Lunr
  site/                    # generated static site (deploy target)
  docs/
    archive/INTERNET_ARCHIVE_PLAN.md  # archived plan (not in use)
  .github/workflows/build.yml
```

Data model (normalized JSON per record)
```json
{
  "id": "<stable_local_id>",
  "oai_identifier": "oai:chinaxiv.org:...",
  "title": "...",
  "creators": ["Last, First", "..."] ,
  "abstract": "...",
  "subjects": ["cs.AI", "..."],
  "date": "YYYY-MM-DD",
  "pdf_url": "https://...",
  "source_url": "https://...", 
  "license": {
    "raw": "...",
    "derivatives_allowed": true
  },
  "setSpec": "optional"
}
```

Data Ingestion
- Internet Archive approach has been removed from scope.
- OAI-PMH remains blocked. For V1, ingestion is external/manual or via future custom harvesters.

License parsing and policy
- **DISABLED: We do not care about licenses.** All papers translated in full regardless of license restrictions.
- License-related code has been commented out in the codebase.

Math/LaTeX preservation
- Mask patterns before translation:
  - Inline: `$...$`, `\\(...\\)`
  - Display: `$$...$$`, `\\[...\\]`
  - Environments: `\\begin{equation}`, `align`, `gather`, etc.
- Replace with stable tokens `⟪MATH_0001⟫` … `⟪MATH_N⟫`
- After translation: verify token counts unchanged; unmask in order
- Also preserve citation/refs commands (e.g., `\\cite{}`, `\\ref{}`) as literals

Translation adapter (OpenRouter)
- Base URL: `https://openrouter.ai/api/v1`
- Models: default `deepseek/deepseek-v3.2-exp`; optional `z-ai/glm-4.5-air`
- API key via `OPENROUTER_API_KEY`
- System prompt fragment:
  - “Translate from Simplified Chinese to English. Preserve all LaTeX commands and ⟪MATH_*⟫ placeholders exactly. Do not rewrite formulas. Obey glossary strictly.”
- Chunking:
  - Titles/abstracts single-pass
  - Body by section/paragraph; target ≤1500 tokens per request
  - Reassemble; run post-pass for placeholder parity and section anchors
- Glossary:
  - Simple bilingual string or JSON list; prepend to each request

Batch translation (future option)
- Some providers expose asynchronous batch endpoints with longer SLAs (e.g., 12–24 hours) at materially lower cost (often ~50%).
- DeepSeek and Z.AI GLM do not currently advertise such endpoints on OpenRouter; re-evaluate periodically.
- Design implications if adopted later:
  - Submit segment batches (title/abstract/body paragraphs) with stable segment IDs; poll or receive callback.
  - Store batch job IDs and per-segment outputs under `data/batches/` to remain idempotent.
  - Nightly pipeline can run in two phases: submit on day N, collect + render on day N+1.
  - Cost estimator should support batch pricing tiers alongside on-demand.
  - Math token parity checks still apply when reassembling.

Rendering & assets
- Jinja2 templates for index and item pages; arXiv-like typography
- MathJax for equations
- Markdown and PDF buttons
- Footer includes “Source: ChinaXiv” link and license badge

Client-side search
- Generate `search-index.json` with minimal fields
- Load MiniSearch/Lunr as single minified script; debounce input; instant results

Automation (GitHub Actions)
- Cron at 03:00 UTC
- Steps: checkout → setup Python → install deps → run pipeline → upload `site/` to Pages
- Caching: pip cache; optional artifacts for `data/raw_xml` (short retention)
- Secrets: `OPENROUTER_API_KEY`

Observability & cost tracking
- Log per-item: model slug, input/output tokens, computed cost per model pricing table
- Daily summary report artifact (JSON) for costs and counts
 - Note: If batch endpoints become available with different pricing/SLAs, extend logging to tag `mode: batch|realtime` and adjust pricing tables accordingly.

### Non‑Functional Requirements
- Deterministic idempotency for re-runs (skip seen IDs)
- Time-bounded operation (target < 30 minutes; per-paper < 90s at P50)
- Site build reproducibility (pinned dependency versions)
- Accessibility: keyboard navigation, sufficient contrast, readable math sizing

### Risks & Mitigations
- Endpoint instability → Retry with backoff; resume via `resumptionToken`
- Model inconsistency on math-heavy paragraphs → stricter masking and glossary; optional Z.AI route
- Cost drift → token logging and pricing configuration; alert if daily estimate exceeds threshold
- Large PDFs or missing LaTeX → fall back to Markdown → Pandoc
- Proxy failures or geo-blocking → Bright Data residential proxies with China IPs; fallback to retry with exponential backoff; monitor proxy quota and costs

### Milestones
1. Harvest + normalize + seen cache (1 day)
2. Fetch PDFs (1 day)
3. Mask/translate/unmask (2–3 days)
4. Render + PDF + search index (1–2 days)
5. CI/CD + Pages deploy + smoke tests (1 day)

### Acceptance Criteria
- Nightly job publishes yesterday's eligible records (all translated in full)
- Math placeholder parity = 100%; random spot check of 20 paragraphs OK
- Pages site loads and search returns results instantly on a sample of ≥100 items
- Download links for original PDF, translated Markdown, and PDF work
- Attribution visible on all item pages

### Configuration
- `config.yaml`:
  - `internet_archive.collection`, `base_url`, `batch_size`
  - `models.default_slug`, `models.alternates`
  - `glossary`
  - `license_mappings` (commented out - we don't care about licenses)
- Secrets (GitHub repo secrets and `.env`):
  - `OPENROUTER_API_KEY` (required)
- Deprecated config (no longer needed with IA approach):
  - `oai.base_url` (ChinaXiv OAI-PMH blocked)
  - `proxy.*` settings
  - `BRIGHTDATA_API_KEY`

### Appendix
Pricing references (subject to change; verify on model pages):
- DeepSeek V3.2-Exp (OpenRouter): ~$0.27/M input, ~$0.40/M output
- Z.AI GLM‑4.5 Air (OpenRouter): ~$0.14/M input, ~$0.86/M output
- Z.AI Translation Agent (direct): ~$3/M tokens

Cost example (abstract: 1200 in, 800 out):
- DeepSeek via OpenRouter ≈ $0.000644
- Z.AI GLM‑4.5 Air ≈ $0.000856

Links
- OpenRouter: `https://openrouter.ai`
- DeepSeek API docs: `https://api-docs.deepseek.com`
- Z.AI docs: `https://docs.z.ai`
- OAI-PMH spec: `https://www.openarchives.org/OAI/openarchivesprotocol.html`
