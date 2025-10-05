# Claude Development Guide

## Quick Start

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

#### All Tests
```bash
# Run all tests with verbose output
python -m pytest tests/ -v --tb=short

# Run all tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Quick test run (minimal output)
python -m pytest tests/ -q
```

#### Specific Test Categories
```bash
# Run E2E tests (end-to-end pipeline validation)
python -m pytest tests/test_e2e_simple.py -v

# Run core functionality tests
python -m pytest tests/test_translate.py tests/test_tex_guard.py tests/test_format_translation.py tests/test_job_queue.py tests/test_harvest_ia.py tests/test_e2e_simple.py -v

# Run specific test file
python -m pytest tests/test_translate.py -v

# Run specific test method
python -m pytest tests/test_translate.py::TestTranslation::test_translate_field_success -v
```

#### Test with Coverage
```bash
# Run tests with coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Development Workflow

#### Before Making Changes
```bash
# Run E2E tests to ensure baseline functionality
python -m pytest tests/test_e2e_simple.py -v
```

#### During Development
```bash
# Run specific tests related to your changes
python -m pytest tests/test_translate.py -v

# Run all tests to check for regressions
python -m pytest tests/ -v --tb=short
```

#### Before Committing
```bash
# Run full test suite
python -m pytest tests/ -v --tb=short

# Run with coverage to ensure no regression
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Pipeline Testing

#### Smoke Test (Local)
```bash
# Harvest a few papers
python -m src.harvest_ia --limit 10

# Translate in dry-run mode
python -m src.translate --dry-run

# Render and build search index
python -m src.render && python -m src.search_index

# Preview site locally
python -m http.server -d site 8000
```

#### Full Pipeline Test
```bash
# Harvest all papers
python -m src.harvest_ia --all

# Translate all papers (requires API key)
python -m src.translate

# Render site and build search index
python -m src.render && python -m src.search_index
```

### Debugging Tests

#### Verbose Output
```bash
# Show detailed test output
python -m pytest tests/test_translate.py -v -s

# Show print statements
python -m pytest tests/test_translate.py -s
```

#### Stop on First Failure
```bash
# Stop after first failure
python -m pytest tests/ -x

# Stop after first failure with verbose output
python -m pytest tests/ -x -v
```

#### Run Only Failed Tests
```bash
# Run only tests that failed in last run
python -m pytest tests/ --lf
```

### Test Structure

#### Test Files
- `tests/test_e2e_simple.py` - End-to-end pipeline tests
- `tests/test_translate.py` - Translation functionality tests
- `tests/test_tex_guard.py` - Math masking/unmasking tests
- `tests/test_format_translation.py` - Translation formatting tests
- `tests/test_job_queue.py` - Job queue system tests
- `tests/test_harvest_ia.py` - Internet Archive harvesting tests
- `tests/test_licenses.py` - License handling tests
- `tests/test_search_index.py` - Search index building tests

#### Test Categories
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete pipeline workflows
- **Mock Tests**: Test with mocked external dependencies

### Continuous Integration

#### GitHub Actions
Tests run automatically on:
- Push to main branch
- Pull request creation/updates
- Scheduled nightly builds

#### Local CI Simulation
```bash
# Run tests as they would run in CI
python -m pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml
```

### Troubleshooting

#### Common Issues
1. **Import Errors**: Ensure virtual environment is activated
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **API Key Issues**: Set `OPENROUTER_API_KEY` environment variable
4. **Port Conflicts**: Use different port for local server (`python -m http.server -d site 8001`)

#### Test Failures
1. **Check test output**: Use `-v` flag for verbose output
2. **Check coverage**: Ensure new code is covered by tests
3. **Run E2E tests**: Validate complete pipeline functionality
4. **Check logs**: Look for error messages in test output

### Best Practices

#### Writing Tests
- Write tests before implementing features (TDD)
- Use descriptive test names
- Mock external dependencies
- Test edge cases and error conditions
- Keep tests independent and isolated

#### Running Tests
- Run tests frequently during development
- Use E2E tests as a safety net for refactoring
- Check coverage regularly
- Fix failing tests immediately
- Use appropriate test flags for different scenarios
