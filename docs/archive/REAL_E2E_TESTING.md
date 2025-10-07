# Real End-to-End Testing Guide

This guide explains how to run real end-to-end tests that use actual external APIs (Internet Archive, OpenRouter) to provide true production confidence.

## Overview

Our real E2E tests use a two-tier strategy:

- **Quality Tests**: 20 papers with DeepSeek V3.2-Exp (~$0.026)
- **Batch Tests**: 500+ papers with free models ($0.00)
- **Total Monthly Cost**: ~$0.026

## Prerequisites

### Required Environment Variables

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```

### Optional Environment Variables

```bash
export DISCORD_WEBHOOK_URL="your-discord-webhook-url"  # For notifications
```

## Test Categories

### 1. Quality Tests (`--category quality`)

**Purpose**: Validate translation quality with production model
**Cost**: ~$0.026 for 20 papers
**Models**: DeepSeek V3.2-Exp
**Duration**: ~5-10 minutes

```bash
python scripts/run_real_e2e_tests.py --category quality
```

**What it tests**:
- Real Internet Archive harvesting
- Translation quality with DeepSeek V3.2-Exp
- Math preservation and glossary usage
- Complex Chinese text handling

### 2. Batch Tests (`--category batch`)

**Purpose**: Validate scale and performance with free models
**Cost**: $0.00 for 500+ papers
**Models**: GLM-4.5-Air:free, deepseek-chat-v3.1:free
**Duration**: ~15-30 minutes

```bash
python scripts/run_real_e2e_tests.py --category batch
```

**What it tests**:
- Large-scale processing
- Performance metrics
- Error handling and resilience
- Rate limiting and backoff

### 3. Pipeline Tests (`--category pipeline`)

**Purpose**: Complete end-to-end workflow validation
**Cost**: ~$0.026 for 2 papers
**Models**: DeepSeek V3.2-Exp
**Duration**: ~3-5 minutes

```bash
python scripts/run_real_e2e_tests.py --category pipeline
```

**What it tests**:
- Harvest → Translate → Render → Search Index
- Complete workflow integration
- Site generation and content validation
- Search functionality

### 4. All Tests (`--category all`)

**Purpose**: Comprehensive validation
**Cost**: ~$0.026 total
**Duration**: ~20-45 minutes

```bash
python scripts/run_real_e2e_tests.py --category all
```

## Running Tests

### Local Development

```bash
# Check requirements
python scripts/run_real_e2e_tests.py --check-only

# Run specific category
python scripts/run_real_e2e_tests.py --category quality

# Run all tests
python scripts/run_real_e2e_tests.py --category all
```

### GitHub Actions

The tests can be triggered manually via GitHub Actions:

1. Go to **Actions** → **Real E2E Tests**
2. Click **Run workflow**
3. Select test category
4. Set papers limit (optional)
5. Click **Run workflow**

## Test Files

### Core Test Files

- `tests/test_e2e_real.py` - Main real E2E tests
- `tests/conftest_real.py` - Test configuration and fixtures
- `tests/test_monitoring_real.py` - Test monitoring and reporting
- `scripts/run_real_e2e_tests.py` - Test runner script

### Test Structure

```
tests/test_e2e_real.py
├── TestRealAPIIntegration
│   ├── test_real_internet_archive_harvest
│   ├── test_real_openrouter_translation_quality
│   ├── test_real_openrouter_translation_batch_free
│   ├── test_real_paper_translation
│   └── test_real_job_queue_integration
├── TestRealPipelineIntegration
│   └── test_real_end_to_end_pipeline
└── TestRealPerformanceAndScale
    ├── test_real_batch_processing_free_models
    └── test_real_error_handling
```

## Monitoring and Reporting

### Test Monitoring

The tests include comprehensive monitoring:

- **Cost Tracking**: Real-time API cost monitoring
- **Performance Metrics**: Papers/minute, response times, error rates
- **Test Results**: Detailed pass/fail status for each test
- **Reports**: JSON reports saved to `data/test_reports/`

### Example Report

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "summary": {
    "total_tests": 5,
    "successful_tests": 5,
    "failed_tests": 0,
    "total_duration": 180.5,
    "total_cost": 0.026
  },
  "cost_tracking": {
    "total_cost": 0.026,
    "papers_processed": 20,
    "api_calls": 20,
    "model_usage": {
      "deepseek/deepseek-v3.2-exp": {
        "calls": 20,
        "tokens": 40000,
        "cost": 0.026
      }
    }
  },
  "performance_metrics": {
    "papers_per_minute": 6.67,
    "average_response_time": 2.1,
    "error_rate": 0.0
  }
}
```

## Cost Management

### Cost Breakdown

- **DeepSeek V3.2-Exp**: $0.27/M input, $0.40/M output tokens
- **Average paper**: ~2,000 input tokens, ~1,500 output tokens
- **Cost per paper**: ~$0.0013
- **Quality tests**: 20 papers = $0.026
- **Batch tests**: 500+ papers with free models = $0.00
- **Total monthly cost**: ~$0.026

### Cost Alerts

The tests include cost monitoring and will alert if:
- Daily costs exceed $0.10
- Monthly costs exceed $1.00
- Unexpected high token usage detected

## Troubleshooting

### Common Issues

#### 1. API Key Not Set

```
❌ OPENROUTER_API_KEY environment variable not set
```

**Solution**: Set the environment variable:
```bash
export OPENROUTER_API_KEY="your-key-here"
```

#### 2. Network Connectivity Issues

```
⚠️ Internet connectivity check failed
```

**Solution**: Check your internet connection. Tests will still run but may fail if connectivity is required.

#### 3. Rate Limiting

```
❌ Rate limit exceeded
```

**Solution**: The tests include automatic delays between requests. If you hit rate limits, increase delays in the test configuration.

#### 4. Test Timeouts

```
❌ Test timeout after 30 minutes
```

**Solution**: Increase timeout in GitHub Actions workflow or run tests locally with longer timeouts.

### Debug Mode

Run tests with verbose output for debugging:

```bash
python -m pytest tests/test_e2e_real.py -v -s --tb=long
```

## Best Practices

### 1. Test Frequency

- **Quality tests**: Run weekly or before releases
- **Batch tests**: Run monthly or for performance validation
- **Pipeline tests**: Run before deployments
- **All tests**: Run for comprehensive validation

### 2. Cost Optimization

- Use free models for batch testing
- Limit paper count for quality tests
- Monitor costs regularly
- Set up cost alerts

### 3. Test Data Management

- Use real Internet Archive data
- Test with diverse paper types
- Validate math preservation
- Check glossary usage

### 4. Performance Monitoring

- Track papers per minute
- Monitor response times
- Watch error rates
- Optimize based on metrics

## Integration with CI/CD

### GitHub Actions Integration

The real E2E tests are integrated with GitHub Actions:

- **Manual triggers**: Run tests on demand
- **Artifact upload**: Test results and generated content
- **Discord notifications**: Success/failure alerts
- **Cost tracking**: Monitor API usage

### Pre-deployment Validation

Run real E2E tests before deployments:

```bash
# Validate translation quality
python scripts/run_real_e2e_tests.py --category quality

# Validate complete pipeline
python scripts/run_real_e2e_tests.py --category pipeline
```

## Future Enhancements

### Planned Features

1. **Automated Test Scheduling**: Daily/weekly test runs
2. **Performance Regression Detection**: Track performance over time
3. **Cost Optimization**: Automatic model selection based on cost
4. **Test Data Curation**: Maintain high-quality test datasets
5. **Real User Testing**: Browser automation for user experience

### Contributing

To contribute to real E2E tests:

1. Add new test cases to `tests/test_e2e_real.py`
2. Update test configuration in `tests/conftest_real.py`
3. Add monitoring in `tests/test_monitoring_real.py`
4. Update documentation in this file

## Conclusion

Real E2E tests provide true production confidence by using actual external dependencies. With minimal cost (~$0.026/month) and comprehensive coverage, these tests ensure our translation pipeline works correctly in production environments.

The two-tier strategy balances quality validation (with production models) and scale testing (with free models) to provide comprehensive coverage at minimal cost.
