# Internet Archive Migration Plan

## Summary
Pivot from blocked ChinaXiv OAI-PMH endpoint to Internet Archive's ChinaXiv mirror collection. This eliminates geo-blocking, bot detection, and proxy costs while providing access to 30,817+ papers with full metadata and PDFs.

## Why Internet Archive?

**ChinaXiv OAI-PMH Issues:**
- ❌ Returns "Sorry!You have no right to access this web"
- ❌ Hard-blocked at application level (not geo/bot detection)
- ❌ No working headers/cookies/user-agents found
- ❌ Likely requires institutional IP whitelisting
- ❌ Would need Bright Data proxies (~$25-50 upfront)

**Internet Archive Benefits:**
- ✅ 30,817+ ChinaXiv papers already mirrored
- ✅ Full metadata (title, authors, abstract, subjects, date, ChinaXiv ID)
- ✅ Full PDFs downloadable
- ✅ No authentication, no geo-blocking, no bot detection
- ✅ Simple JSON API with cursor pagination
- ✅ Zero proxy costs
- ✅ Generous rate limits

## API Overview

### Base URLs
- **Scraping API** (unlimited results): `https://archive.org/services/search/v1/scrape`
- **Metadata API**: `https://archive.org/metadata/{identifier}`
- **Download API**: `https://archive.org/download/{identifier}/{filename}`

### Available Fields
Per paper:
- `identifier` - Archive.org ID (e.g., "ChinaXiv-202211.00170V1")
- `chinaxiv` - Original ChinaXiv ID
- `title` - Paper title
- `creator` - Authors (array)
- `date` - Publication date
- `description` - Abstract
- `subject` - Keywords/disciplines (array)
- `external-identifier` - DOI, CSTR, URN (array)
- `files` - PDF and metadata files available for download

## Implementation Plan

### Phase 1: Harvest Module Replacement (Day 1)

**File: `src/harvest_ia.py` (new)**

Replace `src/harvest_oai.py` with Internet Archive harvester:

```python
def harvest_chinaxiv_metadata(
    cursor: Optional[str] = None,
    limit: int = 10000
) -> Tuple[List[Dict], Optional[str]]:
    """
    Harvest ChinaXiv metadata from Internet Archive.

    Returns:
        (records, next_cursor): List of normalized records and cursor for next page
    """
    url = "https://archive.org/services/search/v1/scrape"
    params = {
        'fields': 'identifier,chinaxiv,title,creator,subject,date,description',
        'q': 'collection:chinaxivmirror',
        'count': limit
    }
    if cursor:
        params['cursor'] = cursor

    response = http_get(url, params=params)
    data = response.json()

    records = [normalize_ia_record(item) for item in data.get('items', [])]
    next_cursor = data.get('cursor')

    return records, next_cursor
```

**Normalization mapping:**
```python
def normalize_ia_record(item: Dict) -> Dict:
    """
    Normalize Internet Archive item to our standard format.

    Maps:
        identifier -> id (with 'ia-' prefix)
        chinaxiv -> oai_identifier (original ChinaXiv ID)
        title -> title
        creator -> creators (ensure list)
        description -> abstract
        subject -> subjects (ensure list)
        date -> date
    """
    return {
        "id": f"ia-{item['identifier']}",
        "oai_identifier": item.get('chinaxiv', ''),
        "title": item.get('title', ''),
        "creators": ensure_list(item.get('creator')),
        "abstract": item.get('description', ''),
        "subjects": ensure_list(item.get('subject')),
        "date": item.get('date', ''),
        "source_url": f"https://archive.org/details/{item['identifier']}",
        "pdf_url": construct_pdf_url(item['identifier']),
        "license": infer_license(item)  # Default to unknown, check metadata
    }
```

**Key changes:**
- Remove OAI-PMH XML parsing (lxml dependency can stay for PDF extraction)
- Remove resumptionToken logic (replaced with cursor pagination)
- Add `construct_pdf_url()` helper to build Archive.org download links
- Store `identifier` as `ia-{archive_id}` to distinguish from future direct ChinaXiv IDs

### Phase 2: PDF Fetching (Day 1)

**File: `src/select_and_fetch.py` (modify)**

Update PDF download to use Internet Archive:

```python
def fetch_pdf_from_ia(identifier: str) -> Optional[str]:
    """
    Download PDF from Internet Archive.

    Args:
        identifier: Archive.org identifier (e.g., 'ChinaXiv-202211.00170V1')

    Returns:
        Path to downloaded PDF or None
    """
    # Get item metadata to find PDF filename
    metadata_url = f"https://archive.org/metadata/{identifier}"
    metadata = http_get(metadata_url).json()

    # Find PDF file (usually ends with .pdf)
    pdf_files = [f for f in metadata.get('files', []) if f['name'].endswith('.pdf')]

    if not pdf_files:
        log(f"No PDF found for {identifier}")
        return None

    pdf_file = pdf_files[0]['name']
    pdf_url = f"https://archive.org/download/{identifier}/{pdf_file}"

    # Download to data/pdfs/{identifier}.pdf
    output_path = os.path.join("data", "pdfs", f"{identifier}.pdf")
    ensure_dir(os.path.dirname(output_path))

    response = http_get(pdf_url)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path
```

**No changes needed:**
- License gate logic (still applies)
- Seen cache (still tracks by ID)
- PDF text extraction (same process)

### Phase 3: Update Configuration (Day 1)

**File: `src/config.yaml`**

Replace OAI config with Internet Archive:

```yaml
# Data source: Internet Archive ChinaXiv mirror
internet_archive:
  collection: "chinaxivmirror"
  base_url: "https://archive.org"
  scrape_endpoint: "/services/search/v1/scrape"
  metadata_endpoint: "/metadata"
  download_endpoint: "/download"
  batch_size: 10000  # Max items per API call

# Remove old OAI config (or comment out for reference)
# oai:
#   base_url: "https://chinaxiv.org/oai/OAIHandler"  # BLOCKED - do not use
#   ...
```

**File: `.env`**

Remove proxy settings (no longer needed):

```bash
# BRIGHTDATA_API_KEY - NOT NEEDED (no proxy required)
# SOCKS5_PROXY - NOT NEEDED
```

### Phase 4: CLI Updates (Day 1)

**File: `src/harvest_ia.py`**

Update CLI interface:

```python
def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest ChinaXiv metadata from Internet Archive."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Max records per batch (default: 10000)"
    )
    parser.add_argument(
        "--cursor",
        help="Resume from cursor (for pagination)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Harvest all records (paginate until exhausted)"
    )
    args = parser.parse_args()

    if args.all:
        harvest_all_records()
    else:
        records, next_cursor = harvest_chinaxiv_metadata(
            cursor=args.cursor,
            limit=args.limit
        )
        save_records(records)
        if next_cursor:
            log(f"More records available. Resume with: --cursor {next_cursor}")
```

**Usage:**
```bash
# Harvest first batch (10K records)
python -m src.harvest_ia

# Harvest all records
python -m src.harvest_ia --all

# Resume from cursor
python -m src.harvest_ia --cursor ABC123...
```

### Phase 5: Testing & Validation (Day 1)

**File: `tests/test_harvest_ia.py` (new)**

```python
import pytest
from src.harvest_ia import normalize_ia_record, harvest_chinaxiv_metadata

def test_normalize_ia_record():
    """Test Internet Archive record normalization"""
    item = {
        'identifier': 'ChinaXiv-202211.00170V1',
        'chinaxiv': '202211.00170',
        'title': 'Test Paper',
        'creator': ['Author One', 'Author Two'],
        'description': 'This is an abstract.',
        'subject': ['Physics', 'Quantum'],
        'date': '2022-11-15'
    }

    result = normalize_ia_record(item)

    assert result['id'] == 'ia-ChinaXiv-202211.00170V1'
    assert result['oai_identifier'] == '202211.00170'
    assert result['title'] == 'Test Paper'
    assert len(result['creators']) == 2
    assert result['abstract'] == 'This is an abstract.'

def test_harvest_metadata():
    """Test live API call (integration test)"""
    records, cursor = harvest_chinaxiv_metadata(limit=10)

    assert len(records) > 0
    assert len(records) <= 10
    assert all('id' in r for r in records)
    assert all('title' in r for r in records)
```

**Smoke test:**
```bash
# Test harvest of 10 records
python -m src.harvest_ia --limit 10

# Verify JSON output
cat data/selected/*.json | jq .
```

### Phase 6: Documentation Updates (Day 1)

**Files to update:**
- ✅ `CLAUDE.md` - Document IA as primary source
- ✅ `AGENTS.md` - Update data source info, remove proxy requirements
- ✅ `docs/PRD.md` - Replace OAI-PMH with IA API
- ✅ `README.md` - Update quick start with IA commands
- ✅ `docs/PROXY_SETUP.md` - Mark as deprecated/archive
- ✅ `docs/PROXY_REVIEW.md` - Mark as deprecated/archive

### Phase 7: CI/CD Updates (Day 1)

**File: `.github/workflows/build.yml`**

Update harvest step:

```yaml
- name: Harvest ChinaXiv Metadata
  run: |
    python -m src.harvest_ia --all
  # Remove BRIGHTDATA_API_KEY secret (no longer needed)
  # Remove proxy env vars
```

**Secrets to remove:**
- `BRIGHTDATA_API_KEY` (optional: keep for future use but not needed now)
- Any proxy URLs

## Migration Checklist

### Code Changes
- [ ] Create `src/harvest_ia.py` with Internet Archive harvester
- [ ] Add `normalize_ia_record()` function
- [ ] Add `construct_pdf_url()` helper
- [ ] Update `src/select_and_fetch.py` with `fetch_pdf_from_ia()`
- [ ] Update `src/config.yaml` with IA endpoints
- [ ] Remove/deprecate `src/harvest_oai.py` (keep for reference)
- [ ] Add `tests/test_harvest_ia.py`

### Documentation
- [ ] Update `CLAUDE.md`
- [ ] Update `AGENTS.md`
- [ ] Update `docs/PRD.md`
- [ ] Update `README.md`
- [ ] Archive `docs/PROXY_SETUP.md` and `docs/PROXY_REVIEW.md`
- [ ] Create this file: `docs/INTERNET_ARCHIVE_PLAN.md` ✅

### Configuration
- [ ] Update `.env` (remove proxy vars, keep OPENROUTER_API_KEY)
- [ ] Update `src/config.yaml` (add IA config, comment out OAI)
- [ ] Update `.github/workflows/build.yml` (remove proxy secrets)

### Testing
- [ ] Test `harvest_ia` with `--limit 10`
- [ ] Test `harvest_ia --all` (full harvest)
- [ ] Test PDF download from IA
- [ ] Test translation pipeline with IA data
- [ ] Test end-to-end build and deploy

## Timeline

**Day 1 (Today):**
- ✅ Research and planning (DONE)
- ⏳ Create `src/harvest_ia.py` (2 hours)
- ⏳ Update docs and config (1 hour)
- ⏳ Test with 10-100 records (30 min)

**Day 2 (Optional):**
- Full harvest of 30K+ records
- Translation pipeline smoke test
- CI/CD testing

## Benefits Summary

| Metric | Before (OAI-PMH) | After (Internet Archive) |
|--------|------------------|--------------------------|
| **Access** | ❌ Blocked | ✅ Open |
| **Records** | Unknown (~20K?) | ✅ 30,817+ confirmed |
| **Cost** | $25-50 (proxy) | ✅ $0 |
| **Complexity** | High (XML, auth) | ✅ Low (JSON API) |
| **Rate limits** | Unknown | ✅ Generous |
| **PDF access** | Separate download | ✅ Same API |
| **Maintenance** | Proxy monitoring | ✅ None |

## Risks & Mitigations

**Risk: Internet Archive collection may not be complete**
- Mitigation: Compare IA count (30,817) with ChinaXiv website stats
- Mitigation: Email ChinaXiv (eprint@mail.las.ac.cn) to confirm official data access later

**Risk: Internet Archive may lag behind new papers**
- Mitigation: Track upload dates, expect 1-7 day lag
- Mitigation: Consider hybrid approach (IA for historical, ChinaXiv API if/when available)

**Risk: License information may be incomplete in IA metadata**
- Mitigation: Use conservative defaults (abstract-only for unknown licenses)
- Mitigation: Fetch from ChinaXiv landing pages if needed (no auth required for HTML)

## Future Enhancements

1. **Real-time updates**: Monitor IA collection for new uploads
2. **Hybrid approach**: IA for bulk, ChinaXiv API (if unlocked) for recent papers
3. **Metadata enrichment**: Cross-reference with ChinaXiv landing pages for license verification
4. **Community contribution**: Share our findings with OAI-PMH community about ChinaXiv blocking

## Success Criteria

- ✅ Harvest 30,000+ papers from Internet Archive
- ✅ Maintain same data model (title, abstract, authors, etc.)
- ✅ Successfully translate at least 100 papers end-to-end
- ✅ Deploy static site with search
- ✅ Zero proxy costs
- ✅ Pipeline runs in under 30 minutes for daily incremental updates
