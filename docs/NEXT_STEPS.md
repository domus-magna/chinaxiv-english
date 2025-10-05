# ChinaXiv English - Next Steps

**Session Date**: 2025-10-05
**Last Updated**: 06:57 UTC
**Status**: Two background pipelines running

⚠️ **Remove this file from CLAUDE.md when all tasks completed**

---

## Current Status

### 🚀 Pipeline 1: Batch Translation (In Progress)
- **Progress**: 2,186 / 3,411 papers (64.1%)
- **Status**: 10 workers running
- **Est. Completion**: ~8 hours (505 min remaining)
- **Source**: Internet Archive data (Jan-March 2025)
- **Monitor**: `python3.11 -m src.batch_translate status`

### 🔍 Pipeline 2: ChinaXiv Harvest (In Progress)
- **Progress**: Scraping April 2025 (#135+ so far)
- **Target**: April-October 2025 (7 months)
- **Status**: Running (PID in data/harvest.pid)
- **Est. Papers**: ~1,200-1,500 new papers
- **Monitor**: `python3.11 -m src.harvest_monitor status`
- **Logs**: `tail -f data/harvest.log`

---

## Immediate Next Steps (Auto-Execute When Ready)

### 1. ✅ Let Pipelines Complete
**Action**: Monitor progress, no intervention needed
**ETA**:
- Translation: ~8 hours
- Harvest: ~2-4 hours

**Check Status**:
```bash
# Quick check both
python3.11 -m src.batch_translate status
python3.11 -m src.harvest_monitor status
```

### 2. ⏳ Merge Harvested Papers with IA Data
**When**: After harvest completes (all 7 months done)

**Script**: Create `scripts/merge_records.py`
```bash
python3.11 -m scripts.merge_records \
  --ia data/records/ia_all_20251004_215726.json \
  --chinaxiv data/records/chinaxiv_*.json \
  --output data/records/combined_all.json
```

**Expected Output**:
- ~3,411 IA papers (Jan-March 2025)
- ~1,200-1,500 ChinaXiv papers (April-Oct 2025)
- **Total**: ~4,600-4,900 papers

### 3. ⏳ Feed New Papers into Translation Queue
**When**: After merge completes

```bash
# Reset queue
rm -f data/jobs.db

# Initialize with ALL papers (merged)
python3.11 -m src.batch_translate init \
  --years 2024,2025 \
  --use-harvested

# Start workers
python3.11 -m src.batch_translate start --workers 10
```

**Expected**:
- Will translate ~1,200-1,500 NEW papers from ChinaXiv harvest
- Old IA papers already translated (can skip)

### 4. ⏳ Rebuild Site
**When**: After all translations complete

```bash
# Rebuild HTML pages
python3.11 -m src.render

# Rebuild search index
python3.11 -m src.search_index

# Deploy to Cloudflare Pages
# (manual step or CI trigger)
```

---

## Files & Artifacts

### Created This Session
- `src/harvest_chinaxiv_smart.py` - Optimized ChinaXiv scraper
- `src/harvest_monitor.py` - Harvest progress monitor
- `scripts/run_harvest_background.sh` - Background harvest launcher
- `docs/CHINAXIV_SCRAPER_PLAN.md` - Scraper design doc
- `docs/BATCH_TRANSLATION_PLAN.md` - Translation pipeline doc

### Active Data Files
- `data/harvest.log` - Live harvest logs
- `data/harvest.pid` - Harvest process PID
- `data/jobs.db` - Translation queue database
- `data/records/chinaxiv_YYYYMM.json` - Harvested papers per month
- `data/translated/*.json` - Translated papers

### Monitoring Commands
```bash
# Translation status
python3.11 -m src.batch_translate status
python3.11 -m src.batch_translate watch      # Live updates

# Harvest status
python3.11 -m src.harvest_monitor status
python3.11 -m src.harvest_monitor watch      # Live updates
tail -f data/harvest.log                     # Stream logs

# Check workers
ps aux | grep python | grep -E "worker|harvest"
```

---

## Cost Tracking

### Estimated Costs (2025-10-05)

**Batch Translation** (IA Papers):
- 3,411 papers × $0.001/paper ≈ **$3.41**
- Status: 64% complete → ~$2.18 spent so far

**ChinaXiv Harvest** (BrightData):
- ~1,500 papers × ~$0.05/paper ≈ **$75**
- Status: April in progress → ~$25-30 spent so far

**Future Translation** (New ChinaXiv Papers):
- ~1,500 papers × $0.001/paper ≈ **$1.50**

**Total Estimated**: ~$80

---

## Success Criteria

- [ ] All 3,411 IA papers translated (>99% success rate)
- [ ] All 7 months harvested from ChinaXiv (April-Oct 2025)
- [ ] ≥1,200 new papers discovered
- [ ] Merged dataset created
- [ ] All new papers translated
- [ ] Site rebuilt with ~4,600+ papers
- [ ] Total cost <$100
- [ ] Zero data loss

---

## Troubleshooting

### If Translation Stops
```bash
# Check failed jobs
python3.11 -m src.batch_translate failed

# Resume stuck jobs
python3.11 -m src.batch_translate resume
```

### If Harvest Stops
```bash
# Check if process died
cat data/harvest.pid
ps -p <PID>

# Restart harvest
scripts/run_harvest_background.sh
```

### If Session Compacts
This document has **everything you need** to:
1. Check current progress (monitoring commands above)
2. Continue from where we left off (next steps section)
3. Understand the full pipeline (status section)

---

## Context for Future Sessions

**What We Built**:
1. **Smart Scraper**: Uses BrightData to bypass ChinaXiv's browse page errors
   - Intelligently probes known ID ranges (not full 00001-99999)
   - 10x more cost-effective than naive sequential probing

2. **Background Processing**: Both pipelines run independently
   - Translation: SQLite queue + worker processes
   - Harvest: Single background process with monitoring

3. **Monitoring Tools**: Real-time progress tracking
   - `batch_translate status/watch` - Translation progress
   - `harvest_monitor status/watch` - Harvest progress

**Key Decisions**:
- Internet Archive for bulk data (Jan-March 2025)
- BrightData Web Unlocker for fresh papers (April-Oct 2025)
- Sequential ID probing with smart max ID discovery
- Background workers to keep Claude session free

**Data Flow**:
```
Internet Archive → IA Papers (3,411) → Translation ✅
      ↓
ChinaXiv Direct → New Papers (1,500) → Translation ⏳
      ↓
Both Combined → Merged Dataset → Site Rebuild
```

---

**Remove from CLAUDE.md when**: All pipelines complete, site rebuilt, and deployed
