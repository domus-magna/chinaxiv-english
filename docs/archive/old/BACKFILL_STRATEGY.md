# Backfill Translation Strategy

## Current Situation

- **Total papers available**: 34,237 papers
- **Current daily processing**: 5 papers/day
- **Time to complete at current rate**: ~18.7 years 😅

## Backfill Options

### Option 1: Manual Backfill Workflow (Recommended)

**New workflow**: `.github/workflows/backfill.yml`

**Features**:
- Manual trigger with configurable limits
- Uses existing batch translation system
- 10 workers for parallel processing
- Progress monitoring and Discord notifications
- 1-hour timeout to avoid GitHub Actions limits

**Usage**:
1. Go to GitHub Actions → "backfill-translations"
2. Click "Run workflow"
3. Set limit (e.g., 100, 500, 1000)
4. Monitor progress in logs

### Option 2: Incremental Daily Backfill

**Modify daily workflow** to process more papers:

```yaml
# In .github/workflows/build.yml
python -m src.harvest_ia --limit 50 || true  # Increase from 10
python -m src.select_and_fetch --records "$latest" --limit 25 --output data/selected.json || true  # Increase from 5
python -m src.pipeline --limit 25 || true  # Increase from 5
```

**Pros**: Automatic, gradual backfill
**Cons**: Still slow (25/day = 3.7 years for full backfill)

### Option 3: Batch Backfill Sessions

**Run multiple backfill workflows** in sequence:

1. **Session 1**: Process 1,000 papers
2. **Session 2**: Process 1,000 papers  
3. **Session 3**: Process 1,000 papers
4. Continue until complete

**Time estimate**: ~34 sessions × 1 hour each = 34 hours total

## Recommended Approach

### Phase 1: Quick Start (1-2 hours)
1. Run backfill workflow with limit 500
2. Process 500 papers to get initial content
3. Verify site works with translated content

### Phase 2: Gradual Backfill (1-2 weeks)
1. Run backfill workflow daily with limit 100-200
2. Monitor progress and costs
3. Adjust limits based on API costs

### Phase 3: Full Backfill (1-2 months)
1. Increase to 500-1000 papers per session
2. Run 2-3 sessions per week
3. Complete full backfill

## Cost Considerations

### OpenRouter API Costs
- **DeepSeek V3.2-Exp**: ~$0.27/M input, ~$0.40/M output
- **Average paper**: ~2,000 tokens input, ~1,500 tokens output
- **Cost per paper**: ~$0.0013
- **Full backfill (34,237 papers)**: ~$45

### GitHub Actions Limits
- **Free tier**: 2,000 minutes/month
- **Backfill workflow**: ~60 minutes per 100 papers
- **Monthly limit**: ~3,333 papers (well within needs)

## Implementation Steps

### 1. Test Backfill Workflow
```bash
# Test locally first
python -m src.batch_translate init --years 2024,2025 --limit 10 --use-harvested=true
python -m src.batch_translate start --workers 3
python -m src.batch_translate status
python -m src.batch_translate stop
```

### 2. Run First Backfill
1. Go to GitHub Actions
2. Run "backfill-translations" workflow
3. Set limit to 100
4. Monitor progress

### 3. Scale Up Gradually
- Start with 100 papers
- Increase to 500 papers
- Then 1000+ papers per session

## Monitoring Progress

### GitHub Actions Logs
- Real-time progress updates
- Completion statistics
- Error handling

### Discord Notifications
- Session start/end
- Completion counts
- Error alerts

### Site Updates
- New translated papers appear automatically
- Search index updates
- Donation page works

## Risk Mitigation

### API Rate Limits
- OpenRouter has generous limits
- Batch processing spreads load
- Workers handle retries automatically

### GitHub Actions Timeouts
- 1-hour timeout per session
- Multiple sessions for large backfills
- Progress saved between sessions

### Cost Control
- Monitor API usage
- Set daily/monthly limits
- Use dry-run for testing

## Expected Timeline

### Conservative (100 papers/day)
- **Daily backfill**: 100 papers
- **Time to complete**: ~342 days
- **Cost**: ~$0.13/day

### Aggressive (1000 papers/day)
- **Daily backfill**: 1000 papers  
- **Time to complete**: ~34 days
- **Cost**: ~$1.30/day

### Recommended (500 papers/day)
- **Daily backfill**: 500 papers
- **Time to complete**: ~68 days
- **Cost**: ~$0.65/day

## Next Steps

1. **Test backfill workflow** with small limit (10-50 papers)
2. **Run first backfill session** (100-500 papers)
3. **Monitor costs and progress**
4. **Scale up gradually** based on results
5. **Complete full backfill** over 1-2 months

The backfill system is ready to run in the cloud! 🚀
