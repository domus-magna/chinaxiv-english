# ChinaXiv Fresh Papers Scraper - Production Plan

## Overview
Scrape missing papers from ChinaXiv (April-October 2025) to fill the 7-month gap in our Internet Archive data.

## Current Status
✅ **Infrastructure Complete**
- BrightData Web Unlocker configured (`china_paper_scraper1`)
- API key and zone configured in `.env`
- Individual paper pages accessible and tested
- HTML structure analyzed

✅ **Gap Identified**
- Internet Archive data: Complete through March 2025 (202503)
- ChinaXiv live site: Has papers through October 2025 (202510)
- **Missing gap**: April-October 2025 (~1,000-1,500 papers)

## Paper ID Format

**Pattern**: `YYYYMM.NNNNN`
- Year-Month (6 digits) + Sequential Number (5 digits)
- Example: `202504.00123` = April 2025, paper #123

**URL**: `https://chinaxiv.org/abs/{YYYYMM.NNNNN}`

## Strategy: Sequential ID Probing

Since browse pages return errors but individual paper pages work:

1. **For each target month** (202504-202510):
   - Start at ID `YYYYMM.00001`
   - Increment sequentially: `YYYYMM.00002`, `YYYYMM.00003`, ...
   - Stop after 50 consecutive 404s (assume month complete)

2. **For each ID**:
   - Use BrightData Web Unlocker to GET page
   - If 404/error → skip to next ID
   - If 200 → parse HTML and extract metadata
   - Save to checkpoint file

3. **Output**: IA-compatible JSON files per month
   - `data/records/chinaxiv_202504.json`
   - `data/records/chinaxiv_202505.json`
   - ... etc

## HTML Parsing Details

Based on analysis of `https://chinaxiv.org/abs/202503.00296`:

### CSS Selectors

| Field | Location | Extraction Method |
|-------|----------|-------------------|
| **Title** | `<h1>` tag | `.find('h1').get_text(strip=True)` |
| **Authors** | Links with `field=author` | `.find_all('a', href=lambda x: 'field=author' in x)` |
| **Abstract** | After `<b>摘要: </b>` | Text following this marker |
| **Submit Date** | After `<b>提交时间：</b>` | Text following marker, parse datetime |
| **Category** | After `<b>分类：</b>` | Links in this section |
| **PDF URL** | Link with `filetype=pdf` | `.find('a', href=lambda x: 'filetype=pdf' in x)` |
| **DOI** | Link with `dx.doi.org` | Extract from href |

### Output JSON Schema

```json
{
  "id": "chinaxiv-202504.00123",
  "oai_identifier": "202504.00123",
  "title": "Paper title in Chinese/English",
  "abstract": "Full abstract text...",
  "creators": ["Author 1", "Author 2", "Author 3"],
  "subjects": ["Category 1", "Category 2"],
  "date": "2025-04-15T10:30:00Z",
  "source_url": "https://chinaxiv.org/abs/202504.00123",
  "pdf_url": "https://chinaxiv.org/user/download.htm?uuid=...&filetype=pdf",
  "license": {
    "raw": "",
    "derivatives_allowed": null
  },
  "setSpec": null
}
```

## Implementation

### File: `src/harvest_chinaxiv.py`

**CLI Interface**:
```bash
# Scrape specific month range
python -m src.harvest_chinaxiv --start 202504 --end 202510

# Scrape single month
python -m src.harvest_chinaxiv --month 202510

# Resume from checkpoint
python -m src.harvest_chinaxiv --resume

# Dry run (test parsing without saving)
python -m src.harvest_chinaxiv --month 202510 --dry-run
```

**Features**:
- ✅ BrightData Web Unlocker integration
- ✅ BeautifulSoup HTML parsing
- ✅ Checkpoint/resume capability
- ✅ Early stopping (50 consecutive 404s)
- ✅ Rate limiting (1-2 req/sec to avoid hammering)
- ✅ Progress logging
- ✅ Error handling and retry logic
- ✅ IA-compatible JSON output

### File: `docs/CHINAXIV_SCRAPER_PLAN.md`

This document (production plan and reference).

## Cost Estimation

### Based on IA Data Analysis

| Month | Est. Papers | Probe Requests | Total Requests |
|-------|-------------|----------------|----------------|
| 202504 (Apr) | 400 | ~600 | ~1,000 |
| 202505 (May) | 300 | ~450 | ~750 |
| 202506 (Jun) | 100 | ~200 | ~300 |
| 202507 (Jul) | 50 | ~100 | ~150 |
| 202508 (Aug) | 100 | ~200 | ~300 |
| 202509 (Sep) | 50 | ~100 | ~150 |
| 202510 (Oct) | 200 | ~300 | ~500 |
| **Total** | **~1,200** | **~1,950** | **~3,150** |

### BrightData Pricing

- Web Unlocker: ~$0.01-0.03 per successful request
- 3,150 requests × $0.02 avg = **~$63 estimated cost**
- Much cheaper than full site crawl (which would be $300-1,500)

## Execution Plan

### Phase 1: Build & Test
1. ✅ Write plan document
2. ⏳ Create `src/harvest_chinaxiv.py`
3. ⏳ Test with single paper (202510.00001)
4. ⏳ Test with October 2025 (current month, ~200 papers)

### Phase 2: Production Run
5. ⏳ Run full harvest (April-October 2025)
6. ⏳ Verify JSON output format
7. ⏳ Feed into batch translation pipeline

### Phase 3: Integration
8. ⏳ Add harvested papers to translation queue
9. ⏳ Monitor translation progress
10. ⏳ Rebuild site with new papers

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ChinaXiv blocks/rate-limits | BrightData handles anti-bot, use rate limiting (1-2 req/sec) |
| HTML structure varies | Defensive parsing, log parse failures |
| Missing metadata fields | Mark as null, continue processing |
| BrightData costs spiral | Set max request limit, checkpoint frequently |
| Network failures | Retry logic with exponential backoff |
| Incomplete months | Early stopping after 50 consecutive 404s |

## Success Metrics

- [ ] Scrape ≥80% of papers from each target month
- [ ] All papers have title + abstract (minimum required fields)
- [ ] JSON format 100% compatible with existing pipeline
- [ ] Total BrightData cost ≤ $100
- [ ] Papers successfully feed into batch translation
- [ ] Zero data loss (checkpoint/resume works correctly)

## Next Steps After Harvest

1. **Merge with existing IA data**:
   ```bash
   # Combine all records
   python -m src.merge_records \
     data/records/ia_all_*.json \
     data/records/chinaxiv_*.json \
     --output data/records/combined_all.json
   ```

2. **Initialize translation queue**:
   ```bash
   python -m src.batch_translate init \
     --use-harvested \
     --records data/records/chinaxiv_*.json
   ```

3. **Monitor and iterate**:
   - Check for parse failures
   - Verify translation quality
   - Update scraper if HTML structure changes

## Files Created

- `src/harvest_chinaxiv.py` (~300 lines) - Main scraper
- `docs/CHINAXIV_SCRAPER_PLAN.md` (this file) - Production plan
- `data/records/chinaxiv_YYYYMM.json` - Output per month
- `data/checkpoints/chinaxiv_YYYYMM.json` - Resume checkpoints

## Maintenance Notes

- **HTML structure changes**: ChinaXiv may update their site design
  - Solution: Review parse failures, update CSS selectors

- **New months**: Need to scrape monthly for ongoing updates
  - Solution: Run with `--month YYYYMM` in cron job

- **BrightData zone**: May need renewal or reconfiguration
  - Check: https://brightdata.com/cp/zones

## References

- Internet Archive ChinaXiv mirror: https://archive.org/details/chinaxivmirror
- ChinaXiv live site: https://chinaxiv.org
- BrightData Web Unlocker docs: https://docs.brightdata.com/scraping-automation/web-unlocker/introduction
