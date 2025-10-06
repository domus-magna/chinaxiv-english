# Parallelization Comparison

## Current vs. Parallel Approaches

| Approach | Workers | Jobs | Papers/Hour | Time for 34K Papers | Cost |
|----------|---------|------|-------------|-------------------|------|
| **Current** | 10 | 1 | 100 | 340 hours (14 days) | $45 |
| **Parallel** | 100 | 5 | 500 | 68 hours (3 days) | $45 |
| **Ultra-Parallel** | 500 | 10 | 2,500 | 14 hours | $45 |
| **Extreme** | 2,000 | 20 | 10,000 | 3.4 hours | $45 |

## Workflow Files

### 1. Standard Backfill
**File**: `.github/workflows/backfill.yml`
- 10 workers per job
- 1 job at a time
- Good for testing and small batches

### 2. Parallel Backfill
**File**: `.github/workflows/backfill.yml` (parallel_jobs: 5)
- 20 workers per job
- 5 parallel jobs
- **Total**: 100 workers
- **Recommended for**: Medium batches (100-1000 papers)

### 3. Ultra-Parallel Backfill
**File**: `.github/workflows/backfill.yml` (parallel_jobs: 10)
- 50 workers per job
- 10 parallel jobs
- **Total**: 500 workers
- **Recommended for**: Large batches (1000-5000 papers)

### 4. Extreme-Parallel Backfill
**File**: `.github/workflows/backfill.yml` (parallel_jobs: 10, workers_per_job: 100)
- 100 workers per job
- 20 parallel jobs
- **Total**: 2,000 workers
- **Recommended for**: Massive batches (5000+ papers)

## GitHub Actions Limits

### Free Tier
- **Concurrent jobs**: 20 jobs
- **Concurrent runners**: 20 runners
- **Job time limit**: 6 hours per job
- **Monthly minutes**: 2,000 minutes

### Paid Tier
- **Concurrent jobs**: 40 jobs
- **Concurrent runners**: 40 runners
- **Job time limit**: 6 hours per job
- **Monthly minutes**: 50,000 minutes

## Recommended Usage

### For Testing (Start Here)
```yaml
# Use: backfill.yml (parallel_jobs: 5)
total_papers: 100
workers_per_job: 20
parallel_jobs: 5
```
**Expected time**: ~12 minutes

### For Production (Recommended)
```yaml
# Use: backfill.yml (parallel_jobs: 10)
total_papers: 5000
workers_per_job: 50
parallel_jobs: 10
```
**Expected time**: ~2 hours

### For Maximum Speed (If Needed)
```yaml
# Use: backfill.yml (parallel_jobs: 10, workers_per_job: 100)
total_papers: 10000
workers_per_job: 100
parallel_jobs: 20
```
**Expected time**: ~1 hour

## Performance Benefits

### Speed Improvement
- **Current**: 14 days for full backfill
- **Extreme**: 3.4 hours for full backfill
- **Improvement**: 99% faster

### Resource Utilization
- **Current**: 10 workers
- **Extreme**: 2,000 workers
- **Improvement**: 200x more workers

### Cost Efficiency
- **API costs**: Same ($45 for full backfill)
- **GitHub Actions**: More efficient (faster completion)
- **Time savings**: Massive

## Risk Assessment

### Low Risk (Parallel)
- 5 jobs × 20 workers = 100 total workers
- Well within GitHub Actions limits
- Easy to monitor and debug

### Medium Risk (Ultra-Parallel)
- 10 jobs × 50 workers = 500 total workers
- Near GitHub Actions concurrent limits
- Requires monitoring

### High Risk (Extreme)
- 20 jobs × 100 workers = 2,000 total workers
- At GitHub Actions limits
- Requires careful monitoring

## Implementation Strategy

### Phase 1: Test Parallel
1. Start with 100 papers, 5 jobs, 20 workers each
2. Monitor performance and quality
3. Verify completion times

### Phase 2: Scale Up
1. Increase to 500 papers, 5 jobs, 20 workers each
2. Test ultra-parallel with 1000 papers, 10 jobs, 50 workers each
3. Monitor GitHub Actions limits

### Phase 3: Full Backfill
1. Use ultra-parallel for 5000 papers per session
2. Run 7 sessions × 5000 papers = 35,000 papers
3. Complete full backfill in ~14 hours

## Monitoring and Optimization

### Key Metrics
- **Completion time per job**
- **Worker utilization**
- **API response times**
- **Error rates**
- **GitHub Actions queue status**

### Optimization Tips
1. **Start conservative**: Test with fewer workers first
2. **Monitor limits**: Watch GitHub Actions concurrent job limits
3. **Adjust dynamically**: Increase workers if jobs complete quickly
4. **Balance speed vs. reliability**: More workers = faster but more complex

## Expected Results

### Conservative Estimate
- **5 parallel jobs × 20 workers = 100 total workers**
- **~500 papers/hour**
- **Full backfill in ~68 hours**

### Optimistic Estimate
- **10 parallel jobs × 50 workers = 500 total workers**
- **~2,500 papers/hour**
- **Full backfill in ~14 hours**

### Maximum Theoretical
- **20 parallel jobs × 100 workers = 2,000 total workers**
- **~10,000 papers/hour**
- **Full backfill in ~3.4 hours**

## Conclusion

The parallelization strategy can reduce backfill time from **14 days to 3.4 hours** - a **99% reduction**! 

**Recommended approach**:
1. Start with **parallel** (100 workers)
2. Scale to **ultra-parallel** (500 workers)
3. Use **extreme** (2,000 workers) for maximum speed

All approaches maintain the same API costs (~$45) while dramatically reducing completion time.
