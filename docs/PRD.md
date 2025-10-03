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
- Attribution: Prominent “Source: ChinaXiv” with link on every page.
- Respect article-level licenses:
  - If derivatives allowed → publish translated full text
  - If derivatives forbidden/unclear → publish translated title+abstract only, link to original PDF
- Show license badge and “Machine translation. Verify with original.” banner on item pages.

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
   - Identify endpoint liveness check on start
   - ListRecords for previous UTC day; handle `resumptionToken` paging
   - Store raw XML for traceability (size-capped, rolling retention)
   - Normalize to JSON with fields: `id`, `oai_identifier`, `title`, `creators`, `subjects`, `abstract`, `date`, `pdf_url`, `source_url`, `license`, `setSpec` (if any)

2) License Gate
   - Parse license terms from metadata; if missing, scrape landing page tag/notice
   - Decision: `derivatives_allowed: true|false|unknown`
   - Enforce attribution and license display on all pages

3) Fetch
   - Download original PDF for every item (for user download + fallback reference)
   - If LaTeX source tarball exists, download and note `has_latex_source`

4) Translation
   - Mask LaTeX/math before translation; unmask after
   - Translate title, abstract, and full text (if permitted)
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
   - GitHub Actions nightly (03:00 UTC): harvest → license gate → fetch → translate → render → index → deploy to Pages
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
    harvest_oai.py         # pull yesterday’s records (OAI-PMH)
    licenses.py            # parse license; decide derivative permission
    select_and_fetch.py    # seen cache, fetch PDF and optional LaTeX
    tex_guard.py           # mask/unmask math and LaTeX
    translate.py           # OpenRouter adapter (DeepSeek default; Z.AI optional)
    render.py              # Jinja2 → HTML + Markdown
    make_pdf.py            # Tectonic (LaTeX) or Pandoc (MD) to PDF
    search_index.py        # build search-index.json
    utils.py               # shared helpers (http, xml, tokens)
    config.yaml            # model slugs, prompts, OAI params, license mappings
  data/
    seen.json              # processed IDs cache
    raw_xml/               # saved OAI responses (truncate/rotate by policy)
  assets/                  # CSS, logo, MathJax, MiniSearch/Lunr
  site/                    # generated static site (deploy target)
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

OAI-PMH harvesting
- Start: `Identify` for availability; log repositoryName/earliestDatestamp/granularity
- Harvest: `ListRecords&metadataPrefix=oai_eprint&from=YYYY-MM-DD&until=YYYY-MM-DD`
- Paging: follow `resumptionToken` until exhausted
- Fallback: if `oai_eprint` missing fields, attempt `oai_dc`
- Storage: write raw XML (per page) to `data/raw_xml/YYYY-MM-DD/part_N.xml`
- Normalization: extract identifiers, titles, creators, subjects, abstracts, dates, and links

License parsing and policy
- Prefer explicit license fields in metadata; else inspect landing page (meta/link/notice)
- Map common licenses to `derivatives_allowed` via `config.yaml` (e.g., CC-BY → true; CC-BY-ND → false)
- If unknown: treat as non-derivative → title/abstract only

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

### Non‑Functional Requirements
- Deterministic idempotency for re-runs (skip seen IDs)
- Time-bounded operation (target < 30 minutes; per-paper < 90s at P50)
- Site build reproducibility (pinned dependency versions)
- Accessibility: keyboard navigation, sufficient contrast, readable math sizing

### Risks & Mitigations
- Endpoint instability → Retry with backoff; resume via `resumptionToken`
- License ambiguity → Default to abstract-only; add review flag
- Model inconsistency on math-heavy paragraphs → stricter masking and glossary; optional Z.AI route
- Cost drift → token logging and pricing configuration; alert if daily estimate exceeds threshold
- Large PDFs or missing LaTeX → fall back to Markdown → Pandoc

### Milestones
1. Harvest + normalize + seen cache (1 day)
2. License gate + fetch PDFs (1 day)
3. Mask/translate/unmask (2–3 days)
4. Render + PDF + search index (1–2 days)
5. CI/CD + Pages deploy + smoke tests (1 day)

### Acceptance Criteria
- Nightly job publishes yesterday’s eligible records with correct license treatment
- Math placeholder parity = 100%; random spot check of 20 paragraphs OK
- Pages site loads and search returns results instantly on a sample of ≥100 items
- Download links for original PDF, translated Markdown, and PDF work
- Attribution and license visible on all item pages

### Configuration
- `config.yaml`:
  - `oai.base_url`, `sets`, `date_window`
  - `models.default_slug`, `models.alternates`
  - `glossary`
  - `license_mappings`
- Secrets: `OPENROUTER_API_KEY` (GitHub repo secret)

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


