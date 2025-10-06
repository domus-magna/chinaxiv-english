# Testing Strategy for ChinaXiv English Translation

## Overview

This document outlines the testing strategy for the ChinaXiv English translation project, including unit tests, integration tests, and testing best practices.

## Current Test Coverage

### ✅ Implemented Tests (79 tests, 31% coverage)

#### Core Functionality Tests
- **Math/LaTeX Masking** (`test_tex_guard.py`) - 13 tests
  - Inline math expressions (`$x = y$`)
  - Display math expressions (`$$x = y$$`)
  - LaTeX environments (`\begin{equation}`)
  - Token parity verification
  - Complex nested expressions

- **Translation Logic** (`test_translate.py`) - 12 tests
  - Field translation with/without dry run
  - Math preservation during translation
  - License-based translation gating
  - Cost tracking
  - Error handling

- **Job Queue System** (`test_job_queue.py`) - 13 tests
  - SQLite database operations
  - Atomic job claiming
  - Retry logic (max 3 attempts)
  - Worker heartbeat tracking
  - QA result storage

- **Internet Archive Harvesting** (`test_harvest_ia.py`) - 11 tests
  - Record normalization
  - API pagination
  - Year filtering
  - Error handling

- **Translation Formatting** (`test_format_translation.py`) - 14 tests
  - Section heading detection
  - Short fragment merging
  - Mathematical formula detection
  - Markdown formatting
  - Edge cases

#### Integration Tests
- **Body Extraction** (`test_body_extract.py`) - 2 tests
- **Cost Logging** (`test_cost_logging.py`) - 1 test
- **License Processing** (`test_licenses.py`) - 2 tests
- **PDF Generation** (`test_make_pdf.py`) - 1 test
- **Site Rendering** (`test_render_smoke.py`) - 1 test
- **Search Index** (`test_search_index.py`) - 1 test
- **File Operations** (`test_select_and_fetch.py`) - 2 tests

## Testing Framework Setup

### Dependencies
```bash
pip install pytest pytest-cov pytest-mock
```

### Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    network: Tests requiring network access
    mock: Tests using mocks
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_tex_guard.py -v

# Run tests matching pattern
python -m pytest tests/ -k "math" -v
```

## Testing Strategy: Test-First Refactoring

### Why Test-First?

1. **Safety Net**: Tests provide confidence during refactoring
2. **Documentation**: Tests serve as living documentation of expected behavior
3. **Regression Prevention**: Catch bugs introduced during changes
4. **Interface Design**: Writing tests first leads to better API design

### Implementation Plan

#### Phase 1: Critical Path Tests ✅ COMPLETED
- [x] Math/LaTeX masking and unmasking
- [x] Translation core logic
- [x] Job queue operations
- [x] Internet Archive harvesting
- [x] Translation formatting

#### Phase 2: Refactoring with Test Safety Net
- [ ] Split `utils.py` into focused modules
- [ ] Extract translation service layer
- [ ] Standardize error handling
- [ ] Add dependency injection

#### Phase 3: Expanded Test Coverage
- [ ] Integration tests for full pipeline
- [ ] Performance tests for large datasets
- [ ] End-to-end tests with real data
- [ ] Load tests for batch processing

## Test Categories

### Unit Tests
- **Purpose**: Test individual functions in isolation
- **Scope**: Single module/function
- **Mocking**: External dependencies (APIs, file system)
- **Examples**: Math masking, translation logic, data normalization

### Integration Tests
- **Purpose**: Test component interactions
- **Scope**: Multiple modules working together
- **Mocking**: Minimal, focus on real interactions
- **Examples**: Harvest → Translate → Render pipeline

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Scope**: Full system from input to output
- **Mocking**: None, use real data
- **Examples**: Complete paper translation workflow

## Test Data Management

### Test Fixtures
```python
@pytest.fixture
def sample_paper():
    return {
        "id": "test-1",
        "title": "Test Paper",
        "abstract": "Test abstract",
        "creators": ["Author 1"],
        "subjects": ["cs.AI"],
        "date": "2024-01-01"
    }
```

### Mock Data
- Use realistic but minimal test data
- Avoid hardcoded values that might change
- Create reusable fixtures for common scenarios

### Test Isolation
- Each test should be independent
- Use temporary files/databases
- Clean up after each test

## Mocking Strategy

### External Dependencies
```python
@patch('src.translate.openrouter_translate')
def test_translation(mock_translate):
    mock_translate.return_value = "Translated text"
    # Test translation logic
```

### File System Operations
```python
@patch('builtins.open', mock_open(read_data="test content"))
def test_file_reading():
    # Test file operations
```

### Network Requests
```python
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    # Test API interactions
```

## Coverage Goals

### Current Status
- **Overall Coverage**: 31%
- **Core Modules**: 60-100% coverage
- **Critical Functions**: 100% coverage

### Target Coverage
- **Overall**: 80%+
- **Core Logic**: 95%+
- **Utility Functions**: 90%+
- **CLI Interfaces**: 70%+

## Testing Best Practices

### Test Naming
```python
def test_function_name_scenario_expected_result():
    """Test that function_name does scenario and returns expected_result."""
    # Test implementation
```

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange
    input_data = "test input"
    expected = "expected output"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

### Assertions
- Use specific assertions (`assert result == expected`)
- Avoid generic assertions (`assert result`)
- Include helpful error messages
- Test edge cases and error conditions

### Test Organization
- Group related tests in classes
- Use descriptive test names
- Keep tests focused and simple
- Avoid test interdependencies

## Continuous Integration

### GitHub Actions Integration
```yaml
- name: Run Tests
  run: |
    python -m pytest tests/ --cov=src --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python -m pytest tests/ -v
        language: system
        pass_filenames: false
```

## Future Enhancements

### Performance Testing
- Load testing for batch translation
- Memory usage monitoring
- API rate limiting tests

### Security Testing
- Input validation tests
- SQL injection prevention
- API key handling

### Accessibility Testing
- HTML output validation
- Screen reader compatibility
- Keyboard navigation

## Conclusion

The current test suite provides a solid foundation for safe refactoring. With 79 tests covering critical functionality, we can confidently proceed with architectural improvements while maintaining system reliability.

The test-first approach ensures that:
1. Refactoring is safe and reversible
2. Code quality improves through better interfaces
3. Documentation stays current
4. Regression bugs are caught early

Next steps: Proceed with Phase 2 refactoring using the existing tests as a safety net.
